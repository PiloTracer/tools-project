from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.inbox_item import InboxItem
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas import InboxCreate, InboxListResponse, InboxOut, InboxTriage
from app.services.project_access import can_mutate_tasks, require_project_access
from app.services.ref_alloc import allocate_ref

router = APIRouter(prefix="/v1/inbox", tags=["inbox"])


@router.get("", response_model=InboxListResponse)
async def list_inbox(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = list(
        (
            await db.scalars(
                select(InboxItem)
                .where(InboxItem.owner_id == user.id, InboxItem.triaged_to_id.is_(None))
                .order_by(InboxItem.created_at.desc())
                .limit(200)
            )
        ).all()
    )
    return InboxListResponse(items=[InboxOut.model_validate(r) for r in rows])


@router.post("", response_model=InboxOut, status_code=status.HTTP_201_CREATED)
async def create_inbox_item(
    body: InboxCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = InboxItem(
        owner_id=user.id,
        body_md=body.body_md.strip(),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return InboxOut.model_validate(row)


@router.post("/{item_id}/triage", response_model=InboxOut)
async def triage_inbox_item(
    item_id: uuid.UUID,
    body: InboxTriage,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    item = await db.get(InboxItem, item_id)
    if item is None or item.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    if item.triaged_to_id is not None:
        raise HTTPException(status_code=400, detail="Item already triaged")

    acc = await require_project_access(db, user, body.project_id)
    if not can_mutate_tasks(acc.role):
        raise HTTPException(
            status_code=403, detail="Viewers cannot triage items"
        )

    if body.into == "task":
        ref = await allocate_ref(db, body.project_id, "task")
        task = Task(
            project_id=body.project_id,
            component_id=body.component_id,
            ref=ref,
            title=item.body_md[:500],
            description=item.body_md,
            status="todo",
            priority=body.priority.strip(),
            assignee_id=body.assignee_id,
            reporter_id=user.id,
            is_todo=False,
        )
        db.add(task)
        await db.flush()
        item.triaged_to_type = "task"
        item.triaged_to_id = task.id
    elif body.into == "ticket":
        ref = await allocate_ref(db, body.project_id, "ticket")
        ticket = Ticket(
            project_id=body.project_id,
            ref=ref,
            title=item.body_md[:500],
            description=item.body_md,
            status="open",
            priority=body.priority.strip(),
            reporter_id=user.id,
            assignee_id=body.assignee_id,
        )
        db.add(ticket)
        await db.flush()
        item.triaged_to_type = "ticket"
        item.triaged_to_id = ticket.id

    item.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(item)
    return InboxOut.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inbox_item(
    item_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    item = await db.get(InboxItem, item_id)
    if item is None or item.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    await db.delete(item)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
