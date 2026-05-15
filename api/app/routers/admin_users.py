from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_superuser
from app.models.user import User
from app.schemas import (
    AdminUserCreate,
    AdminUserListResponse,
    AdminUserOut,
    AdminUserUpdate,
)
from app.services.auth_local import hash_password

router = APIRouter(prefix="/v1/admin/users", tags=["admin-users"])


@router.get("", response_model=AdminUserListResponse)
async def list_users(
    _: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.scalars(
        select(User).order_by(User.created_at.asc()),
    )
    rows = list(result.all())
    return AdminUserListResponse(items=[AdminUserOut.model_validate(r) for r in rows])


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
