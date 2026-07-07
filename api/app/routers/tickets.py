from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas import (
    TICKET_STATUSES,
    TicketBatchUpdate,
    TicketCreate,
    TicketListResponse,
    TicketOut,
    TicketPatch,
    TicketTransition,
)
from app.services.activity_writer import write_activity
from app.services.github_task_registry import (
    spawn_push_ticket_ref,
)
from app.services.github_task_registry import (
    spawn_remove_ref as spawn_remove_ticket_ref,
)
from app.services.project_access import (
    MemberRole,
    can_mutate_tasks,
    can_view_tickets,
    client_company_user_ids,
    is_client_participant,
    require_project_access,
    require_role,
)
from app.services.ref_alloc import allocate_ref
from app.services.webhook_dispatcher import dispatch_event

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
    q: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    acc = await require_project_access(db, user, project_id)
    if not can_view_tickets(acc):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view tickets in this project",
        )

    base = select(Ticket).where(Ticket.project_id == project_id)
    if q:
        like = f"%{q.strip()}%"
        base = base.where(or_(Ticket.title.ilike(like), Ticket.ref.ilike(like)))
    if queue_slug:
        base = base.where(Ticket.queue_slug == queue_slug.strip())
    if ticket_status:
        base = base.where(Ticket.status == ticket_status.strip())
    if is_client_participant(acc):
        peer_ids = await client_company_user_ids(db, acc)
        base = base.where(Ticket.assignee_id.in_(peer_ids))

    total = (await db.scalar(base.with_only_columns(func.count()).order_by(None))) or 0

    stmt = base.order_by(
        case(
            (Ticket.status.in_(("resolved", "closed")), 1),
            else_=0,
        ),
        Ticket.created_at.asc(),
    ).offset(offset).limit(limit)
    rows = list((await db.scalars(stmt)).all())
    return TicketListResponse(
        items=[TicketOut.model_validate(r) for r in rows],
        total=total,
        has_more=(offset + len(rows)) < total,
    )


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
    closed_at = datetime.now(UTC) if status_val in _TERMINAL_TICKET_STATUSES else None
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
    await db.flush()
    await write_activity(
        db=db,
        project_id=project_id,
        subject_type="ticket",
        subject_id=row.id,
        kind="system",
        actor_id=user.id,
        body=f"Ticket created: {row.title}",
    )
    await db.commit()
    await db.refresh(row)
    dispatch_event("ticket.created", {
        "ticket_id": str(row.id),
        "project_id": str(project_id),
        "title": row.title,
        "ref": row.ref,
        "status": row.status,
    })
    if row.ref:
        spawn_push_ticket_ref(project_id, row.ref, row.title, row.status, row.description)
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
    acc = await require_project_access(db, user, row.project_id)
    if not can_view_tickets(acc):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this ticket",
        )
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
        _prev_ticket_status = row.status
        row.status = status_val
        if status_val in _TERMINAL_TICKET_STATUSES:
            now = datetime.now(UTC)
            if row.resolved_at is None:
                row.resolved_at = now
            if row.closed_at is None:
                row.closed_at = now
        else:
            if status_val == "in_progress" and row.first_response_at is None:
                row.first_response_at = datetime.now(UTC)
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
    if body.status is not None and _prev_ticket_status != "closed" and row.status == "closed":
        dispatch_event("ticket.closed", {
            "ticket_id": str(ticket_id),
            "project_id": str(row.project_id),
            "title": row.title,
            "ref": row.ref,
        })
    if row.ref:
        spawn_push_ticket_ref(row.project_id, row.ref, row.title, row.status, row.description)
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
    now = datetime.now(UTC)
    if status_val == "in_progress" and row.first_response_at is None:
        row.first_response_at = now
    if status_val == "resolved" and row.resolved_at is None:
        row.resolved_at = now
    if status_val == "closed" and row.closed_at is None:
        row.closed_at = now
    row.status = status_val
    await db.commit()
    await db.refresh(row)
    if status_val == "closed":
        dispatch_event("ticket.closed", {
            "ticket_id": str(ticket_id),
            "project_id": str(row.project_id),
            "title": row.title,
            "ref": row.ref,
        })
    if row.ref:
        spawn_push_ticket_ref(row.project_id, row.ref, row.title, row.status, row.description)
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
    ref = row.ref
    await db.delete(row)
    await db.commit()
    if ref:
        spawn_remove_ticket_ref(row.project_id, ref)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@detail_router.post("/batch", response_model=list[TicketOut])
async def batch_update_tickets(
    body: TicketBatchUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Batch update multiple tickets — status, priority, assignee, or queue_slug."""
    rows = list((await db.scalars(
        select(Ticket).where(Ticket.id.in_(body.ids))
    )).all())

    if not rows:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No tickets found")

    # Verify access to all tickets
    project_ids = {r.project_id for r in rows}
    for pid in project_ids:
        acc = await require_project_access(db, user, pid)
        if not can_mutate_tasks(acc.role):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to edit tickets in project {pid}",
            )

    updated: list[Ticket] = []
    for row in rows:
        changed = False
        if body.status is not None:
            status_val = body.status.strip()
            if status_val not in TICKET_STATUSES:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_val}. Use one of {sorted(TICKET_STATUSES)}",
                )
            row.status = status_val
            now = datetime.now(UTC)
            if status_val in {"resolved", "closed"}:
                if row.resolved_at is None:
                    row.resolved_at = now
                if row.closed_at is None:
                    row.closed_at = now
            elif status_val == "in_progress" and row.first_response_at is None:
                row.first_response_at = now
            changed = True
        if body.priority is not None:
            row.priority = body.priority.strip()
            changed = True
        if body.assignee_id is not None:
            row.assignee_id = body.assignee_id
            changed = True
        if body.queue_slug is not None:
            row.queue_slug = body.queue_slug.strip() or "default"
            changed = True
        if changed:
            updated.append(row)

    await db.commit()
    for row in updated:
        await db.refresh(row)
        if row.ref:
            spawn_push_ticket_ref(row.project_id, row.ref, row.title, row.status, row.description)
    return [TicketOut.model_validate(r) for r in updated]
