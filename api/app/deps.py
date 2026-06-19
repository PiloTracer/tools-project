from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.models.client_contact import ClientContact
from app.models.user import User
from app.services.auth_local import decode_local_token
from app.services.oauth_userinfo import upsert_user_from_oauth_access_token

_http_bearer = HTTPBearer(auto_error=False)


async def get_current_user_local(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    settings = get_settings()
    if not settings.auth_local_enabled:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Local auth is disabled"
        )
    payload = decode_local_token(creds.credentials)
    if not payload:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        )
    try:
        user_uuid = uuid.UUID(uid)
    except ValueError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        )
    row = await db.scalar(select(User).where(User.id == user_uuid))
    if row is None or not row.is_active:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )
    return row


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    settings = get_settings()
    token = creds.credentials

    if settings.auth_local_enabled:
        payload = decode_local_token(token)
        if payload:
            uid = payload.get("sub")
            if not uid:
                raise HTTPException(
                    status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
                )
            try:
                user_uuid = uuid.UUID(uid)
            except ValueError:
                raise HTTPException(
                    status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
                )
            row = await db.scalar(select(User).where(User.id == user_uuid))
            if row is None or not row.is_active:
                raise HTTPException(
                    status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
                )
            return row

    if settings.auth_oauth_enabled:
        oauth_user = await upsert_user_from_oauth_access_token(db, token, settings)
        if oauth_user is not None and oauth_user.is_active:
            return oauth_user

    raise HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
    )


async def require_superuser(
    user: Annotated[User, Depends(get_current_user_local)],
) -> User:
    if not user.is_superuser:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return user


async def get_current_client_participant(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> tuple[User, ClientContact]:
    """Returns (user, client_contact) if the current user has a linked contact."""
    contact = await db.scalar(
        select(ClientContact).where(ClientContact.user_id == user.id)
    )
    if contact is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="User is not linked to any client contact",
        )
    return user, contact
