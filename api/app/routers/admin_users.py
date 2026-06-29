from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_superuser
from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas import (
    AdminUserCreate,
    AdminUserListResponse,
    AdminUserOut,
    AdminUserUpdate,
    UserClientContactOut,
    UserMembershipOut,
)
from app.services.auth_local import hash_password

router = APIRouter(prefix="/v1/admin/users", tags=["admin-users"])


@router.get("", response_model=AdminUserListResponse)
async def list_users(
    _: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str | None = Query(default=None, min_length=1, max_length=200),
):
    stmt = select(User).order_by(User.created_at.asc())
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            User.email.ilike(term) | User.display_name.ilike(term),
        )
    result = await db.scalars(stmt)
    rows = list(result.all())

    user_ids = [u.id for u in rows]
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
                    client_id=cc.client_id,
                    client_name=client_name,
                    role=cc.role,
                    email=cc.email,
                    name=cc.name,
                ),
            )

    out = []
    for u in rows:
        obj = AdminUserOut.model_validate(u)
        obj.memberships = memberships_map.get(u.id, [])
        obj.client_contacts = contacts_map.get(u.id, [])
        out.append(obj)

    return AdminUserListResponse(items=out)


@router.post("", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: AdminUserCreate,
    _: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    email = body.email.strip().lower()
    dup = await db.scalar(select(User).where(User.email == email))
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
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return AdminUserOut.model_validate(user)


@router.patch("/{user_id}", response_model=AdminUserOut)
async def update_user(
    user_id: uuid.UUID,
    body: AdminUserUpdate,
    admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    if body.password is not None:
        user.password_hash = hash_password(body.password)
    if body.display_name is not None:
        user.display_name = body.display_name
    if body.is_active is not None:
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
    return AdminUserOut.model_validate(user)
