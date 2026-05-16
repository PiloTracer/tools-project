from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas import (
    TICKET_STATUSES,
    TicketCreate,
    TicketListResponse,
    TicketOut,
    TicketPatch,
    TicketTransition,
)
from app.services.project_access import MemberRole, can_mutate_tasks, require_project_access, require_role
from app.services.ref_alloc import allocate_ref

router = APIRouter(
    prefix="/v1/projects/{project_id}/tickets",
    tags=["tickets"],
)
detail_router = APIRouter(prefix="/v1/tickets", tags=["tickets"])

_TERMINAL_TICKET_STATUSES: frozenset[str] = frozenset({"resolved", "closed"})


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    queue_slug: str | None = None,
    ticket_status: str | None = None,
):
    await require_project_access(db, user, project_id)
    stmt = select(Ticket).where(Ticket.project_id == project_id)
    if queue_slug:
        stmt = stmt.where(Ticket.queue_slug == queue_slug.strip())
    if ticket_status:
        stmt = stmt.where(Ticket.status == ticket_status.strip())
    # Support queue: open work first, oldest first (age / triage); terminal tickets sink.
    stmt = stmt.order_by(
        case(
            (Ticket.status.in_(("resolved", "closed")), 1),
            else_=0,
        ),
        Ticket.created_at.asc(),
    )
    rows = list((await db.scalars(stmt)).all())
    return TicketListResponse(items=[TicketOut.model_validate(r) for r in rows])


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    project_id: uuid.UUID,
    body: TicketCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not can_mutate_tasks(acc.role):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Viewers cannot create tickets",
        )
    status_val = body.status.strip()
    if status_val not in TICKET_STATUSES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_val}. Use one of {sorted(TICKET_STATUSES)}",
        )
    ref = await allocate_ref(db, project_id, "ticket")
    closed_at = datetime.now(timezone.utc) if status_val in _TERMINAL_TICKET_STATUSES else None
    row = Ticket(
        project_id=project_id,
        ref=ref,
        title=body.title.strip(),
        description=body.description.strip() if body.description else None,
        status=status_val,
        priority=body.priority.strip(),
        queue_slug=body.queue_slug.strip() or "default",
        requester_email=body.requester_email.strip().lower() if body.requester_email else None,
        reporter_id=user.id,
        assignee_id=body.assignee_id,
        closed_at=closed_at,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return TicketOut.model_validate(row)


@detail_router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Ticket, ticket_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    await require_project_access(db, user, row.project_id)
    return TicketOut.model_validate(row)


@detail_router.patch("/{ticket_id}", response_model=TicketOut)
async def patch_ticket(
    ticket_id: uuid.UUID,
    body: TicketPatch,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Ticket, ticket_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    acc = await require_project_access(db, user, row.project_id)
    if not can_mutate_tasks(acc.role):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Viewers cannot edit tickets",
        )
    if body.title is not None:
        row.title = body.title.strip()
    if body.description is not None:
        v = body.description.strip()
        row.description = v if v else None
    if body.status is not None:
        status_val = body.status.strip()
        if status_val not in TICKET_STATUSES:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_val}. Use one of {sorted(TICKET_STATUSES)}",
            )
        row.status = status_val
        if status_val in _TERMINAL_TICKET_STATUSES:
            now = datetime.now(timezone.utc)
            if row.resolved_at is None:
                row.resolved_at = now
            if row.closed_at is None:
                row.closed_at = now
        else:
            if status_val == "in_progress" and row.first_response_at is None:
                row.first_response_at = datetime.now(timezone.utc)
    if body.priority is not None:
        row.priority = body.priority.strip()
    if body.queue_slug is not None:
        row.queue_slug = body.queue_slug.strip() or "default"
    if body.requester_email is not None:
        row.requester_email = body.requester_email.strip().lower() if body.requester_email else None
    if body.assignee_id is not None:
        row.assignee_id = body.assignee_id
    await db.commit()
    await db.refresh(row)
    return TicketOut.model_validate(row)


@detail_router.post("/{ticket_id}/transition", response_model=TicketOut)
async def transition_ticket(
    ticket_id: uuid.UUID,
    body: TicketTransition,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Ticket, ticket_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    acc = await require_project_access(db, user, row.project_id)
    if not can_mutate_tasks(acc.role):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Viewers cannot change ticket status",
        )
    status_val = body.status.strip()
    if status_val not in TICKET_STATUSES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_val}. Use one of {sorted(TICKET_STATUSES)}",
        )
    now = datetime.now(timezone.utc)
    if status_val == "in_progress" and row.first_response_at is None:
        row.first_response_at = now
    if status_val == "resolved" and row.resolved_at is None:
        row.resolved_at = now
    if status_val == "closed" and row.closed_at is None:
        row.closed_at = now
    row.status = status_val
    await db.commit()
    await db.refresh(row)
    return TicketOut.model_validate(row)


@detail_router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Ticket, ticket_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    acc = await require_project_access(db, user, row.project_id)
    require_role(acc, MemberRole.maintainer)
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
