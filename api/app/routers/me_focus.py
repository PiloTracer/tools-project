from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.activity import Activity
from app.models.client import Client
from app.models.mention import Mention
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.prospect import Prospect
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.models.watcher import Watcher
from app.schemas import (
    MentionListResponse,
    MentionWithContext,
    RefSearchResult,
    TaskOut,
    TodayResponse,
    TodayTaskBundle,
    UnifiedSearchHit,
    UserSearchResult,
    WatchCreate,
    WatchDelete,
    WatchListResponse,
    WatchOut,
)
from app.services.project_access import require_project_access

router = APIRouter(prefix="/v1/me", tags=["me"])


@router.get("/today", response_model=TodayResponse)
async def my_today(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=7, ge=1, le=30),
):
    """Assigned tasks with a due date in the rolling window, plus watched items."""
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    horizon = start + timedelta(days=days + 1)
    stmt = (
        select(Task, Project.name)
        .join(Project, Task.project_id == Project.id)
        .where(Task.assignee_id == user.id)
        .where(Task.due_at.is_not(None))
        .where(Task.due_at >= start)
        .where(Task.due_at < horizon)
        .where(Task.status.not_in(["done", "cancelled"]))
        .order_by(Task.due_at.asc())
        .limit(100)
    )
    result = await db.execute(stmt)
    bundles: list[TodayTaskBundle] = []
    seen_task_ids: set[uuid.UUID] = set()
    for task, project_name in result.all():
        bundles.append(
            TodayTaskBundle(
                task=TaskOut.model_validate(task),
                project_name=project_name,
            )
        )
        seen_task_ids.add(task.id)

    # Add watched tasks that are not terminal and not already in the list
    wt_stmt = (
        select(Watcher.subject_id, Watcher.subject_type)
        .where(Watcher.user_id == user.id)
    )
    wt_result = await db.execute(wt_stmt)
    watched_tasks: list[uuid.UUID] = []
    watched_tickets: list[uuid.UUID] = []
    for sid, stype in wt_result.all():
        if stype == "task":
            watched_tasks.append(sid)
        elif stype == "ticket":
            watched_tickets.append(sid)

    if watched_tasks:
        wtask_stmt = (
            select(Task, Project.name)
            .join(Project, Task.project_id == Project.id)
            .where(Task.id.in_(watched_tasks))
            .where(Task.status.not_in(["done", "cancelled"]))
            .order_by(Task.updated_at.desc())
            .limit(50)
        )
        wtask_result = await db.execute(wtask_stmt)
        for task, project_name in wtask_result.all():
            if task.id not in seen_task_ids:
                bundles.append(
                    TodayTaskBundle(
                        task=TaskOut.model_validate(task),
                        project_name=f"[Watched] {project_name}",
                    )
                )
                seen_task_ids.add(task.id)

    watched_ticket_bundles: list[TodayTicketBundle] = []
    if watched_tickets:
        wticket_stmt = (
            select(Ticket, Project.name)
            .join(Project, Ticket.project_id == Project.id)
            .where(Ticket.id.in_(watched_tickets))
            .where(Ticket.status.not_in(["resolved", "closed"]))
            .order_by(Ticket.updated_at.desc())
            .limit(50)
        )
        wticket_result = await db.execute(wticket_stmt)
        for ticket, project_name in wticket_result.all():
            watched_ticket_bundles.append(
                TodayTicketBundle(
                    ticket=TicketOut.model_validate(ticket),
                    project_name=f"[Watched] {project_name}",
                )
            )

    return TodayResponse(items=bundles, watched_tickets=watched_ticket_bundles)


