"""Client portal endpoints for external client participants."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.deps import get_current_user
from app.models.activity import Activity
from app.models.component import Component
from app.models.task import Task
from app.models.ticket import Ticket
from app.routers.activities import _enrich_subject_titles
from app.models.client_contact import ClientContact
from app.models.project import Project
from app.models.project_client import ProjectClient
from app.models.project_client_access import ProjectClientAccess
from app.models.user import User
from app.schemas import (
    ActivityListResponse,
    ActivityOut,
    ClientSummary,
    ProjectListResponse,
    ProjectOut,
    TASK_STATUSES,
    TaskCreate,
    TaskListResponse,
    TaskOut,
    TicketListResponse,
    TicketOut,
)
from app.services.activity_writer import write_activity
from app.services.ref_alloc import allocate_ref

router = APIRouter(prefix="/v1/me/client", tags=["client-portal"])


async def _require_client_contact(
    db: AsyncSession, user: User
) -> ClientContact:
    contact = await db.scalar(
        select(ClientContact).where(ClientContact.user_id == user.id)
    )
    if contact is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="User is not linked to a client contact",
        )
    return contact


async def _require_client_project_access(
    db: AsyncSession,
    contact: ClientContact,
    project_id: uuid.UUID,
) -> tuple[Project, ProjectClientAccess]:
    acc = await db.scalar(
        select(ProjectClientAccess)
        .options(selectinload(ProjectClientAccess.project))
        .where(
            ProjectClientAccess.project_id == project_id,
            ProjectClientAccess.client_contact_id == contact.id,
        )
    )
    if acc is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return acc.project, acc


@router.get("/projects", response_model=ProjectListResponse)
async def list_client_projects(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List projects the current client contact has access to."""
    contact = await _require_client_contact(db, user)
    rows = list(
        (
            await db.scalars(
                select(ProjectClientAccess)
                .options(selectinload(ProjectClientAccess.project))
                .where(ProjectClientAccess.client_contact_id == contact.id)
                .order_by(ProjectClientAccess.created_at.desc())
            )
        ).all()
    )
    items = [
        ProjectOut.model_validate(a.project).model_copy(
            update={"membership_role": a.role}
        )
        for a in rows
    ]
    return ProjectListResponse(items=items)


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_client_project(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a single project accessible to the current client contact."""
    contact = await _require_client_contact(db, user)
    project, acc = await _require_client_project_access(db, contact, project_id)
    client_rows = await db.scalars(
        select(ProjectClient)
        .options(selectinload(ProjectClient.client))
        .where(ProjectClient.project_id == project_id)
    )
    clients_summary = [
        ClientSummary(id=pc.client.id, name=pc.client.name, slug=pc.client.slug)
        for pc in client_rows.all()
    ]
    return ProjectOut.model_validate(project).model_copy(
        update={
            "membership_role": acc.role,
            "clients_summary": clients_summary,
        }
    )


@router.get("/projects/{project_id}/activities", response_model=ActivityListResponse)
async def list_client_project_activities(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
):
    """Public (non-internal) activities for a client-accessible project."""
    contact = await _require_client_contact(db, user)
    await _require_client_project_access(db, contact, project_id)
    stmt = (
        select(Activity)
        .where(Activity.project_id == project_id)
        .where(Activity.is_internal.is_(False))
        .order_by(Activity.created_at.desc())
        .limit(limit)
    )
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
    return ActivityListResponse(items=items)


@router.get("/projects/{project_id}/tasks", response_model=TaskListResponse)
async def list_client_project_tasks(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Tasks assigned to the current client contact or their client company contacts in an accessible project (SPEC FR-5)."""
    contact = await _require_client_contact(db, user)
    project, acc = await _require_client_project_access(db, contact, project_id)
    if not acc.can_view_tasks:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view tasks in this project",
        )
    peer_rows = await db.scalars(
        select(ClientContact.user_id).where(
            ClientContact.client_id == contact.client_id,
            ClientContact.user_id.is_not(None),
        )
    )
    peer_ids = [u for u in peer_rows.all() if u is not None]
    stmt = (
        select(Task)
        .where(Task.project_id == project_id)
        .where(Task.assignee_id.in_(peer_ids))
        .order_by(Task.updated_at.desc())
    )
    rows = list((await db.scalars(stmt)).all())
    return TaskListResponse(items=[TaskOut.model_validate(r) for r in rows])


@router.post("/projects/{project_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_client_project_task(
    project_id: uuid.UUID,
    body: TaskCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Client participants can create tasks in accessible projects (if permitted)."""
    contact = await _require_client_contact(db, user)
    project, acc = await _require_client_project_access(db, contact, project_id)
    if not acc.can_create_tasks:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create tasks in this project",
        )
    if body.component_id is not None:
        comp = await db.get(Component, body.component_id)
        if comp is None or comp.project_id != project_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="component_id must belong to this project",
            )
    if body.parent_task_id is not None:
        parent = await db.get(Task, body.parent_task_id)
        if parent is None or parent.project_id != project_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="parent_task_id must belong to this project",
            )
    status_val = body.status.strip()
    if status_val not in TASK_STATUSES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_val}. Use one of {sorted(TASK_STATUSES)}",
        )
    ref = await allocate_ref(db, project_id, "task")
    closed_at = datetime.now(timezone.utc) if status_val in {"done", "cancelled"} else None
    row = Task(
        project_id=project_id,
        component_id=body.component_id,
        ref=ref,
        title=body.title.strip(),
        description=body.description.strip() if body.description else None,
        status=status_val,
        priority=body.priority.strip(),
        assignee_id=body.assignee_id,
        reporter_id=user.id,
        due_at=body.due_at,
        parent_task_id=body.parent_task_id,
        is_todo=body.is_todo,
        closed_at=closed_at,
    )
    db.add(row)
    await db.flush()
    await write_activity(
        db=db,
        project_id=project_id,
        subject_type="task",
        subject_id=row.id,
        kind="status_change",
        actor_id=user.id,
        body=f"Created task **{ref}: {body.title.strip()}**",
    )
    await db.commit()
    await db.refresh(row)
    return TaskOut.model_validate(row)


@router.get("/projects/{project_id}/tickets", response_model=TicketListResponse)
async def list_client_project_tickets(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Tickets assigned to the current client contact or their client company contacts."""
    contact = await _require_client_contact(db, user)
    project, acc = await _require_client_project_access(db, contact, project_id)
    if not acc.can_view_tickets:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view tickets in this project",
        )
    peer_rows = await db.scalars(
        select(ClientContact.user_id).where(
            ClientContact.client_id == contact.client_id,
            ClientContact.user_id.is_not(None),
        )
    )
    peer_ids = [u for u in peer_rows.all() if u is not None]
    stmt = (
        select(Ticket)
        .where(Ticket.project_id == project_id)
        .where(Ticket.assignee_id.in_(peer_ids))
        .order_by(Ticket.created_at.asc())
    )
    rows = list((await db.scalars(stmt)).all())
    return TicketListResponse(items=[TicketOut.model_validate(r) for r in rows])
