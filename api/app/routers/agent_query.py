from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.deps import require_agent_or_user
from app.models.client import Client
from app.models.commit_subject_ref import CommitSubjectRef
from app.models.project import Project
from app.models.project_client import ProjectClient
from app.models.project_member import ProjectMember
from app.models.prospect import Prospect
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas import ClientOut, CommitSubjectRefOut

router = APIRouter(prefix="/v1/agent", tags=["agent"])


def _require_agent_superuser(
    user: Annotated[User, Depends(require_agent_or_user)],
) -> User:
    """Agent endpoints require superuser-level access.

    When the caller uses the API key, the synthetic agent user has
    is_superuser=True. When using Bearer JWT, the real user must be
    a superuser — by design per SPEC §R2: "superuser-only gate for
    global views". Regular users use existing project-scoped endpoints.
    """
    if not user.is_superuser:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Agent endpoints require superuser privileges",
        )
    return user


# ── Response models ────────────────────────────────────────────────────


class AgentResponse(BaseModel):
    ok: bool = True
    data: object


class ProjectSummaryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    slug: str
    description: str | None
    status: str
    project_key: str | None
    github_task_registry_enabled: bool
    auto_prefix_enabled: bool
    open_tasks: int = 0
    open_tickets: int = 0
    member_count: int = 0
    created_at: str
    updated_at: str


class MemberOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    email: str
    display_name: str
    role: str


class TaskRefOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    ref: str | None
    title: str
    description: str | None
    status: str
    priority: str
    assignee_id: str | None
    due_at: str | None
    is_todo: bool
    project_id: str
    project_name: str
    created_at: str
    updated_at: str


class TicketRefOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    ref: str | None
    title: str
    description: str | None
    status: str
    priority: str
    assignee_id: str | None
    project_id: str
    project_name: str
    created_at: str
    updated_at: str


class ProjectContextOut(BaseModel):
    model_config = {"from_attributes": True}

    project: ProjectSummaryOut
    members: list[MemberOut]
    tasks: list[TaskRefOut]
    tickets: list[TicketRefOut]
    clients: list[dict]
    github_refs: list[dict]


class SearchHitOut(BaseModel):
    model_config = {"from_attributes": True}

    kind: str
    id: str
    label: str
    subtitle: str
    ref: str | None = None
    status: str | None = None


# ── Dict helpers (serialize ORM → plain dict for Pydantic model_validate) ─


def _project_dict(p: Project, open_tasks=0, open_tickets=0, member_count=0) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "slug": p.slug,
        "description": p.description,
        "status": p.status,
        "project_key": p.project_key,
        "github_task_registry_enabled": p.github_task_registry_enabled,
        "auto_prefix_enabled": p.auto_prefix_enabled,
        "open_tasks": open_tasks or 0,
        "open_tickets": open_tickets or 0,
        "member_count": member_count or 0,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


def _task_dict(t: Task, project_name: str) -> dict:
    return {
        "id": str(t.id),
        "ref": t.ref,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "priority": t.priority,
        "assignee_id": str(t.assignee_id) if t.assignee_id else None,
        "due_at": t.due_at.isoformat() if t.due_at else None,
        "is_todo": t.is_todo,
        "project_id": str(t.project_id),
        "project_name": project_name,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
    }


def _ticket_dict(t: Ticket, project_name: str) -> dict:
    return {
        "id": str(t.id),
        "ref": t.ref,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "priority": t.priority,
        "assignee_id": str(t.assignee_id) if t.assignee_id else None,
        "project_id": str(t.project_id),
        "project_name": project_name,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
    }


def _ok(data) -> dict:
    return AgentResponse(data=data).model_dump()


# ── Endpoints ──────────────────────────────────────────────────────────


