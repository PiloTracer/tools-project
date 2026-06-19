"""Client portal endpoints for external client participants."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.deps import get_current_user
from app.models.activity import Activity
from app.models.client_contact import ClientContact
from app.models.project import Project
from app.models.project_client import ProjectClient
from app.models.project_client_access import ProjectClientAccess
from app.models.task import Task
from app.models.user import User
from app.schemas import (
    ActivityListResponse,
    ActivityOut,
    ClientSummary,
    ProjectListResponse,
    ProjectOut,
    TaskListResponse,
    TaskOut,
)

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
    items = [
        ActivityOut.model_validate(r).model_copy(
            update={"actor_email": r.actor.email if r.actor else None}
        )
        for r in rows
    ]
    return ActivityListResponse(items=items)


@router.get("/projects/{project_id}/tasks", response_model=TaskListResponse)
async def list_client_project_tasks(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Tasks assigned to the current client contact in an accessible project."""
    contact = await _require_client_contact(db, user)
    project, acc = await _require_client_project_access(db, contact, project_id)
    if not acc.can_view_tasks:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view tasks in this project",
        )
    stmt = (
        select(Task)
        .where(Task.project_id == project_id)
        .where(Task.assignee_id == user.id)
        .order_by(Task.updated_at.desc())
    )
    rows = list((await db.scalars(stmt)).all())
    return TaskListResponse(items=[TaskOut.model_validate(r) for r in rows])
