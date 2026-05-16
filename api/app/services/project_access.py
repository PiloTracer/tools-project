"""Project membership and coarse RBAC helpers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User


class MemberRole(str, Enum):
    owner = "owner"
    maintainer = "maintainer"
    contributor = "contributor"
    viewer = "viewer"


ROLE_RANK: dict[MemberRole, int] = {
    MemberRole.viewer: 0,
    MemberRole.contributor: 1,
    MemberRole.maintainer: 2,
    MemberRole.owner: 3,
}


def parse_member_role(value: str) -> MemberRole:
    try:
        return MemberRole(value.strip().lower())
    except ValueError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Invalid role (use owner, maintainer, contributor, viewer)",
        )


@dataclass(frozen=True)
class ProjectAccess:
    project: Project
    role: MemberRole


async def resolve_project_access(
    db: AsyncSession,
    user: User,
    project_id: uuid.UUID,
) -> ProjectAccess | None:
    proj = await db.get(Project, project_id)
    if proj is None:
        return None
    if user.is_superuser:
        return ProjectAccess(proj, MemberRole.owner)
    row = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    if row is None:
        return None
    try:
        role = MemberRole(row.role)
    except ValueError:
        role = MemberRole.viewer
    return ProjectAccess(proj, role)


async def require_project_access(
    db: AsyncSession,
    user: User,
    project_id: uuid.UUID,
) -> ProjectAccess:
    acc = await resolve_project_access(db, user, project_id)
    if acc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")
    return acc


def require_role(acc: ProjectAccess, minimum: MemberRole) -> None:
    if ROLE_RANK[acc.role] < ROLE_RANK[minimum]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Insufficient project permissions"
        )


def can_manage_members(role: MemberRole) -> bool:
    return role in (MemberRole.owner, MemberRole.maintainer)


def can_edit_project_meta(role: MemberRole) -> bool:
    return role in (MemberRole.owner, MemberRole.maintainer)


def can_mutate_tasks(role: MemberRole) -> bool:
    return role in (
        MemberRole.owner,
        MemberRole.maintainer,
        MemberRole.contributor,
    )


def assert_can_assign_role(inviter: MemberRole, target: MemberRole) -> None:
    if target == MemberRole.owner and inviter != MemberRole.owner:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only a project owner can assign the owner role",
        )
    if ROLE_RANK[target] > ROLE_RANK[inviter]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Cannot assign a role higher than your own",
        )


async def count_role_members(
    db: AsyncSession, project_id: uuid.UUID, role: MemberRole
) -> int:
    return int(
        await db.scalar(
            select(func.count())
            .select_from(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.role == role.value,
            )
        )
        or 0
    )
