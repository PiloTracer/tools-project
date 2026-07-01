from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
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
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_superuser:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return user


async def require_agent_or_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    x_api_key: Annotated[str | None, Header(alias="X-Api-Key")] = None,
) -> User:
    """Accept a personal API key, server-wide agent key, or Bearer JWT.

    Auth resolution (first match wins):
      1. X-Api-Key matches Settings.agent_api_key → synthetic agent superuser
      2. X-Api-Key matches a user_api_keys row (SHA-256) → authenticated user
      3. Bearer JWT → normal user session
      4. None → 401
    """
    import hashlib

    settings = get_settings()

    if x_api_key:
        plaintext = x_api_key.strip()

        # Server-wide shared agent key (local convenience)
        if settings.agent_api_key and plaintext == settings.agent_api_key.strip():
            return User(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, "agent.localhost"),
                email="agent@localhost",
                display_name="Agent",
                is_superuser=True,
                is_active=True,
            )

        # Personal API key — look up by SHA-256 hash
        from app.models.user_api_key import UserApiKey

        from sqlalchemy.orm import joinedload

        key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
        api_key_row = await db.scalar(
            select(UserApiKey)
            .where(UserApiKey.key_hash == key_hash)
            .options(joinedload(UserApiKey.user))
        )
        if api_key_row is not None and api_key_row.user.is_active:
            api_key_row.last_used_at = func.now()
            await db.commit()
            return api_key_row.user

    # Fall back to Bearer JWT
    return await get_current_user(creds, db)


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
