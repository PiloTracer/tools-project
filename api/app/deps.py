from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.models.user import User
from app.services.auth_local import decode_local_token

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


async def require_superuser(
    user: Annotated[User, Depends(get_current_user_local)],
) -> User:
    if not user.is_superuser:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return user
