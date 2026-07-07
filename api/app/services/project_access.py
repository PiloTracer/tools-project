"""Project membership and coarse RBAC helpers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_contact import ClientContact
from app.models.project import Project
from app.models.project_client_access import ProjectClientAccess
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
        ) from None


@dataclass(frozen=True)
class ProjectAccess:
    project: Project
    role: MemberRole
    client_access: ProjectClientAccess | None = None


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

    # Internal team membership takes precedence.
    member_row = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    if member_row is not None:
        try:
            role = MemberRole(member_row.role)
        except ValueError:
            role = MemberRole.viewer
        return ProjectAccess(proj, role)

    # Fall back to client participant access.
    contact = await db.scalar(
        select(ClientContact).where(ClientContact.user_id == user.id)
    )
    if contact is not None:
        client_acc = await db.scalar(
            select(ProjectClientAccess).where(
                ProjectClientAccess.project_id == project_id,
                ProjectClientAccess.client_contact_id == contact.id,
            )
        )
        if client_acc is not None:
            # Client participants are treated as viewers for internal RBAC checks;
            # actual permissions are in client_access.
            return ProjectAccess(proj, MemberRole.viewer, client_access=client_acc)

    return None


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


def is_client_participant(acc: ProjectAccess) -> bool:
    return acc.client_access is not None


async def client_company_user_ids(
    db: AsyncSession, acc: ProjectAccess
) -> list[uuid.UUID]:
    """User ids of every contact in the signed-in client participant's company.

    Includes the signed-in contact. Use only when ``is_client_participant(acc)`` is True.
    Implements SPEC FR-5: client participants see tasks/tickets assigned to them or their
    client company contacts (not just themselves).
    """
    ca = acc.client_access
    if ca is None:
        return []
    contact = await db.get(ClientContact, ca.client_contact_id)
    if contact is None:
        return []
    rows = await db.scalars(
        select(ClientContact.user_id).where(
            ClientContact.client_id == contact.client_id,
            ClientContact.user_id.is_not(None),
        )
    )
    return [u for u in rows.all() if u is not None]


def can_view_tasks(acc: ProjectAccess) -> bool:
    if acc.client_access is not None:
        return acc.client_access.can_view_tasks
    return True


def can_view_tickets(acc: ProjectAccess) -> bool:
    if acc.client_access is not None:
        return acc.client_access.can_view_tickets
    return True


def can_create_tasks(acc: ProjectAccess) -> bool:
    if acc.client_access is not None:
        return acc.client_access.can_create_tasks
    return can_mutate_tasks(acc.role)


def can_comment_on_project(acc: ProjectAccess) -> bool:
    """Who can post activity / comments in a project."""
    if acc.client_access is not None:
        return acc.client_access.role in {"contribute", "decision_maker"}
    return can_mutate_tasks(acc.role)


def can_edit_tasks(acc: ProjectAccess) -> bool:
    """Client participants can create tasks (if granted) but not edit existing ones."""
    if acc.client_access is not None:
        return False
    return can_mutate_tasks(acc.role)


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


async def require_client_project_access(
    db: AsyncSession,
    user: User,
    project_id: uuid.UUID,
) -> ProjectClientAccess:
    """Check if the user (via their linked client contact) has access to the project.
    Returns the access record or raises 403."""
    contact = await db.scalar(
        select(ClientContact).where(ClientContact.user_id == user.id)
    )
    if contact is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="User is not linked to a client contact",
        )
    acc = await db.scalar(
        select(ProjectClientAccess).where(
            ProjectClientAccess.project_id == project_id,
            ProjectClientAccess.client_contact_id == contact.id,
        )
    )
    if acc is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Client contact does not have access to this project",
        )
    return acc
