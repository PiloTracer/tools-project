from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.deps import get_current_user
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas import (
    ProjectCreate,
    ProjectHealth,
    ProjectListResponse,
    ProjectMemberCreate,
    ProjectMemberListResponse,
    ProjectMemberOut,
    ProjectMemberPatch,
    ProjectOut,
    ProjectUpdate,
)
from app.services.project_access import (
    MemberRole,
    assert_can_assign_role,
    can_edit_project_meta,
    can_manage_members,
    count_role_members,
    parse_member_role,
    require_project_access,
)

router = APIRouter(prefix="/v1/projects", tags=["projects"])

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")[:80]
    return s or "project"


async def _unique_slug(db: AsyncSession, base: str) -> str:
    candidate = base[:80]
    for _ in range(24):
        if not _SLUG_RE.match(candidate):
            candidate = _slugify(candidate) or "project"
        existing = await db.scalar(select(Project).where(Project.slug == candidate))
        if existing is None:
            return candidate
        suffix = uuid.uuid4().hex[:6]
        trimmed = base[: max(1, 80 - 7 - len(suffix))]
        candidate = f"{trimmed}-{suffix}"
    raise HTTPException(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not allocate a unique slug",
    )


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    q = (
        select(Project, ProjectMember.role)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user.id)
        .order_by(Project.updated_at.desc())
    )
    result = await db.execute(q)
    rows = list(result.all())

    project_ids = [p.id for p, _ in rows]
    items: list[ProjectOut] = []
    if project_ids:
        # Aggregate task counts
        task_counts = {}
        task_result = await db.execute(
            select(Task.project_id, func.count())
            .where(Task.project_id.in_(project_ids))
            .where(Task.status.not_in(["done", "cancelled"]))
            .group_by(Task.project_id)
        )
        for pid, cnt in task_result.all():
            task_counts[pid] = cnt

        # Aggregate ticket counts + oldest
        ticket_result = await db.execute(
            select(
                Ticket.project_id,
                func.count(),
                func.min(Ticket.created_at),
            )
            .where(Ticket.project_id.in_(project_ids))
            .where(Ticket.status.not_in(["closed", "resolved"]))
            .group_by(Ticket.project_id)
        )
        ticket_info: dict[uuid.UUID, tuple[int, datetime | None]] = {}
        for pid, cnt, oldest in ticket_result.all():
            ticket_info[pid] = (cnt, oldest)

        now_utc = datetime.now(timezone.utc)
        for p, role in rows:
            health = None
            open_tasks = task_counts.get(p.id, 0)
            tc = ticket_info.get(p.id, (0, None))
            open_tickets = tc[0]
            oldest_days = None
            if tc[1] is not None:
                oldest_days = (now_utc - tc[1]).days
            if open_tasks > 0 or open_tickets > 0:
                health = ProjectHealth(
                    open_tasks=open_tasks,
                    open_tickets=open_tickets,
                    oldest_open_ticket_days=oldest_days,
                )
            items.append(
                ProjectOut.model_validate(p).model_copy(
                    update={"membership_role": role, "health": health}
                )
            )
    return ProjectListResponse(items=items)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    base_slug = (body.slug.strip() if body.slug else _slugify(body.name)).strip()
    slug = await _unique_slug(db, base_slug)
    row = Project(
        name=body.name.strip(),
        slug=slug,
        description=body.description.strip() if body.description else None,
        owner_id=user.id,
        status="active",
        project_key=None,
    )
    db.add(row)
    await db.flush()
    db.add(
        ProjectMember(
            project_id=row.id,
            user_id=user.id,
            role=MemberRole.owner.value,
        )
    )
    await db.commit()
    await db.refresh(row)
    return ProjectOut.model_validate(row).model_copy(
        update={"membership_role": MemberRole.owner.value}
    )


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    return ProjectOut.model_validate(acc.project).model_copy(
        update={"membership_role": acc.role.value}
    )


@router.patch("/{project_id}", response_model=ProjectOut)
async def patch_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not can_edit_project_meta(acc.role):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only owners and maintainers can update project settings",
        )
    proj = acc.project
    if body.name is not None:
        proj.name = body.name.strip()
    if body.description is not None:
        v = body.description.strip()
        proj.description = v if v else None
    if body.status is not None:
        proj.status = body.status
    if body.project_key is not None:
        v = body.project_key.strip()
        proj.project_key = v if v else None
    await db.commit()
    await db.refresh(proj)
    return ProjectOut.model_validate(proj).model_copy(
        update={"membership_role": acc.role.value}
    )


def _member_out(m: ProjectMember) -> ProjectMemberOut:
    u = m.user
    return ProjectMemberOut(
        user_id=m.user_id,
        email=u.email,
        display_name=u.display_name,
        role=m.role,
        created_at=m.created_at,
    )


@router.get("/{project_id}/members", response_model=ProjectMemberListResponse)
async def list_members(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await require_project_access(db, user, project_id)
    result = await db.scalars(
        select(ProjectMember)
        .options(selectinload(ProjectMember.user))
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.created_at.asc())
    )
    rows = list(result.all())
    return ProjectMemberListResponse(items=[_member_out(m) for m in rows])


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    project_id: uuid.UUID,
    body: ProjectMemberCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not user.is_superuser and not can_manage_members(acc.role):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only owners and maintainers can add members",
        )
    new_role = parse_member_role(body.role)
    assert_can_assign_role(acc.role, new_role)
    email = body.email.strip().lower()
    target = await db.scalar(select(User).where(User.email == email))
    if target is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="No user with this email — they must have an account before they can be added",
        )
    dup = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target.id,
        )
    )
    if dup is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="User is already a member of this project",
        )
    row = ProjectMember(
        project_id=project_id,
        user_id=target.id,
        role=new_role.value,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    await db.refresh(row, attribute_names=["user"])
    row.user = target
    return _member_out(row)


@router.patch("/{project_id}/members/{member_user_id}", response_model=ProjectMemberOut)
async def patch_member(
    project_id: uuid.UUID,
    member_user_id: uuid.UUID,
    body: ProjectMemberPatch,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not user.is_superuser and not can_manage_members(acc.role):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only owners and maintainers can change member roles",
        )
    row = await db.scalar(
        select(ProjectMember)
        .options(selectinload(ProjectMember.user))
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member_user_id,
        )
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Member not found")
    old_role = parse_member_role(row.role)
    if old_role == MemberRole.owner and acc.role != MemberRole.owner:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only an owner can modify another owner",
        )
    new_role = parse_member_role(body.role)
    assert_can_assign_role(acc.role, new_role)
    if old_role == MemberRole.owner and new_role != MemberRole.owner:
        owners = await count_role_members(db, project_id, MemberRole.owner)
        if owners <= 1:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last owner — promote another owner first",
            )
    row.role = new_role.value
    await db.commit()
    await db.refresh(row)
    return _member_out(row)


@router.delete("/{project_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    project_id: uuid.UUID,
    member_user_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not user.is_superuser and not can_manage_members(acc.role):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only owners and maintainers can remove members",
        )
    row = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member_user_id,
        )
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Member not found")
    target_role = parse_member_role(row.role)
    if target_role == MemberRole.owner:
        if acc.role != MemberRole.owner:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Only an owner can remove an owner",
            )
        owners = await count_role_members(db, project_id, MemberRole.owner)
        if owners <= 1:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner",
            )
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
