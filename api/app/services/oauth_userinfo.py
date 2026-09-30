from __future__ import annotations

import logging
import uuid
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.tenant import Tenant
from app.models.user import User

log = logging.getLogger(__name__)


class OAuthTenantAmbiguousError(Exception):
    """The userinfo email matches more than one tenant and none was selected (R9b)."""

    def __init__(self, choices: list[tuple[str, str]]) -> None:
        super().__init__("OAuth email matches multiple tenants")
        self.choices = choices

def _validate_userinfo_url(url: str, settings: Settings) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(
            f"OAuth userinfo URL must use HTTPS scheme, got '{parsed.scheme}'"
        )
    allowed = settings.oauth_allowed_userinfo_hosts
    if allowed:
        hosts = frozenset(h.strip().lower() for h in allowed.split(",") if h.strip())
        if hosts and parsed.hostname not in hosts:
            raise ValueError(
                f"OAuth userinfo host '{parsed.hostname}' is not in allowed list: "
                f"{', '.join(sorted(hosts))}"
            )
    return url


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
    tenant_id: uuid.UUID | None = None,
) -> User | None:
    """Resolve the user behind an OAuth access token.

    ``tenant_id`` is the tenant selected by the request (subdomain /
    ``X-Tenant-Slug``): it scopes the email lookup when multi-tenancy is on,
    because ``users.email`` is unique per tenant (R5). New accounts are never
    created — provisioning is admin-only (R9c). Raises ``OAuthTenantAmbiguousError``
    when the email exists in several tenants and the request selected none (R9b).
    """
    if not settings.oauth_user_info_endpoint:
        log.warning("OAuth user resolution skipped: oauth_user_info_endpoint unset")
        return None
    url = _validate_userinfo_url(str(settings.oauth_user_info_endpoint).strip(), settings)
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
    # Tenant-scoped email lookup: with per-tenant emails (R5) the same address can
    # exist in several tenants, so never pick a row from a tenant the request did
    # not select. Tenant-NULL rows are cross-tenant superusers (R4a) and stay
    # reachable from any tenant context.
    stmt = select(User).where(User.email == email)
    if settings.multi_tenancy_enabled and tenant_id is not None:
        stmt = stmt.where(or_(User.tenant_id == tenant_id, User.tenant_id.is_(None)))
    stmt = stmt.order_by(User.tenant_id.is_(None).asc())
    matches = list((await db.scalars(stmt)).all())
    if matches:
        if settings.multi_tenancy_enabled and tenant_id is None:
            tenant_ids = {m.tenant_id for m in matches if m.tenant_id is not None}
            if len(tenant_ids) > 1:
                # R9b: ambiguous without a tenant context — let the caller answer 300.
                raise OAuthTenantAmbiguousError(await _tenant_choices(db, tenant_ids))
        row = matches[0]
        if display_name and row.display_name != display_name:
            row.display_name = display_name
            await db.commit()
            await db.refresh(row)
        return row
    # SPEC R9c: an OAuth sign-in for an unknown email is rejected — accounts are
    # provisioned by an admin (users.tenant_id is NOT NULL for non-superusers, so
    # there is also no tenant to auto-provision into).
    log.info("OAuth sign-in rejected: no account for email=%s (SPEC R9c)", email)
    return None


async def _tenant_choices(
    db: AsyncSession, tenant_ids: set[uuid.UUID]
) -> list[tuple[str, str]]:
    """(slug, name) pairs for the tenants an ambiguous email belongs to."""
    rows = (
        await db.scalars(
            select(Tenant).where(Tenant.id.in_(tenant_ids)).order_by(Tenant.name.asc())
        )
    ).all()
    return [(t.slug, t.name) for t in rows]