@router.post("/watch", response_model=WatchOut, status_code=201)
async def watch_subject(
    body: WatchCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.subject_type == "project":
        await require_project_access(db, user, body.subject_id)
    elif body.subject_type == "task":
        t = await db.get(Task, body.subject_id)
        if t is None:
            raise HTTPException(status_code=404, detail="Task not found")
        await require_project_access(db, user, t.project_id)
    elif body.subject_type == "ticket":
        t = await db.get(Ticket, body.subject_id)
        if t is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        await require_project_access(db, user, t.project_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid subject_type")

    existing = await db.scalar(
        select(Watcher).where(
            Watcher.user_id == user.id,
            Watcher.subject_type == body.subject_type,
            Watcher.subject_id == body.subject_id,
        )
    )
    if existing is not None:
        return WatchOut.model_validate(existing)

    row = Watcher(
        user_id=user.id,
        subject_type=body.subject_type,
        subject_id=body.subject_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return WatchOut.model_validate(row)


@router.delete("/watch", status_code=204)
async def unwatch_subject(
    body: WatchDelete,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.scalar(
        select(Watcher).where(
            Watcher.user_id == user.id,
            Watcher.subject_type == body.subject_type,
            Watcher.subject_id == body.subject_id,
        )
    )
    if row is not None:
        await db.delete(row)
        await db.commit()
    return Response(status_code=204)


@router.get("/watches", response_model=WatchListResponse)
async def my_watches(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = list((await db.scalars(
        select(Watcher).where(Watcher.user_id == user.id).order_by(Watcher.created_at.desc())
    )).all())
    return WatchListResponse(items=[WatchOut.model_validate(r) for r in rows])


@router.get("/mentions", response_model=MentionListResponse)
async def my_mentions(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
):
    stmt = (
        select(Mention, Activity.body, Project.name)
        .join(Activity, Mention.activity_id == Activity.id)
        .join(Project, Mention.project_id == Project.id)
        .where(Mention.mentioned_user_id == user.id)
        .order_by(Mention.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    items: list[MentionWithContext] = []
    for m, body, project_name in result.all():
        excerpt = (body or "")[:200]
        if len(body or "") > 200:
            excerpt += "…"
        items.append(
            MentionWithContext(
                id=m.id,
                project_id=m.project_id,
                project_name=project_name,
                activity_id=m.activity_id,
                excerpt=excerpt,
                created_at=m.created_at,
            )
        )
    return MentionListResponse(items=items)


@router.get("/users/search")
async def search_users(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query(default="", min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
):
    """Return users with a matching email prefix (for @mention autocomplete)."""
    stmt = (
        select(User.id, User.email, User.display_name)
        .where(User.is_active.is_(True))
        .where(User.email.ilike(f"{q.strip()}%"))
        .order_by(User.email.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [UserSearchResult(id=uid, email=email, display_name=name) for uid, email, name in rows]


@router.get("/refs/search")
async def search_refs(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query(default="", min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
):
    """Return tasks and tickets matching a ref prefix or title fragment, for #ref autocomplete."""
    term = q.strip()
    results: list[RefSearchResult] = []

    task_stmt = (
        select(Task.id, Task.ref, Task.title, Task.project_id, Project.name)
        .join(Project, Task.project_id == Project.id)
        .where(
            (Task.ref.ilike(f"{term}%")) | (Task.title.ilike(f"%{term}%"))
        )
        .order_by(Task.updated_at.desc())
        .limit(limit)
    )
    task_rows = (await db.execute(task_stmt)).all()
    for tid, ref, title, pid, pname in task_rows:
        results.append(RefSearchResult(
            id=str(tid), ref=ref, title=title,
            project_id=str(pid), project_name=pname, kind="task",
        ))

    if len(results) < limit:
        ticket_stmt = (
            select(Ticket.id, Ticket.ref, Ticket.title, Ticket.project_id, Project.name)
            .join(Project, Ticket.project_id == Project.id)
            .where(
                (Ticket.ref.ilike(f"{term}%")) | (Ticket.title.ilike(f"%{term}%"))
            )
            .order_by(Ticket.updated_at.desc())
            .limit(limit - len(results))
        )
        ticket_rows = (await db.execute(ticket_stmt)).all()
        for tid, ref, title, pid, pname in ticket_rows:
            results.append(RefSearchResult(
                id=str(tid), ref=ref, title=title,
                project_id=str(pid), project_name=pname, kind="ticket",
            ))

    return results


@router.get("/search")
async def unified_search(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query(default="", min_length=1),
    limit: int = Query(default=15, ge=1, le=50),
):
    """Unified search across projects, tasks, tickets, clients, and prospects."""
    term = q.strip()
    results: list[UnifiedSearchHit] = []

    # Get projects the user can access
    member_subq = select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)

    # Projects
    if len(results) < limit:
        stmt = (
            select(Project.id, Project.name, Project.slug)
            .where(Project.id.in_(member_subq))
            .where(Project.name.ilike(f"%{term}%"))
            .order_by(Project.updated_at.desc())
            .limit(limit - len(results))
        )
        rows = (await db.execute(stmt)).all()
        for pid, name, slug in rows:
            results.append(UnifiedSearchHit(
                id=str(pid), label=name,
                subtitle=f"Project — {slug}",
                href=f"/projects/{pid}", kind="project",
            ))

    # Tasks (only in accessible projects)
    if len(results) < limit:
        stmt = (
            select(Task.id, Task.title, Task.ref, Task.project_id, Project.name)
            .join(Project, Task.project_id == Project.id)
            .where(Task.project_id.in_(member_subq))
            .where((Task.title.ilike(f"%{term}%")) | (Task.ref.ilike(f"{term}%")))
            .order_by(Task.updated_at.desc())
            .limit(limit - len(results))
        )
        rows = (await db.execute(stmt)).all()
        for tid, title, ref, pid, pname in rows:
            results.append(UnifiedSearchHit(
                id=str(tid), label=title,
                subtitle=f"[{ref or '—'}] {pname}",
                href=f"/projects/{pid}/tasks/{tid}",
                kind="task",
            ))

    # Tickets (only in accessible projects)
    if len(results) < limit:
        stmt = (
            select(Ticket.id, Ticket.title, Ticket.ref, Ticket.project_id, Project.name)
            .join(Project, Ticket.project_id == Project.id)
            .where(Ticket.project_id.in_(member_subq))
            .where((Ticket.title.ilike(f"%{term}%")) | (Ticket.ref.ilike(f"{term}%")))
            .order_by(Ticket.updated_at.desc())
            .limit(limit - len(results))
        )
        rows = (await db.execute(stmt)).all()
        for tid, title, ref, pid, pname in rows:
            results.append(UnifiedSearchHit(
                id=str(tid), label=title,
                subtitle=f"[{ref or '—'}] {pname}",
                href=f"/projects/{pid}/tickets/{tid}",
                kind="ticket",
            ))

    # Clients (all authenticated users can search)
    if len(results) < limit:
        stmt = (
            select(Client.id, Client.name, Client.slug)
            .where(Client.name.ilike(f"%{term}%"))
            .order_by(Client.name.asc())
            .limit(limit - len(results))
        )
        rows = (await db.execute(stmt)).all()
        for cid, name, slug in rows:
            results.append(UnifiedSearchHit(
                id=str(cid), label=name, subtitle=f"Client — {slug}",
                href=f"/clients/{cid}", kind="client",
            ))

    # Prospects (all authenticated users can search)
    if len(results) < limit:
        stmt = (
            select(Prospect.id, Prospect.company_name, Prospect.pipeline_stage)
            .where(Prospect.company_name.ilike(f"%{term}%"))
            .order_by(Prospect.updated_at.desc())
            .limit(limit - len(results))
        )
        rows = (await db.execute(stmt)).all()
        for pid, company, stage in rows:
            results.append(UnifiedSearchHit(
                id=str(pid), label=company, subtitle=f"Prospect — {stage}",
                href=f"/prospects/{pid}", kind="prospect",
            ))

    return results
