from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas import (
    AdminAddToProjectRequest,
    AdminChangeProjectRoleRequest,
    AdminLinkableContactOut,
    AdminLinkContactRequest,
    AdminUserCreate,
    AdminUserListResponse,
    AdminUserOut,
    AdminUserUpdate,
    UserClientContactOut,
    UserMembershipOut,
)
from app.services.auth_local import hash_password
from app.services.project_access import parse_member_role

router = APIRouter(prefix="/v1/admin/users", tags=["admin-users"])


def _tenant_mismatch_response() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")


async def _enrich_users(
    db: AsyncSession,
    users: list[User],
) -> list[AdminUserOut]:
    """Load memberships and client contacts for one or more User rows."""
    user_ids = [u.id for u in users]
    memberships_map: dict[uuid.UUID, list[UserMembershipOut]] = {}
    contacts_map: dict[uuid.UUID, list[UserClientContactOut]] = {}

    if user_ids:
        mem_rows = await db.execute(
            select(ProjectMember, Project.name)
            .join(Project, ProjectMember.project_id == Project.id)
            .where(ProjectMember.user_id.in_(user_ids))
            .order_by(Project.name.asc()),
        )
        for pm, project_name in mem_rows.all():
            memberships_map.setdefault(pm.user_id, []).append(
                UserMembershipOut(
                    project_id=pm.project_id,
                    project_name=project_name,
                    role=pm.role,
                ),
            )

        contact_rows = await db.execute(
            select(ClientContact, Client.name)
            .join(Client, ClientContact.client_id == Client.id)
            .where(ClientContact.user_id.in_(user_ids))
            .order_by(Client.name.asc()),
        )
        for cc, client_name in contact_rows.all():
            contacts_map.setdefault(cc.user_id, []).append(
                UserClientContactOut(
                    id=cc.id,
                    client_id=cc.client_id,
                    client_name=client_name,
                    role=cc.role,
                    email=cc.email,
                    name=cc.name,
                ),
            )

    out = []
    for u in users:
        obj = AdminUserOut.model_validate(u)
        obj.memberships = memberships_map.get(u.id, [])
        obj.client_contacts = contacts_map.get(u.id, [])
        out.append(obj)
    return out


@router.get("", response_model=AdminUserListResponse)
async def list_users(
    request: Request,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None, min_length=1, max_length=200),
):
    if not admin.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    is_cross_tenant_superuser = admin.tenant_id is None
    stmt = select(User)
    if not is_cross_tenant_superuser:
        stmt = stmt.where(User.tenant_id == admin.tenant_id)
    stmt = stmt.order_by(User.created_at.asc())
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            User.email.ilike(term) | User.display_name.ilike(term),
        )
    result = await db.scalars(stmt)
    rows = list(result.all())
    items = await _enrich_users(db, rows)
    return AdminUserListResponse(items=items)


@router.post("", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    body: AdminUserCreate,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not admin.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    is_cross_tenant_superuser = admin.tenant_id is None

    # Resolve target tenant_id
    target_tenant_id: uuid.UUID | None
    if is_cross_tenant_superuser:
        if body.tenant_slug:
            tenant_row = await db.scalar(select(Tenant).where(Tenant.slug == body.tenant_slug))
            if tenant_row is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Tenant not found")
            target_tenant_id = tenant_row.id
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="tenant_slug is required for cross-tenant superuser")
    else:
        target_tenant_id = admin.tenant_id

    email = body.email.strip().lower()
    # Per-tenant email uniqueness: check within target tenant
    dup_stmt = select(User).where(User.email == email)
    if target_tenant_id is not None:
        dup_stmt = dup_stmt.where(User.tenant_id == target_tenant_id)
    dup = await db.scalar(dup_stmt)
    if dup is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="User with this email already exists"
        )
    user = User(
        email=email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        is_active=True,
        is_superuser=body.is_superuser,
        tenant_id=target_tenant_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    items = await _enrich_users(db, [user])
    return items[0]


@router.patch("/{user_id}", response_model=AdminUserOut)
async def update_user(
    request: Request,
    user_id: uuid.UUID,
    body: AdminUserUpdate,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not admin.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    # Multi-tenancy: org admins can only update users in their tenant
    if admin.tenant_id is not None and user.tenant_id != admin.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    if body.password is not None:
        user.password_hash = hash_password(body.password)
    if body.display_name is not None:
        user.display_name = body.display_name
    if body.is_active is not None:
        if user.id == admin.id and not body.is_active:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate yourself",
            )
        user.is_active = body.is_active
    if body.is_superuser is not None:
        if user.id == admin.id and not body.is_superuser:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove superuser from yourself",
            )
        user.is_superuser = body.is_superuser

    await db.commit()
    await db.refresh(user)
    items = await _enrich_users(db, [user])
    return items[0]


# --- Client contact linking ---


