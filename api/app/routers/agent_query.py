from __future__ import annotations

import logging
import re
import uuid
from typing import Annotated
from urllib.parse import unquote, urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.deps import require_agent_superuser
from app.models.activity import Activity
from app.models.attachment import Attachment
from app.models.client import Client
from app.models.commit_subject_ref import CommitSubjectRef
from app.models.github_commit import GithubCommit
from app.models.project import Project
from app.models.project_client import ProjectClient
from app.models.project_member import ProjectMember
from app.models.prospect import Prospect
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.models.watcher import Watcher
from app.schemas import ClientOut, CommitSubjectRefOut
from app.services.activity_query import (
    activity_count,
    activity_page,
    activity_where_clauses,
    assert_visibility_allowed,
)
from app.services.project_access import (
    can_view_tickets,
    client_company_user_ids,
    is_client_participant,
    require_project_access,
)
from app.services.public_urls import api_base_url, web_base_url

router = APIRouter(prefix="/v1/agent", tags=["agent"])

log = logging.getLogger(__name__)


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



# ── Ticket detail helpers (SPEC amendment 01 §R3–R5) ──────────────────

AGENT_API_VERSION = "1.1.0"
_ATTACHMENT_TARGET_RE = re.compile(r"\]\((/api/attachments/([0-9a-fA-F-]{36}))\)")
_TICKET_REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{1,39}")
_ATTACHMENTS_PER_RESPONSE = 200
_IMAGE_MIMES = frozenset({"image/png", "image/jpeg", "image/gif", "image/webp"})


def _ticket_not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, detail="ticket_not_found")


def _iso(value) -> str | None:
    return value.isoformat() if value is not None else None


def _person(user: User | None, *, include_email: bool) -> dict | None:
    if user is None:
        return None
    return {
        "id": str(user.id),
        "display_name": user.display_name,
        "email": user.email if include_email else None,
    }


def _attachment_dict(
    row: Attachment,
    *,
    base_url: str,
    markdown_ref: str | None,
    created_by: User | None,
) -> dict:
    # An activity-linked file hangs on the comment even when it was uploaded through
    # the ticket (both ids set); prefer the more specific scope.
    scope = "activity" if row.activity_id is not None else "ticket" if row.ticket_id is not None else "task"
    return {
        "id": str(row.id),
        "filename": row.filename,
        "mime": row.mime,
        "size_bytes": row.size_bytes,
        "is_image": row.mime in _IMAGE_MIMES,
        "scope": scope,
        "activity_id": str(row.activity_id) if row.activity_id is not None else None,
        "created_at": _iso(row.created_at),
        "created_by": (
            {"id": str(created_by.id), "display_name": created_by.display_name}
            if created_by is not None
            else None
        ),
        "download_url": f"{base_url}/v1/agent/attachments/{row.id}",
        "markdown_ref": markdown_ref,
    }


def _activity_dict(
    row: Activity,
    attachments: list[Attachment],
    *,
    base_url: str,
    include_email: bool,
    people: dict,
) -> dict:
    actor = row.actor
    return {
        "id": str(row.id),
        "kind": row.kind,
        "actor": _person(actor, include_email=include_email),
        "body": row.body,
        "is_internal": row.is_internal,
        "parent_activity_id": str(row.parent_activity_id) if row.parent_activity_id else None,
        "created_at": _iso(row.created_at),
        "attachments": [
            _attachment_dict(
                att,
                base_url=base_url,
                markdown_ref=None,
                created_by=people.get(att.created_by),
            )
            for att in attachments
        ],
        "meta_json": row.meta_json,
    }


def _resolved_description(description: str | None, download_urls: dict[str, str]) -> str:
    if not description:
        return ""

    def _replace(match: re.Match[str]) -> str:
        url = download_urls.get(match.group(2).lower())
        return f"]({url})" if url else match.group(0)

    return _ATTACHMENT_TARGET_RE.sub(_replace, description)


async def _load_ticket(db: AsyncSession, ticket_ref: str) -> tuple[Ticket, Project] | None:
    try:
        ticket_uuid: uuid.UUID | None = uuid.UUID(ticket_ref)
    except ValueError:
        ticket_uuid = None

    stmt = select(Ticket, Project).join(Project, Ticket.project_id == Project.id)
    if ticket_uuid is not None:
        stmt = stmt.where(Ticket.id == ticket_uuid)
    else:
        ref = ticket_ref.strip().upper()
        if not ref:
            return None
        stmt = stmt.where(func.upper(Ticket.ref) == ref)

    row = (await db.execute(stmt)).first()
    return (row[0], row[1]) if row is not None else None


