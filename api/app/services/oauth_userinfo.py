from __future__ import annotations

import logging
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.user import User

log = logging.getLogger(__name__)


def _pick_email(info: dict[str, Any]) -> str | None:
    raw = info.get("email")
    if isinstance(raw, str) and "@" in raw:
        return raw.strip().lower()
    preferred = info.get("preferred_username")
    if isinstance(preferred, str) and "@" in preferred:
        return preferred.strip().lower()
    return None


def _pick_display_name(info: dict[str, Any]) -> str | None:
    for key in ("name", "display_name", "preferred_username"):
        v = info.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()[:200]
    return None


async def upsert_user_from_oauth_access_token(
    db: AsyncSession,
    access_token: str,
    settings: Settings,
) -> User | None:
    if not settings.oauth_user_info_endpoint:
        log.warning("OAuth user resolution skipped: oauth_user_info_endpoint unset")
        return None
    url = str(settings.oauth_user_info_endpoint).strip()
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.RequestError as exc:
            log.debug("OAuth userinfo request failed: %s", exc)
            return None
    if resp.status_code != 200:
        return None
    try:
        info = resp.json()
    except ValueError:
        return None
    if not isinstance(info, dict):
        return None
    email = _pick_email(info)
    if not email:
        return None
    display_name = _pick_display_name(info)
    row = await db.scalar(select(User).where(User.email == email))
    if row is not None:
        if display_name and row.display_name != display_name:
            row.display_name = display_name
            await db.commit()
            await db.refresh(row)
        return row
    user = User(
        email=email,
        password_hash=None,
        display_name=display_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