@router.get("/{user_id}/linkable-contacts", response_model=list[AdminLinkableContactOut])
async def list_linkable_contacts(
    request: Request,
    user_id: uuid.UUID,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None, min_length=1, max_length=200),
):
    """Search client contacts that can be linked to this user.

    Returns contacts that have no linked user OR are already linked to this user.
    """
    if not admin.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    if admin.tenant_id is not None and user.tenant_id != admin.tenant_id:
        raise _tenant_mismatch_response()

    stmt = select(ClientContact, Client.name).join(
        Client, ClientContact.client_id == Client.id,
    ).where(
        (ClientContact.user_id.is_(None)) | (ClientContact.user_id == user_id),
    )
    if admin.tenant_id is not None:
        stmt = stmt.where(ClientContact.tenant_id == admin.tenant_id)
    stmt = stmt.order_by(Client.name.asc(), ClientContact.name.asc())

    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            ClientContact.name.ilike(term)
            | ClientContact.email.ilike(term)
            | Client.name.ilike(term),
        )

    result = await db.execute(stmt)
    rows = result.all()
    return [
        AdminLinkableContactOut(
            id=cc.id,
            client_id=cc.client_id,
            client_name=client_name,
            name=cc.name,
            email=cc.email,
            role=cc.role,
        )
        for cc, client_name in rows
    ]


@router.post("/{user_id}/link-contact", response_model=AdminUserOut)
async def link_contact(
    request: Request,
    user_id: uuid.UUID,
    body: AdminLinkContactRequest,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link a user to a client contact (1-to-1).

    If the user was previously linked to a different contact, that link is removed.
    If the contact was previously linked to a different user, that link is removed.
    """
    if not admin.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    if admin.tenant_id is not None and user.tenant_id != admin.tenant_id:
        raise _tenant_mismatch_response()

    contact = await db.get(ClientContact, body.client_contact_id)
    if contact is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Client contact not found",
        )
    if admin.tenant_id is not None and contact.tenant_id != admin.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client contact not found")

    # Clear any existing link from this user to another contact
    old_contact = await db.scalar(
        select(ClientContact).where(
            ClientContact.user_id == user_id,
            ClientContact.id != contact.id,
        ),
    )
    if old_contact is not None:
        old_contact.user_id = None

    # Clear any existing link from this contact to another user
    if contact.user_id is not None and contact.user_id != user_id:
        # The contact was linked to a different user — that user's link is gone
        pass  # setting contact.user_id below handles this

    contact.user_id = user_id
    await db.commit()
    await db.refresh(contact)
    items = await _enrich_users(db, [user])
    return items[0]


@router.delete("/{user_id}/link-contact", response_model=AdminUserOut)
async def unlink_contact(
    request: Request,
    user_id: uuid.UUID,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove the user-to-contact link for this user."""
    if not admin.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    if admin.tenant_id is not None and user.tenant_id != admin.tenant_id:
        raise _tenant_mismatch_response()

    contact = await db.scalar(
        select(ClientContact).where(ClientContact.user_id == user_id),
    )
    if contact is not None:
        contact.user_id = None
        await db.commit()

    items = await _enrich_users(db, [user])
    return items[0]


# --- Project member management ---


@router.post("/{user_id}/add-to-project", response_model=AdminUserOut)
async def add_user_to_project(
    request: Request,
    user_id: uuid.UUID,
    body: AdminAddToProjectRequest,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a user to a project with the given role."""
    if not admin.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    if admin.tenant_id is not None and user.tenant_id != admin.tenant_id:
        raise _tenant_mismatch_response()

    project = await db.get(Project, body.project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")
    if admin.tenant_id is not None and project.tenant_id != admin.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")

    role = parse_member_role(body.role)

    dup = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == body.project_id,
            ProjectMember.user_id == user_id,
        ),
    )
    if dup is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="User is already a member of this project",
        )

    pm = ProjectMember(
        project_id=body.project_id,
        user_id=user_id,
        role=role.value,
    )
    db.add(pm)
    await db.commit()
    items = await _enrich_users(db, [user])
    return items[0]


@router.patch("/{user_id}/project-membership/{project_id}", response_model=AdminUserOut)
async def change_project_role(
    request: Request,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    body: AdminChangeProjectRoleRequest,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change a user's role in a project."""
    if not admin.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    if admin.tenant_id is not None and user.tenant_id != admin.tenant_id:
        raise _tenant_mismatch_response()

    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")
    if admin.tenant_id is not None and project.tenant_id != admin.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")

    pm = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        ),
    )
    if pm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Member not found")

    new_role = parse_member_role(body.role)
    pm.role = new_role.value
    await db.commit()
    items = await _enrich_users(db, [user])
    return items[0]


@router.delete("/{user_id}/project-membership/{project_id}", response_model=AdminUserOut)
async def remove_from_project(
    request: Request,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a user from a project."""
    if not admin.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    if admin.tenant_id is not None and user.tenant_id != admin.tenant_id:
        raise _tenant_mismatch_response()

    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")
    if admin.tenant_id is not None and project.tenant_id != admin.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")

    pm = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        ),
    )
    if pm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Member not found")

    await db.delete(pm)
    await db.commit()
    items = await _enrich_users(db, [user])
    return items[0]
