"""Calendar, workload, dependencies, time, and CRM history. Dates are not moved."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_tenant, get_current_user, require_superuser
from app.models.activity import Activity
from app.models.client import Client
from app.models.planning import CrmFieldChange, ProjectBudget, TaskDependency, TimeEntry
from app.models.project import Project
from app.models.project_client import ProjectClient
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User
from app.services.project_access import (
    MemberRole,
    can_create_tasks,
    can_view_tasks,
    require_project_access,
    require_role,
)
from app.services.task_extras import add_dependency

router = APIRouter(prefix="/v1/planning", tags=["planning"])
project_router = APIRouter(prefix="/v1/projects/{project_id}", tags=["planning"])


class DependencyIn(BaseModel):
    predecessor_id: uuid.UUID
    successor_id: uuid.UUID


class TimeIn(BaseModel):
    minutes: int = Field(ge=1, le=1440)
    work_date: date
    task_id: uuid.UUID | None = None
    note: str | None = Field(default=None, max_length=2000)


class BudgetIn(BaseModel):
    revenue_amount: float | None = Field(default=None, ge=0)
    hourly_cost: float | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)


@router.get("/calendar")
async def calendar(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=100, ge=1, le=300),
):
    member = select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)
    stmt = (
        select(Task, Project.name)
        .join(Project, Project.id == Task.project_id)
        .where(Task.project_id.in_(member), Task.due_at.is_not(None))
        .order_by(Task.due_at.asc())
        .limit(limit)
    )
    if user.tenant_id is not None:
        stmt = stmt.where(Project.tenant_id == user.tenant_id)
    rows = (await db.execute(stmt)).all()
    return {
        "items": [
            {
                "id": str(task.id),
                "title": task.title,
                "status": task.status,
                "due_at": task.due_at.isoformat() if task.due_at else None,
                "project_id": str(task.project_id),
                "project_name": project_name,
                "recurrence": task.recurrence,
            }
            for task, project_name in rows
        ]
    }


@router.get("/workload")
async def workload(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    member = select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)
    stmt = (
        select(Task.assignee_id, User.display_name, User.email, func.count())
        .join(Project, Project.id == Task.project_id)
        .outerjoin(User, User.id == Task.assignee_id)
        .where(Task.project_id.in_(member), Task.closed_at.is_(None))
        .group_by(Task.assignee_id, User.display_name, User.email)
        .order_by(func.count().desc())
    )
    if user.tenant_id is not None:
        stmt = stmt.where(Project.tenant_id == user.tenant_id)
    rows = (await db.execute(stmt)).all()
    return {
        "items": [
            {
                "assignee_id": str(assignee_id) if assignee_id else None,
                "name": name or email or "Unassigned",
                "open_tasks": count,
            }
            for assignee_id, name, email, count in rows
        ]
    }


@router.get("/changes")
async def field_changes(
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    entity_type: str = Query(pattern="^(prospect|client)$"),
    entity_id: uuid.UUID = Query(),
):
    stmt = (
        select(CrmFieldChange)
        .where(CrmFieldChange.entity_type == entity_type, CrmFieldChange.entity_id == entity_id)
        .order_by(CrmFieldChange.created_at.desc())
        .limit(50)
    )
    if user.tenant_id is not None:
        stmt = stmt.where(CrmFieldChange.tenant_id == user.tenant_id)
    rows = list((await db.scalars(stmt)).all())
    return {
        "items": [
            {
                "id": str(row.id),
                "field_name": row.field_name,
                "old_value": row.old_value,
                "new_value": row.new_value,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.get("/clients/{client_id}/timeline")
async def client_timeline(
    client_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tenant = await get_current_tenant(request, db)
    client = await db.get(Client, client_id)
    if client is None or (
        tenant is not None and user.tenant_id is not None and client.tenant_id != user.tenant_id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client not found")
    project_ids = select(ProjectClient.project_id).where(ProjectClient.client_id == client_id)
    rows = list(
        (
            await db.scalars(
                select(Activity)
                .where(Activity.project_id.in_(project_ids))
                .order_by(Activity.created_at.desc())
                .limit(40)
            )
        ).all()
    )
    return {
        "items": [
            {
                "id": str(row.id),
                "project_id": str(row.project_id),
                "kind": row.kind,
                "body": row.body,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@project_router.get("/dependencies")
async def list_dependencies(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not can_view_tasks(acc):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Forbidden")
    rows = list(
        (
            await db.scalars(select(TaskDependency).where(TaskDependency.project_id == project_id))
        ).all()
    )
    return {
        "items": [
            {
                "id": str(row.id),
                "predecessor_id": str(row.predecessor_id),
                "successor_id": str(row.successor_id),
                "dependency_type": row.dependency_type,
            }
            for row in rows
        ]
    }


@project_router.post("/dependencies", status_code=status.HTTP_201_CREATED)
async def create_dependency(
    project_id: uuid.UUID,
    body: DependencyIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not can_create_tasks(acc):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Forbidden")
    row = await add_dependency(
        db,
        project_id=project_id,
        predecessor_id=body.predecessor_id,
        successor_id=body.successor_id,
    )
    await db.commit()
    return {"id": str(row.id)}


@project_router.post("/time-entries", status_code=status.HTTP_201_CREATED)
async def log_time(
    project_id: uuid.UUID,
    body: TimeIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not can_create_tasks(acc):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if body.task_id is not None:
        task = await db.get(Task, body.task_id)
        if task is None or task.project_id != project_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Task is not in this project")
    row = TimeEntry(
        project_id=project_id,
        task_id=body.task_id,
        user_id=user.id,
        minutes=body.minutes,
        note=(body.note or "").strip() or None,
        work_date=body.work_date,
    )
    db.add(row)
    await db.commit()
    return {"id": str(row.id)}


@project_router.put("/budget")
async def save_budget(
    project_id: uuid.UUID,
    body: BudgetIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    require_role(acc, MemberRole.maintainer)
    row = await db.get(ProjectBudget, project_id)
    if row is None:
        row = ProjectBudget(project_id=project_id)
        db.add(row)
    row.revenue_amount = body.revenue_amount
    row.hourly_cost = body.hourly_cost
    row.currency = body.currency.upper()
    await db.commit()
    return {"project_id": str(project_id)}


@project_router.get("/profitability")
async def profitability(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not can_view_tasks(acc):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Forbidden")
    minutes = await db.scalar(
        select(func.coalesce(func.sum(TimeEntry.minutes), 0)).where(TimeEntry.project_id == project_id)
    )
    budget = await db.get(ProjectBudget, project_id)
    hours = float(minutes or 0) / 60
    revenue = float(budget.revenue_amount) if budget and budget.revenue_amount is not None else None
    hourly = float(budget.hourly_cost) if budget and budget.hourly_cost is not None else None
    labor = round(hours * hourly, 2) if hourly is not None else None
    margin = round(revenue - labor, 2) if revenue is not None and labor is not None else None
    return {
        "minutes": int(minutes or 0),
        "hours": round(hours, 2),
        "revenue_amount": revenue,
        "hourly_cost": hourly,
        "labor_cost": labor,
        "margin": margin,
        "currency": budget.currency if budget else "USD",
    }
