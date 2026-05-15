from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas import LocalLoginRequest, MeResponse, TokenResponse
from app.services.auth_local import create_local_access_token, verify_password, decode_local_token

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.get("/config")
def auth_config():
    s = get_settings()
    return {"local_enabled": s.auth_local_enabled, "oauth_enabled": s.auth_oauth_enabled}


@router.post("/local/login", response_model=TokenResponse)
async def local_login(
    body: LocalLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    s = get_settings()
    if not s.auth_local_enabled:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Local authentication is disabled for this deployment",
        )
    email = body.email.strip().lower()
    user = await db.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active or not user.password_hash:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token, expires_in = create_local_access_token(
        user_id=str(user.id),
        email=user.email,
        is_superuser=user.is_superuser,
        settings=s,
    )
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=MeResponse)
async def auth_me(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
):
    auth_kind = "oauth"
    if get_settings().auth_local_enabled:
        auth_header = (request.headers.get("authorization") or "").strip()
        token = ""
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
        if token and decode_local_token(token):
            auth_kind = "local"
    return MeResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_superuser=user.is_superuser,
        auth=auth_kind,
    )