async def _require_ticket_visible(
    db: AsyncSession,
    acc,
    ticket: Ticket,
) -> None:
    """Client participants only read tickets assigned to their company (web parity)."""
    if not is_client_participant(acc):
        return
    if not can_view_tickets(acc):
        raise _ticket_not_found()
    peers = await client_company_user_ids(db, acc)
    if ticket.assignee_id not in peers:
        raise _ticket_not_found()


# ── Endpoints ──────────────────────────────────────────────────────────


@router.get("/projects")
async def agent_list_projects(
    _admin: Annotated[User, Depends(require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """List all projects with summary stats — single query, no N+1."""

    tenant_id = getattr(request.state, "tenant_id", None)
    tenant_uuid = uuid.UUID(tenant_id) if tenant_id else None

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
    )
    if tenant_uuid is not None:
        stmt = stmt.where(Project.tenant_id == tenant_uuid)
    stmt = stmt.order_by(Project.name.asc())

    rows = (await db.execute(stmt)).all()
    results = [_project_dict(p, ot or 0, oti or 0, mc or 0) for p, ot, oti, mc in rows]

    return _ok(results)


@router.get("/projects/{project_id}/context")
async def agent_project_context(
    project_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """Full project context: details + tasks + tickets + members + clients + GitHub refs."""
    tenant_id = getattr(request.state, "tenant_id", None)
    tenant_uuid = uuid.UUID(tenant_id) if tenant_id else None
    project = await db.scalar(
        select(Project).where(Project.id == project_id)
    )
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")
    if tenant_uuid is not None and project.tenant_id != tenant_uuid:
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
    _admin: Annotated[User, Depends(require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    ref: str | None = Query(default=None, description="Filter by task ref (e.g. TPR-3)"),
    status: str | None = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """List tasks, optionally filtered by ref or status."""
    tenant_id = getattr(request.state, "tenant_id", None)
    tenant_uuid = uuid.UUID(tenant_id) if tenant_id else None
    stmt = select(Task, Project.name).join(Project, Task.project_id == Project.id)
    if tenant_uuid is not None:
        stmt = stmt.where(Project.tenant_id == tenant_uuid)
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
    _admin: Annotated[User, Depends(require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    ref: str | None = Query(default=None, description="Filter by ticket ref (e.g. TPR-T-12)"),
    status: str | None = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """List tickets, optionally filtered by ref or status."""
    tenant_id = getattr(request.state, "tenant_id", None)
    tenant_uuid = uuid.UUID(tenant_id) if tenant_id else None
    stmt = select(Ticket, Project.name).join(Project, Ticket.project_id == Project.id)
    if tenant_uuid is not None:
        stmt = stmt.where(Project.tenant_id == tenant_uuid)
    if ref:
        stmt = stmt.where(Ticket.ref == ref)
    if status:
        stmt = stmt.where(Ticket.status == status)
    stmt = stmt.order_by(Ticket.updated_at.desc()).limit(limit)

    rows = (await db.execute(stmt)).all()
    results = [_ticket_dict(t, pname) for t, pname in rows]
    return _ok(results)



async def _resolve_ticket_for_agent(
    db: AsyncSession,
    admin: User,
    request: Request,
    ticket_ref: str,
):
    """Resolve a ticket address (UUID, ref or web URL segment) and enforce access."""
    tenant_id = getattr(request.state, "tenant_id", None)
    tenant_uuid = uuid.UUID(tenant_id) if tenant_id else None

    loaded = await _load_ticket(db, ticket_ref)
    if loaded is None:
        log.warning("agent.ticket_detail ticket=%s result=not_found", ticket_ref)
        raise _ticket_not_found()
    row, project = loaded

    if tenant_uuid is not None and project.tenant_id != tenant_uuid:
        log.warning("agent.ticket_detail ticket_id=%s result=not_found", row.id)
        raise _ticket_not_found()

    try:
        acc = await require_project_access(db, admin, project.id)
    except HTTPException:
        log.warning("agent.ticket_detail ticket_id=%s project_id=%s result=denied", row.id, project.id)
        raise _ticket_not_found() from None

    try:
        await _require_ticket_visible(db, acc, row)
    except HTTPException:
        log.warning("agent.ticket_detail ticket_id=%s project_id=%s result=denied", row.id, project.id)
        raise

    return row, project, acc


def ticket_ref_from_url(value: str) -> str | None:
    """Extract the ticket UUID or ref from a web ticket URL (absolute or relative)."""
    raw = (value or "").strip()
    if not raw:
        return None

    parsed = urlparse(raw)
    path = unquote(parsed.path) if (parsed.scheme or parsed.netloc) else unquote(raw)
    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        return None

    candidate = segments[-1]
    try:
        return str(uuid.UUID(candidate))
    except ValueError:
        pass
    if _TICKET_REF_RE.fullmatch(candidate):
        return candidate
    return None


async def _ticket_detail_payload(
    db: AsyncSession,
    admin: User,
    request: Request,
    ticket_ref: str,
    *,
    include_activities: bool,
    activity_limit: int,
    include_internal: bool,
) -> dict:
    """Build the R3 ticket-detail payload for an already-validated address."""
    row, project, acc = await _resolve_ticket_for_agent(db, admin, request, ticket_ref)

    include_email = not is_client_participant(acc)
    effective_internal = include_internal and include_email

    base_url = api_base_url(request)
    web_base = web_base_url()

    attachment_rows = list(
        (
            await db.scalars(
                select(Attachment)
                .where(Attachment.ticket_id == row.id)
                .order_by(Attachment.created_at.asc())
            )
        ).all()
    )

    watcher_rows = list(
        (
            await db.scalars(
                select(Watcher).where(
                    Watcher.subject_type == "ticket",
                    Watcher.subject_id == row.id,
                )
            )
        ).all()
    )
    watcher_ids = [w.user_id for w in watcher_rows]

    people_ids: set = {row.reporter_id, row.assignee_id, *watcher_ids, *(a.created_by for a in attachment_rows)}
    people_ids.discard(None)
    people: dict = {}
    if people_ids:
        for person in (await db.scalars(select(User).where(User.id.in_(people_ids)))).all():
            people[person.id] = person

    # Description references drive the attachment order + resolved markdown.
    referenced: list[tuple[str, str]] = []
    seen: set[str] = set()
    for match in _ATTACHMENT_TARGET_RE.finditer(row.description or ""):
        attachment_id = match.group(2).lower()
        if attachment_id not in seen:
            seen.add(attachment_id)
            referenced.append((attachment_id, match.group(1)))

    ordered_ids = [item[0] for item in referenced]
    ordered_ids += [
        str(att.id).lower()
        for att in attachment_rows
        if str(att.id).lower() not in seen
    ]
    by_id = {str(att.id).lower(): att for att in attachment_rows}
    ordered_attachments = [by_id[aid] for aid in ordered_ids if aid in by_id]
    truncated = len(ordered_attachments) > _ATTACHMENTS_PER_RESPONSE
    visible_attachments = ordered_attachments[:_ATTACHMENTS_PER_RESPONSE]

    markdown_refs = {aid: path for aid, path in referenced}
    download_urls = {str(att.id).lower(): f"{base_url}/v1/agent/attachments/{att.id}" for att in visible_attachments}

    attachments = [
        _attachment_dict(
            att,
            base_url=base_url,
            markdown_ref=markdown_refs.get(str(att.id).lower()),
            created_by=people.get(att.created_by),
        )
        for att in visible_attachments
    ]

    activities: list[dict] = []
    activities_page: dict | None = None
    activity_total = 0
    if include_activities:
        clauses = await activity_where_clauses(
            db,
            acc,
            project.id,
            subject_type="ticket",
            subject_id=row.id,
            visibility=None if effective_internal else "external",
        )
        base = select(Activity).where(*clauses)
        activity_total = await activity_count(db, base)
        activity_rows = list(
            (
                await db.scalars(
                    base.order_by(Activity.created_at.desc()).limit(activity_limit)
                )
            ).all()
        )
        activity_attachments: dict = {}
        activity_ids = [a.id for a in activity_rows]
        if activity_ids:
            for att in (
                await db.scalars(
                    select(Attachment).where(Attachment.activity_id.in_(activity_ids))
                )
            ).all():
                activity_attachments.setdefault(att.activity_id, []).append(att)
        activities = [
            _activity_dict(
                item,
                activity_attachments.get(item.id, []),
                base_url=base_url,
                include_email=include_email,
                people=people,
            )
            for item in activity_rows
        ]
        has_more = len(activities) < activity_total
        activities_page = {
            "total": activity_total,
            "has_more": has_more,
            "next_offset": len(activities) if has_more else None,
            "order": "desc",
        }

    commit_rows = (
        await db.execute(
            select(CommitSubjectRef, GithubCommit)
            .outerjoin(GithubCommit, CommitSubjectRef.github_commit_id == GithubCommit.id)
            .where(
                CommitSubjectRef.subject_type == "ticket",
                CommitSubjectRef.subject_id == row.id,
            )
            .order_by(CommitSubjectRef.created_at.desc())
        )
    ).all()
    linked_commits = []
    for ref, commit in commit_rows:
        sha = (commit.sha if commit is not None else ref.sha) or ""
        message = (commit.message if commit is not None else "") or ""
        linked_commits.append(
            {
                "sha": sha,
                "short_sha": sha[:7],
                "html_url": commit.html_url if commit is not None else None,
                "message_preview": message.splitlines()[0][:120] if message else "",
                "author_name": commit.author_name if commit is not None else None,
                "committed_at": _iso(commit.committed_at) if commit is not None else None,
                "state": "resolved" if commit is not None else "pending",
            }
        )

    log.info(
        "agent.ticket_detail ticket_id=%s project_id=%s activities=%s attachments=%s result=ok",
        row.id,
        project.id,
        activity_total,
        len(attachments),
    )

    ticket_payload = {
        "id": str(row.id),
        "ref": row.ref,
        "project_id": str(project.id),
        "title": row.title,
        "description": row.description,
        "description_resolved": _resolved_description(row.description, download_urls),
        "status": row.status,
        "priority": row.priority,
        "queue_slug": row.queue_slug,
        "requester_email": row.requester_email if include_email else None,
        "reporter": _person(people.get(row.reporter_id), include_email=include_email),
        "assignee": _person(people.get(row.assignee_id), include_email=include_email) if row.assignee_id else None,
        "watchers": [
            person
            for person in (
                _person(people.get(wid), include_email=include_email) for wid in watcher_ids
            )
            if person is not None
        ],
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
        "first_response_at": _iso(row.first_response_at),
        "resolved_at": _iso(row.resolved_at),
        "closed_at": _iso(row.closed_at),
        "web_url": (
            f"{web_base}/projects/{project.id}/tickets/{row.id}" if web_base else None
        ),
        "counts": {
            "activities": activity_total if include_activities else 0,
            "attachments": len(ordered_attachments),
            "linked_commits": len(linked_commits),
        },
        "attachments_truncated": truncated,
        "attachments": attachments,
        "linked_commits": linked_commits,
    }
    if include_activities:
        ticket_payload["activities"] = activities
        ticket_payload["activities_page"] = activities_page

    return _ok(
        {
            "agent_api_version": AGENT_API_VERSION,
            "ticket": ticket_payload,
            "project": {
                "id": str(project.id),
                "name": project.name,
                "slug": project.slug,
                "project_key": project.project_key,
            },
        }
    )


@router.get("/tickets/resolve")
async def agent_ticket_detail_by_url(
    admin: Annotated[User, Depends(require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    url: str = Query(min_length=1, max_length=2000, description="Web ticket URL"),
    include_activities: bool = Query(default=True),
    activity_limit: int = Query(default=50, ge=1, le=200),
    include_internal: bool = Query(default=True),
):
    """Ticket detail from a copied web link — e.g. https://host/projects/<p>/tickets/<uuid>."""
    ticket_ref = ticket_ref_from_url(url)
    if ticket_ref is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_ticket_url")
    return await _ticket_detail_payload(
        db,
        admin,
        request,
        ticket_ref,
        include_activities=include_activities,
        activity_limit=activity_limit,
        include_internal=include_internal,
    )


@router.get("/tickets/{ticket}")
async def agent_ticket_detail(
    ticket: str,
    admin: Annotated[User, Depends(require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    include_activities: bool = Query(default=True),
    activity_limit: int = Query(default=50, ge=1, le=200),
    include_internal: bool = Query(default=True),
):
    """Full ticket detail: people, counts, evidence, first activity page, commits, URLs."""
    return await _ticket_detail_payload(
        db,
        admin,
        request,
        ticket,
        include_activities=include_activities,
        activity_limit=activity_limit,
        include_internal=include_internal,
    )


@router.get("/tickets/{ticket}/activities")
async def agent_ticket_activities(
    ticket: str,
    admin: Annotated[User, Depends(require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order: str = Query(default="desc", pattern=r"^(asc|desc)$"),
    kind: str | None = Query(default=None),
    include_internal: bool = Query(default=True),
    visibility: str = Query(default="all", pattern=r"^(all|internal|external)$"),
):
    """Paginated ticket activity/comment feed (newest first by default)."""
    row, project, acc = await _resolve_ticket_for_agent(db, admin, request, ticket)
    client_caller = is_client_participant(acc)

    requested_visibility = None if visibility == "all" else visibility
    assert_visibility_allowed(acc, requested_visibility)
    effective_visibility = requested_visibility
    if not include_internal or client_caller:
        effective_visibility = "external"

    clauses = await activity_where_clauses(
        db,
        acc,
        project.id,
        subject_type="ticket",
        subject_id=row.id,
        kind=kind,
        visibility=effective_visibility,
    )
    base = select(Activity).where(*clauses)
    total = await activity_count(db, base)
    activity_rows = list(
        (await db.scalars(activity_page(base, order=order, limit=limit, offset=offset))).all()
    )

    grouped: dict = {}
    if activity_rows:
        activity_ids = [item.id for item in activity_rows]
        for att in (
            await db.scalars(
                select(Attachment).where(Attachment.activity_id.in_(activity_ids))
            )
        ).all():
            grouped.setdefault(att.activity_id, []).append(att)

    people: dict = {}
    creator_ids = {att.created_by for attachments in grouped.values() for att in attachments}
    if creator_ids:
        for person in (await db.scalars(select(User).where(User.id.in_(creator_ids)))).all():
            people[person.id] = person

    base_url = api_base_url(request)
    items = [
        _activity_dict(
            item,
            grouped.get(item.id, []),
            base_url=base_url,
            include_email=not client_caller,
            people=people,
        )
        for item in activity_rows
    ]
    has_more = offset + len(items) < total
    log.info(
        "agent.ticket_activities ticket_id=%s page=%s/%s result=ok",
        row.id,
        offset,
        limit,
    )

    return _ok(
        {
            "items": items,
            "total": total,
            "has_more": has_more,
            "next_offset": offset + len(items) if has_more else None,
            "order": order,
        }
    )


@router.get("/search")
async def agent_search(
    _admin: Annotated[User, Depends(require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=50),
):
    """Unified search across projects, tasks, tickets, clients, and prospects."""
    term = q.strip()
    results: list[dict] = []
    st_tenant_id = getattr(request.state, "tenant_id", None)
    st_tenant_uuid = uuid.UUID(st_tenant_id) if st_tenant_id else None

    # Projects
    if len(results) < limit:
        stmt = (
            select(Project.id, Project.name, Project.slug, Project.status)
        )
        if st_tenant_uuid is not None:
            stmt = stmt.where(Project.tenant_id == st_tenant_uuid)
        stmt = stmt.where(Project.name.ilike(f"%{term}%")).order_by(Project.updated_at.desc()).limit(limit - len(results))
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
        )
        if st_tenant_uuid is not None:
            stmt = stmt.where(Project.tenant_id == st_tenant_uuid)
        rows = (await db.execute(
            stmt.order_by(Task.updated_at.desc()).limit(limit - len(results))
        )).all()
        for tid, title, ref_, status_, _pid, pname in rows:
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
        )
        if st_tenant_uuid is not None:
            stmt = stmt.where(Project.tenant_id == st_tenant_uuid)
        rows = (await db.execute(
            stmt.order_by(Ticket.updated_at.desc()).limit(limit - len(results))
        )).all()
        for tid, title, ref_, status_, _pid, pname in rows:
            results.append({
                "kind": "ticket", "id": str(tid), "label": title,
                "subtitle": f"[{ref_ or '—'}] {pname}",
                "ref": ref_, "status": status_,
            })

    # Clients
    if len(results) < limit:
        stmt = (
            select(Client.id, Client.name, Client.slug)
        )
        if st_tenant_uuid is not None:
            stmt = stmt.where(Client.tenant_id == st_tenant_uuid)
        stmt = stmt.where(Client.name.ilike(f"%{term}%")).order_by(Client.name.asc()).limit(limit - len(results))
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
        )
        if st_tenant_uuid is not None:
            stmt = stmt.where(Prospect.tenant_id == st_tenant_uuid)
        stmt = stmt.where(Prospect.company_name.ilike(f"%{term}%")).order_by(Prospect.updated_at.desc()).limit(limit - len(results))
        rows = (await db.execute(stmt)).all()
        for pid, company, stage in rows:
            results.append({
                "kind": "prospect", "id": str(pid), "label": company,
                "subtitle": f"Prospect — {stage}", "ref": None, "status": stage,
            })

    return _ok(results)
