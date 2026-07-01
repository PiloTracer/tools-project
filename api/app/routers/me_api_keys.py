from __future__ import annotations

import hashlib
import secrets
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.user_api_key import UserApiKey
from app.schemas import UserApiKeyCreate, UserApiKeyListResponse, UserApiKeyOut, UserApiKeySecretOut

router = APIRouter(prefix="/v1/me/keys", tags=["me"])

_PREFIX = "tools_project_"


def _hash_key(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode()).hexdigest()


def _generate_key() -> tuple[str, str, str]:
    plaintext = _PREFIX + secrets.token_urlsafe(32)
    return plaintext, _hash_key(plaintext), plaintext[:8]


@router.get("", response_model=UserApiKeyListResponse)
async def list_api_keys(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (
        await db.execute(
            select(UserApiKey)
            .where(UserApiKey.user_id == user.id)
            .order_by(UserApiKey.created_at.desc())
        )
    ).scalars().all()

    return UserApiKeyListResponse(
        items=[UserApiKeyOut.model_validate(r) for r in rows]
    )


@router.post("", response_model=UserApiKeySecretOut, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: UserApiKeyCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    plaintext, key_hash, key_prefix = _generate_key()

    api_key = UserApiKey(
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        label=body.label.strip() if body.label else None,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    out = UserApiKeySecretOut.model_validate(api_key)
    out.plaintext = plaintext
    return out


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.scalar(
        select(UserApiKey).where(
            UserApiKey.id == key_id,
            UserApiKey.user_id == user.id,
        )
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="API key not found")

    await db.delete(row)
    await db.commit()
