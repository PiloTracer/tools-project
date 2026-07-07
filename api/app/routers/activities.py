from __future__ import annotations

import asyncio
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db, session_factory
from app.deps import get_current_user
from app.models.activity import Activity
from app.models.attachment import Attachment
from app.models.commit_subject_ref import CommitSubjectRef
from app.models.github_commit import GithubCommit
from app.models.github_link import GithubLink
from app.models.mention import Mention
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas import ACTIVITY_KINDS, ActivityCreate, ActivityListResponse, ActivityOut
from app.services.mention_parse import mention_emails_from_text
from app.services.project_access import (
    can_comment_on_project,
    is_client_participant,
    require_project_access,
)

router = APIRouter(
    prefix="/v1/projects/{project_id}/activities",
    tags=["activities"],
)


async def _validate_github_ref(
    db: AsyncSession,
    project_id: uuid.UUID,
    ref: dict | None,
) -> uuid.UUID | None:
    """Validate github_ref and return the commit UUID, or None."""
    if not ref:
        return None
    commit_id = ref.get("commit_id")
    sha = ref.get("sha")
    if not commit_id or not sha:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="github_ref requires commit_id and sha",
        )
    try:
        commit_uuid = uuid.UUID(str(commit_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Invalid commit_id in github_ref",
        ) from None
    commit = await db.get(GithubCommit, commit_uuid)
    if commit is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Referenced commit not found",
        )
    link = await db.get(GithubLink, commit.github_link_id)
    if link is None or link.project_id != project_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Referenced commit does not belong to this project",
        )
    return commit_uuid

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
    for aid in ids:
        att = await db.get(Attachment, aid)
        if att is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Attachment not found")
        if att.project_id != project_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Attachment does not belong to this project",
            )
        if subject_type == "ticket" and att.ticket_id != subject_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Attachment does not belong to this ticket",
            )
        if subject_type == "task" and att.task_id != subject_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Attachment does not belong to this task",
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


async def _enrich_subject_titles(
    db: AsyncSession,
    rows: list[Activity],
) -> dict[uuid.UUID, tuple[str | None, str | None]]:
    """Batch-resolve task/ticket ref + title for activities with non-project subject_type."""
    task_ids = [r.subject_id for r in rows if r.subject_type == "task"]
    ticket_ids = [r.subject_id for r in rows if r.subject_type == "ticket"]
    lookup: dict[uuid.UUID, tuple[str | None, str | None]] = {}
    if task_ids:
        result = await db.scalars(select(Task).where(Task.id.in_(task_ids)))
        for t in result.all():
            lookup[t.id] = (t.ref, t.title)
    if ticket_ids:
        result = await db.scalars(select(Ticket).where(Ticket.id.in_(ticket_ids)))
        for t in result.all():
            lookup[t.id] = (t.ref, t.title)
    return lookup


@router.get("", response_model=ActivityListResponse)
async def list_activities(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    subject_type: str | None = None,
    subject_id: uuid.UUID | None = None,
    kind: str | None = None,
    visibility: str | None = Query(
        default=None,
        description="Filter by note visibility: 'internal' (staff-only) or 'external' (customer-visible).",
        pattern=r"^(internal|external)$",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    acc = await require_project_access(db, user, project_id)
    client_participant = is_client_participant(acc)
    if client_participant and visibility == "internal":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Client participants cannot view internal activities",
        )

    base = select(Activity).where(Activity.project_id == project_id)
    if subject_type:
        base = base.where(Activity.subject_type == subject_type.strip().lower())
    if subject_id is not None:
        base = base.where(Activity.subject_id == subject_id)
    if kind is not None:
        base = base.where(Activity.kind == kind.strip().lower())
    if client_participant:
        base = base.where(Activity.is_internal.is_(False))
    elif visibility == "internal":
        base = base.where(Activity.is_internal.is_(True))
    elif visibility == "external":
        base = base.where(Activity.is_internal.is_(False))

    total = (await db.scalar(base.with_only_columns(func.count()).order_by(None))) or 0

    stmt = base.order_by(Activity.created_at.desc()).offset(offset).limit(limit)
    rows = list((await db.scalars(stmt)).all())
    lookup = await _enrich_subject_titles(db, rows)
    items = []
    for r in rows:
        ref, title = lookup.get(r.subject_id, (None, None))
        items.append(
            ActivityOut.model_validate(r).model_copy(
                update={
                    "actor_email": r.actor.email if r.actor else None,
                    "subject_ref": ref,
                    "subject_title": title,
                }
            )
        )
    return ActivityListResponse(
        items=items,
        total=total,
        has_more=(offset + len(items)) < total,
    )


@router.post("", response_model=ActivityOut, status_code=status.HTTP_201_CREATED)
async def create_activity(
    project_id: uuid.UUID,
    body: ActivityCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not can_comment_on_project(acc):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to post activity in this project",
        )
    st = body.subject_type.strip().lower()
    await _validate_subject(db, project_id, st, body.subject_id)
    github_ref = (body.meta_json or {}).get("github_ref")
    commit_ref_id = await _validate_github_ref(db, project_id, github_ref)
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
        if parent.parent_activity_id is not None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Nested replies beyond one level are not supported",
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
    is_internal = bool(body.is_internal)
    if is_internal and is_client_participant(acc):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Client participants cannot post internal activities",
        )
    if is_internal and st not in ("task", "ticket"):
        # Project-wide notes are visible to all members by design; internal toggle
        # only makes sense on a specific work item (task / ticket case thread).
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="is_internal is only valid on task or ticket activity entries",
        )
    row = Activity(
        project_id=project_id,
        subject_type=st,
        subject_id=body.subject_id,
        kind=kind_val,
        actor_id=user.id,
        parent_activity_id=body.parent_activity_id,
        body=body_text,
        meta_json=body.meta_json,
        is_internal=is_internal,
    )
    db.add(row)
    await db.flush()

    # Create commit_subject_ref row if github_ref was present
    if commit_ref_id is not None and st in ("task", "ticket"):
        existing_ref = await db.scalar(
            select(CommitSubjectRef).where(
                CommitSubjectRef.github_commit_id == commit_ref_id,
                CommitSubjectRef.subject_type == st,
                CommitSubjectRef.subject_id == body.subject_id,
            )
        )
        if existing_ref is None:
            ref_commit = await db.get(GithubCommit, commit_ref_id)
            if ref_commit is None:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail="Referenced commit not found",
                )
            db.add(
                CommitSubjectRef(
                    github_commit_id=commit_ref_id,
                    sha=ref_commit.sha,
                    project_id=project_id,
                    subject_type=st,
                    subject_id=body.subject_id,
                    created_by=user.id,
                )
            )
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
    """SSE: emits latest activity when it changes (~4s poll). Includes kind/subject for richer feed."""
    fac = session_factory()

    async def gen():
        await asyncio.sleep(0)
        last: str | None = None
        for _ in range(45):
            async with fac() as session:
                await require_project_access(session, user, project_id)
                row = await session.scalar(
                    select(Activity)
                    .where(Activity.project_id == project_id)
                    .order_by(Activity.created_at.desc())
                    .limit(1)
                )
            if row is not None:
                cur = str(row.id)
                if cur != last:
                    last = cur
                    payload = json.dumps({
                        "latest_activity_id": cur,
                        "kind": row.kind,
                        "subject_type": row.subject_type,
                        "subject_id": str(row.subject_id),
                    })
                    yield f"data: {payload}\n\n"
            await asyncio.sleep(4)

    return StreamingResponse(gen(), media_type="text/event-stream")