@router.get("/projects")
async def agent_list_projects(
    _admin: Annotated[User, Depends(_require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all projects with summary stats — single query, no N+1."""

    open_task_subq = (
        select(func.count(Task.id))
        .where(Task.project_id == Project.id, Task.status.not_in(("done", "cancelled")))
        .correlate(Project)
        .scalar_subquery()
    )
    open_ticket_subq = (
        select(func.count(Ticket.id))
        .where(Ticket.project_id == Project.id, Ticket.status.not_in(("closed", "resolved")))
        .correlate(Project)
        .scalar_subquery()
    )
    member_subq = (
        select(func.count(ProjectMember.user_id))
        .where(ProjectMember.project_id == Project.id)
        .correlate(Project)
        .scalar_subquery()
    )

    stmt = (
        select(
            Project,
            open_task_subq.label("open_tasks"),
            open_ticket_subq.label("open_tickets"),
            member_subq.label("member_count"),
        )
        .order_by(Project.name.asc())
    )

    rows = (await db.execute(stmt)).all()
    results = [_project_dict(p, ot or 0, oti or 0, mc or 0) for p, ot, oti, mc in rows]

    return _ok(results)


@router.get("/projects/{project_id}/context")
async def agent_project_context(
    project_id: uuid.UUID,
    _admin: Annotated[User, Depends(_require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Full project context: details + tasks + tickets + members + clients + GitHub refs."""
    project = await db.scalar(
        select(Project).where(Project.id == project_id)
    )
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Tasks
    task_rows = (await db.execute(
        select(Task).where(Task.project_id == project_id)
        .order_by(Task.created_at.desc())
        .limit(100)
    )).scalars().all()
    tasks = [_task_dict(t, project.name) for t in task_rows]

    # Tickets
    ticket_rows = (await db.execute(
        select(Ticket).where(Ticket.project_id == project_id)
        .order_by(Ticket.created_at.desc())
        .limit(100)
    )).scalars().all()
    tickets = [_ticket_dict(t, project.name) for t in ticket_rows]

    # Members
    member_rows = (await db.execute(
        select(User.id, User.email, User.display_name, ProjectMember.role)
        .join(ProjectMember, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id == project_id)
    )).all()
    members = [
        {"id": str(uid), "email": email, "display_name": name, "role": role}
        for uid, email, name, role in member_rows
    ]

    # Clients linked to this project
    client_rows = (await db.execute(
        select(Client)
        .join(ProjectClient, ProjectClient.client_id == Client.id)
        .where(ProjectClient.project_id == project_id)
    )).scalars().all()

    # GitHub refs
    ref_rows = (await db.execute(
        select(CommitSubjectRef)
        .where(CommitSubjectRef.project_id == project_id)
        .options(selectinload(CommitSubjectRef.commit))
        .order_by(CommitSubjectRef.created_at.desc())
        .limit(50)
    )).scalars().all()

    return _ok({
        "project": _project_dict(project),
        "members": members,
        "tasks": tasks,
        "tickets": tickets,
        "clients": [ClientOut.model_validate(c).model_dump() for c in client_rows],
        "github_refs": [CommitSubjectRefOut.model_validate(r).model_dump() for r in ref_rows],
    })


@router.get("/tasks")
async def agent_list_tasks(
    _admin: Annotated[User, Depends(_require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    ref: str | None = Query(default=None, description="Filter by task ref (e.g. TPR-3)"),
    status: str | None = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """List tasks, optionally filtered by ref or status."""
    stmt = select(Task, Project.name).join(Project, Task.project_id == Project.id)
    if ref:
        stmt = stmt.where(Task.ref == ref)
    if status:
        stmt = stmt.where(Task.status == status)
    stmt = stmt.order_by(Task.updated_at.desc()).limit(limit)

    rows = (await db.execute(stmt)).all()
    results = [_task_dict(t, pname) for t, pname in rows]
    return _ok(results)


@router.get("/tickets")
async def agent_list_tickets(
    _admin: Annotated[User, Depends(_require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    ref: str | None = Query(default=None, description="Filter by ticket ref (e.g. TPR-T-12)"),
    status: str | None = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """List tickets, optionally filtered by ref or status."""
    stmt = select(Ticket, Project.name).join(Project, Ticket.project_id == Project.id)
    if ref:
        stmt = stmt.where(Ticket.ref == ref)
    if status:
        stmt = stmt.where(Ticket.status == status)
    stmt = stmt.order_by(Ticket.updated_at.desc()).limit(limit)

    rows = (await db.execute(stmt)).all()
    results = [_ticket_dict(t, pname) for t, pname in rows]
    return _ok(results)


@router.get("/search")
async def agent_search(
    _admin: Annotated[User, Depends(_require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=50),
):
    """Unified search across projects, tasks, tickets, clients, and prospects."""
    term = q.strip()
    results: list[dict] = []

    # Projects
    if len(results) < limit:
        stmt = (
            select(Project.id, Project.name, Project.slug, Project.status)
            .where(Project.name.ilike(f"%{term}%"))
            .order_by(Project.updated_at.desc())
            .limit(limit - len(results))
        )
        rows = (await db.execute(stmt)).all()
        for pid, name, slug, status_ in rows:
            results.append({
                "kind": "project", "id": str(pid), "label": name,
                "subtitle": f"Project — {slug}", "ref": None, "status": status_,
            })

    # Tasks
    if len(results) < limit:
        stmt = (
            select(Task.id, Task.title, Task.ref, Task.status, Task.project_id, Project.name)
            .join(Project, Task.project_id == Project.id)
            .where((Task.title.ilike(f"%{term}%")) | (Task.ref.ilike(f"{term}%")))
            .order_by(Task.updated_at.desc())
            .limit(limit - len(results))
        )
        rows = (await db.execute(stmt)).all()
        for tid, title, ref_, status_, pid, pname in rows:
            results.append({
                "kind": "task", "id": str(tid), "label": title,
                "subtitle": f"[{ref_ or '—'}] {pname}",
                "ref": ref_, "status": status_,
            })

    # Tickets
    if len(results) < limit:
        stmt = (
            select(Ticket.id, Ticket.title, Ticket.ref, Ticket.status, Ticket.project_id, Project.name)
            .join(Project, Ticket.project_id == Project.id)
            .where((Ticket.title.ilike(f"%{term}%")) | (Ticket.ref.ilike(f"{term}%")))
            .order_by(Ticket.updated_at.desc())
            .limit(limit - len(results))
        )
        rows = (await db.execute(stmt)).all()
        for tid, title, ref_, status_, pid, pname in rows:
            results.append({
                "kind": "ticket", "id": str(tid), "label": title,
                "subtitle": f"[{ref_ or '—'}] {pname}",
                "ref": ref_, "status": status_,
            })

    # Clients
    if len(results) < limit:
        stmt = (
            select(Client.id, Client.name, Client.slug)
            .where(Client.name.ilike(f"%{term}%"))
            .order_by(Client.name.asc())
            .limit(limit - len(results))
        )
        rows = (await db.execute(stmt)).all()
        for cid, name, slug in rows:
            results.append({
                "kind": "client", "id": str(cid), "label": name,
                "subtitle": f"Client — {slug}", "ref": None, "status": None,
            })

    # Prospects
    if len(results) < limit:
        stmt = (
            select(Prospect.id, Prospect.company_name, Prospect.pipeline_stage)
            .where(Prospect.company_name.ilike(f"%{term}%"))
            .order_by(Prospect.updated_at.desc())
            .limit(limit - len(results))
        )
        rows = (await db.execute(stmt)).all()
        for pid, company, stage in rows:
            results.append({
                "kind": "prospect", "id": str(pid), "label": company,
                "subtitle": f"Prospect — {stage}", "ref": None, "status": stage,
            })

    return _ok(results)
