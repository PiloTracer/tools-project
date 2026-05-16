from __future__ import annotations

import asyncio
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db, session_factory
from app.deps import get_current_user
from app.models.activity import Activity
from app.models.attachment import Attachment
from app.models.mention import Mention
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas import ACTIVITY_KINDS, ActivityCreate, ActivityListResponse, ActivityOut
from app.services.mention_parse import mention_emails_from_text
from app.services.project_access import can_mutate_tasks, require_project_access

router = APIRouter(
    prefix="/v1/projects/{project_id}/activities",
    tags=["activities"],
)


async def _validate_subject(
    db: AsyncSession,
    project_id: uuid.UUID,
    subject_type: str,
    subject_id: uuid.UUID,
) -> None:
    st = subject_type.strip().lower()
    if st == "project":
        if subject_id != project_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="For subject_type=project, subject_id must be the project id",
            )
        return
    if st == "task":
        row = await db.get(Task, subject_id)
        if row is None or row.project_id != project_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Task not found in this project",
            )
        return
    if st == "ticket":
        row = await db.get(Ticket, subject_id)
        if row is None or row.project_id != project_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Ticket not found in this project",
            )
        return
    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid subject_type")


def _attachment_ids_from_meta(meta: dict | None) -> list[uuid.UUID]:
    if not meta:
        return []
    raw = meta.get("attachment_ids")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="meta_json.attachment_ids must be a list of UUID strings",
        )
    out: list[uuid.UUID] = []
    for x in raw:
        try:
            out.append(uuid.UUID(str(x)))
        except (ValueError, TypeError) as exc:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="meta_json.attachment_ids must be a list of UUID strings",
            ) from exc
    return out


async def _validate_and_link_ticket_attachments(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    subject_type: str,
    subject_id: uuid.UUID,
    activity_id: uuid.UUID,
    meta: dict | None,
) -> None:
    ids = _attachment_ids_from_meta(meta)
    if not ids:
        return
    if subject_type != "ticket":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Image attachments on comments are only supported for tickets in this release",
        )
    for aid in ids:
        att = await db.get(Attachment, aid)
        if att is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Attachment not found")
        if att.project_id != project_id or att.ticket_id != subject_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Attachment does not belong to this ticket",
            )
        if att.activity_id is not None and att.activity_id != activity_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Attachment already linked to another comment",
            )
    for aid in ids:
        att = await db.get(Attachment, aid)
        if att is not None:
            att.activity_id = activity_id


async def _insert_mentions_for_activity(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    activity_id: uuid.UUID,
    actor_id: uuid.UUID,
    body: str,
) -> None:
    for email in mention_emails_from_text(body):
        user = await db.scalar(select(User).where(User.email == email))
        if user is None or user.id == actor_id:
            continue
        stmt = (
            pg_insert(Mention)
            .values(
                id=uuid.uuid4(),
                project_id=project_id,
                activity_id=activity_id,
                mentioned_user_id=user.id,
            )
            .on_conflict_do_nothing(index_elements=["activity_id", "mentioned_user_id"])
        )
        await db.execute(stmt)


@router.get("", response_model=ActivityListResponse)
async def list_activities(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    subject_type: str | None = None,
    subject_id: uuid.UUID | None = None,
    kind: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    await require_project_access(db, user, project_id)
    stmt = (
        select(Activity)
        .where(Activity.project_id == project_id)
        .order_by(Activity.created_at.desc())
        .limit(limit)
    )
    if subject_type:
        stmt = stmt.where(Activity.subject_type == subject_type.strip().lower())
    if subject_id is not None:
        stmt = stmt.where(Activity.subject_id == subject_id)
    if kind is not None:
        stmt = stmt.where(Activity.kind == kind.strip().lower())
    rows = list((await db.scalars(stmt)).all())
    items = [
        ActivityOut.model_validate(r).model_copy(
            update={"actor_email": r.actor.email if r.actor else None}
        )
        for r in rows
    ]
    return ActivityListResponse(items=items)


@router.post("", response_model=ActivityOut, status_code=status.HTTP_201_CREATED)
async def create_activity(
    project_id: uuid.UUID,
    body: ActivityCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not can_mutate_tasks(acc.role):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Viewers cannot post activity",
        )
    st = body.subject_type.strip().lower()
    await _validate_subject(db, project_id, st, body.subject_id)
    kind_val = body.kind.strip().lower()
    if kind_val not in ACTIVITY_KINDS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid kind: {kind_val}. Use one of {sorted(ACTIVITY_KINDS)}",
        )
    if body.parent_activity_id is not None:
        parent = await db.get(Activity, body.parent_activity_id)
        if parent is None or parent.project_id != project_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="parent_activity_id must belong to this project",
            )
    ids = _attachment_ids_from_meta(body.meta_json)
    body_text = body.body.strip()
    if not body_text and not ids:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Provide a comment body and/or images (attachment_ids)",
        )
    if not body_text and ids:
        body_text = "(image)"
    row = Activity(
        project_id=project_id,
        subject_type=st,
        subject_id=body.subject_id,
        kind=kind_val,
        actor_id=user.id,
        parent_activity_id=body.parent_activity_id,
        body=body_text,
        meta_json=body.meta_json,
    )
    db.add(row)
    await db.flush()
    await _validate_and_link_ticket_attachments(
        db,
        project_id=project_id,
        subject_type=st,
        subject_id=body.subject_id,
        activity_id=row.id,
        meta=body.meta_json,
    )
    await _insert_mentions_for_activity(
        db,
        project_id=project_id,
        activity_id=row.id,
        actor_id=user.id,
        body=row.body,
    )
    await db.commit()
    await db.refresh(row)
    return ActivityOut.model_validate(row).model_copy(
        update={"actor_email": user.email},
    )


@router.get("/stream")
async def activity_stream(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
):
    """Light SSE: emits latest activity id when it changes (~4s poll). Client may reconnect."""
    fac = session_factory()

    async def gen():
        await asyncio.sleep(0)
        last: str | None = None
        for _ in range(45):  # ~3 min
            async with fac() as session:
                await require_project_access(session, user, project_id)
                row = await session.scalar(
                    select(Activity.id)
                    .where(Activity.project_id == project_id)
                    .order_by(Activity.created_at.desc())
                    .limit(1)
                )
            cur = str(row) if row else None
            if cur != last:
                last = cur
                payload = json.dumps({"latest_activity_id": cur})
                yield f"data: {payload}\n\n"
            await asyncio.sleep(4)

    return StreamingResponse(gen(), media_type="text/event-stream")
