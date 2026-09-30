"""Local login tenant context (multi-tenancy SPEC R5 / R9b / R13a).

Per-tenant emails (R5) mean one address can belong to several accounts, so login
must never pick one arbitrarily: it either uses the requested tenant, or answers
``300 Multiple Choices`` with the tenant list.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.user import User
from app.services.auth_local import hash_password

PASSWORD = "password-1234"


async def _tenant(db: AsyncSession, prefix: str) -> Tenant:
    tag = uuid.uuid4().hex[:8]
    row = Tenant(slug=f"{prefix}-{tag}", name=f"{prefix.title()} {tag}")
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def _user(
    db: AsyncSession,
    *,
    email: str,
    tenant_id: uuid.UUID | None,
    is_superuser: bool = False,
    password: str = PASSWORD,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=email.split("@")[0][:200],
        is_active=True,
        is_superuser=is_superuser,
        tenant_id=tenant_id,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest.mark.usefixtures("multi_tenant_on")
async def test_cross_tenant_superuser_logs_in_with_tenant_context(
    client: AsyncClient, db: AsyncSession
) -> None:
    """The bootstrap superuser (tenant_id NULL) can log in on a tenant subdomain/slug."""
    tenant = await _tenant(db, "acme")
    email = f"cross-tenant-{uuid.uuid4().hex[:8]}@example.com"
    await _user(db, email=email, tenant_id=None, is_superuser=True)
    await db.commit()

    resp = await client.post(
        "/v1/auth/local/login",
        json={"email": email, "password": PASSWORD, "tenant_slug": tenant.slug},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["tenant_id"] is None  # still a cross-tenant superuser
    assert body["tenant_slug"] is None
    assert body["request_tenant_slug"] == tenant.slug


@pytest.mark.usefixtures("multi_tenant_on")
async def test_ambiguous_email_returns_300_with_choices(
    client: AsyncClient, db: AsyncSession
) -> None:
    """Same email + password in two tenants, no tenant context → 300 choices (R9b)."""
    first = await _tenant(db, "alpha")
    second = await _tenant(db, "beta")
    email = f"duplicate-{uuid.uuid4().hex[:8]}@example.com"
    await _user(db, email=email, tenant_id=first.id)
    await _user(db, email=email, tenant_id=second.id)
    await db.commit()

    ambiguous = await client.post(
        "/v1/auth/local/login", json={"email": email, "password": PASSWORD}
    )
    assert ambiguous.status_code == 300, ambiguous.text
    body = ambiguous.json()
    assert body["access_token"] == ""
    assert {c["tenant_slug"] for c in body["choices"]} == {first.slug, second.slug}

    # Naming the tenant resolves the ambiguity.
    selected = await client.post(
        "/v1/auth/local/login",
        json={"email": email, "password": PASSWORD, "tenant_slug": second.slug},
    )
    assert selected.status_code == 200, selected.text
    assert selected.json()["tenant_slug"] == second.slug


@pytest.mark.usefixtures("multi_tenant_on")
async def test_wrong_tenant_slug_rejects_tenant_bound_user(
    client: AsyncClient, db: AsyncSession
) -> None:
    """A tenant-bound account cannot sign in through another tenant's context."""
    own = await _tenant(db, "own")
    other = await _tenant(db, "other")
    email = f"bound-{uuid.uuid4().hex[:8]}@example.com"
    await _user(db, email=email, tenant_id=own.id)
    await db.commit()

    denied = await client.post(
        "/v1/auth/local/login",
        json={"email": email, "password": PASSWORD, "tenant_slug": other.slug},
    )
    assert denied.status_code == 401, denied.text

    allowed = await client.post(
        "/v1/auth/local/login",
        json={"email": email, "password": PASSWORD, "tenant_slug": own.slug},
    )
    assert allowed.status_code == 200, allowed.text
    assert allowed.json()["tenant_slug"] == own.slug


async def test_single_tenant_login_returns_tenant_slug(
    client: AsyncClient, db: AsyncSession
) -> None:
    """Single-tenant mode: no tenant context needed, binding still echoed."""
    email = f"single-{uuid.uuid4().hex[:8]}@example.com"
    user = await _user(db, email=email, tenant_id=None, is_superuser=True)
    await db.commit()

    resp = await client.post(
        "/v1/auth/local/login", json={"email": email, "password": PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["tenant_id"] is None
    assert body["request_tenant_slug"] is None
    assert jwt.get_unverified_claims(body["access_token"])["sub"] == str(user.id)
