"""OAuth sign-in tenant behaviour (multi-tenancy SPEC R5 / R9b / R9c).

OAuth resolution must never pick a user from a tenant the request did not select,
and must never auto-provision an account: ``users.tenant_id`` is NOT NULL for
non-superusers, so the previous auto-create path could not even be persisted.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.tenant import Tenant
from app.models.user import User
from app.services import oauth_userinfo
from app.services.tenancy import get_default_tenant
from tests.factories import create_user

_KNOWN_EMAIL = "oauth-idp-user@example.com"


class _FakeUserinfoResponse:
    status_code = 200

    def __init__(self, email: str) -> None:
        self._email = email

    def json(self) -> dict:
        return {"email": self._email, "name": "OAuth User"}


class _FakeAsyncClient:
    """Stands in for httpx.AsyncClient inside oauth_userinfo."""

    email = _KNOWN_EMAIL

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self) -> _FakeAsyncClient:
        return self

    async def __aexit__(self, *exc) -> bool:
        return False

    async def get(self, url: str = "", headers: dict | None = None) -> _FakeUserinfoResponse:
        _ = (url, headers)
        return _FakeUserinfoResponse(self.email)


class _Idp:
    def __init__(self, token: str, email: str) -> None:
        self.token = token
        self.email = email

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


def _configure_idp(monkeypatch: pytest.MonkeyPatch, *, multi_tenant: bool, email: str | None = None) -> _Idp:
    monkeypatch.setenv("AUTH_OAUTH_ENABLED", "true")
    monkeypatch.setenv("OAUTH_USER_INFO_ENDPOINT", "https://idp.example.com/userinfo")
    if multi_tenant:
        monkeypatch.setenv("MULTI_TENANCY_ENABLED", "true")
    resolved_email = email or f"idp-{uuid.uuid4().hex[:8]}@example.com"
    _FakeAsyncClient.email = resolved_email
    monkeypatch.setattr(oauth_userinfo, "httpx", SimpleNamespace(AsyncClient=_FakeAsyncClient))
    get_settings.cache_clear()
    return _Idp("opaque-oauth-access-token", resolved_email)


@pytest.fixture
def oauth_idp(monkeypatch: pytest.MonkeyPatch) -> _Idp:
    """Single-tenant deployment with a reachable (stubbed) OAuth IdP.

    Each test gets its own IdP email so the shared test database stays isolated.
    """
    idp = _configure_idp(monkeypatch, multi_tenant=False)
    yield idp
    get_settings.cache_clear()


@pytest.fixture
def oauth_idp_unknown_email(monkeypatch: pytest.MonkeyPatch) -> _Idp:
    """Single-tenant deployment whose IdP reports an unprovisioned email."""
    idp = _configure_idp(monkeypatch, multi_tenant=False)
    yield idp
    get_settings.cache_clear()


@pytest.fixture
def oauth_idp_multi_tenant(monkeypatch: pytest.MonkeyPatch) -> _Idp:
    """Multi-tenant deployment with a reachable (stubbed) OAuth IdP."""
    idp = _configure_idp(monkeypatch, multi_tenant=True)
    yield idp
    get_settings.cache_clear()


async def _tenant(db: AsyncSession, prefix: str) -> Tenant:
    tag = uuid.uuid4().hex[:8]
    row = Tenant(slug=f"{prefix}-{tag}", name=f"{prefix.title()} {tag}")
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def test_oauth_signin_rejects_unknown_email(
    client: AsyncClient, db: AsyncSession, oauth_idp_unknown_email: _Idp
) -> None:
    """R9c: unknown email → 401, no auto-provisioned (tenant-less) account."""
    idp = oauth_idp_unknown_email
    resp = await client.get("/v1/auth/me", headers=idp.headers)
    assert resp.status_code == 401, resp.text

    created = await db.scalar(select(User).where(User.email == idp.email))
    assert created is None


async def test_oauth_signin_resolves_existing_user_in_single_tenant_mode(
    client: AsyncClient, db: AsyncSession, oauth_idp: _Idp
) -> None:
    tenant = await get_default_tenant(db)
    assert tenant is not None
    user = await create_user(db, email=oauth_idp.email, is_superuser=True, tenant_id=tenant.id)
    await db.commit()

    resp = await client.get("/v1/auth/me", headers=oauth_idp.headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == str(user.id)
    assert resp.json()["auth"] == "oauth"

    # Tenant resolution keeps working for the OAuth-authenticated caller.
    listing = await client.get("/v1/clients", headers=oauth_idp.headers)
    assert listing.status_code == 200, listing.text


async def test_oauth_signin_multi_tenant_requires_tenant_context(
    client: AsyncClient, db: AsyncSession, oauth_idp_multi_tenant: _Idp
) -> None:
    """R9b: an email in several tenants needs a tenant context, else 300 choices."""
    first = await _tenant(db, "acme")
    second = await _tenant(db, "globex")
    await create_user(db, email=oauth_idp_multi_tenant.email, is_superuser=True, tenant_id=first.id)
    await create_user(db, email=oauth_idp_multi_tenant.email, is_superuser=True, tenant_id=second.id)
    await db.commit()

    resp = await client.get("/v1/auth/me", headers=oauth_idp_multi_tenant.headers)
    assert resp.status_code == 300, resp.text
    choices = resp.json()["detail"]["choices"]
    assert {c["tenant_slug"] for c in choices} == {first.slug, second.slug}

    resolved = await client.get(
        "/v1/auth/me",
        headers={**oauth_idp_multi_tenant.headers, "X-Tenant-Slug": second.slug},
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["tenant_id"] == str(second.id)


async def test_oauth_signin_multi_tenant_single_match_resolves_without_context(
    client: AsyncClient, db: AsyncSession, oauth_idp_multi_tenant: _Idp
) -> None:
    """R9b: a single tenant match resolves even when the request names no tenant."""
    tenant = await _tenant(db, "solo")
    user = await create_user(
        db, email=oauth_idp_multi_tenant.email, is_superuser=True, tenant_id=tenant.id
    )
    await db.commit()

    resp = await client.get("/v1/auth/me", headers=oauth_idp_multi_tenant.headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == str(user.id)
    assert resp.json()["tenant_id"] == str(tenant.id)


async def test_oauth_signin_multi_tenant_scopes_lookup_to_selected_tenant(
    client: AsyncClient, db: AsyncSession, oauth_idp_multi_tenant: _Idp
) -> None:
    idp = oauth_idp_multi_tenant
    own = await _tenant(db, "owner")
    other = await _tenant(db, "stranger")
    user = await create_user(db, email=idp.email, is_superuser=True, tenant_id=own.id)
    await db.commit()

    matching = await client.get(
        "/v1/auth/me", headers={**idp.headers, "X-Tenant-Slug": own.slug}
    )
    assert matching.status_code == 200, matching.text
    assert matching.json()["id"] == str(user.id)
    assert matching.json()["tenant_id"] == str(own.id)

    foreign = await client.get(
        "/v1/auth/me", headers={**idp.headers, "X-Tenant-Slug": other.slug}
    )
    assert foreign.status_code == 401, foreign.text
