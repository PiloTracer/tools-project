"""Tenant resolution across deployment modes.

Covers the single-tenant deployment mode (``MULTI_TENANCY_ENABLED=false``) where
every tenant-scoped row lives in the ``default`` tenant and the bootstrap
superuser has ``tenant_id IS NULL``, plus the multi-tenant mode where the request
tenant comes from subdomain → JWT → ``X-Tenant-Slug``.

Regression context: the create endpoints used to answer
``400 tenant_id or tenant_slug is required for cross-tenant superuser`` for the
bootstrapped admin in single-tenant mode, because ``get_current_tenant`` returned
None instead of the ``default`` tenant (SPEC multi-tenancy §Feature flag).
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.project import Project
from app.models.prospect import Prospect
from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_api_key import UserApiKey
from app.models.webhook_subscription import WebhookSubscription
from app.services.auth_local import create_local_access_token, hash_password
from app.services.tenancy import DEFAULT_TENANT_SLUG, get_default_tenant


async def _default_tenant_id(db: AsyncSession) -> uuid.UUID:
    tenant = await get_default_tenant(db)
    assert tenant is not None, "the `default` tenant must exist in every deployment"
    return tenant.id


async def _cross_tenant_superuser(db: AsyncSession) -> User:
    """The bootstrap-admin shape: is_superuser, tenant_id IS NULL."""
    tag = uuid.uuid4().hex[:8]
    user = User(
        email=f"cross-tenant-{tag}@example.com",
        password_hash=hash_password("password"),
        display_name=f"Cross Tenant {tag}",
        is_active=True,
        is_superuser=True,
        tenant_id=None,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _tenant(db: AsyncSession, prefix: str) -> Tenant:
    tag = uuid.uuid4().hex[:8]
    row = Tenant(slug=f"{prefix}-{tag}", name=f"{prefix.title()} {tag}")
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def _user_in(db: AsyncSession, tenant: Tenant | None, *, is_superuser: bool = True) -> User:
    tag = uuid.uuid4().hex[:8]
    user = User(
        email=f"user-{tag}@example.com",
        password_hash=hash_password("password"),
        display_name=f"User {tag}",
        is_active=True,
        is_superuser=is_superuser,
        tenant_id=tenant.id if tenant else None,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


def _jwt(user: User) -> dict[str, str]:
    token, _ = create_local_access_token(
        user_id=str(user.id),
        email=user.email,
        is_superuser=user.is_superuser,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
    )
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------
# Single-tenant mode (MULTI_TENANCY_ENABLED=false)
# --------------------------------------------------------------------------


async def test_bootstrap_superuser_can_create_project(client: AsyncClient, db: AsyncSession) -> None:
    """The reported production blocker: 400 instead of 201."""
    admin = await _cross_tenant_superuser(db)
    await db.commit()

    resp = await client.post(
        "/v1/projects",
        json={"name": f"Single Tenant Project {uuid.uuid4().hex[:6]}"},
        headers=_jwt(admin),
    )
    assert resp.status_code == 201, resp.text

    project = await db.get(Project, uuid.UUID(resp.json()["id"]))
    assert project is not None
    assert project.tenant_id == await _default_tenant_id(db)
    assert project.owner_id == admin.id


async def test_bootstrap_superuser_can_create_client_and_prospect(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _cross_tenant_superuser(db)
    await db.commit()
    default_tenant_id = await _default_tenant_id(db)
    tag = uuid.uuid4().hex[:6]

    client_resp = await client.post(
        "/v1/clients",
        json={"name": f"Single Tenant Client {tag}"},
        headers=_jwt(admin),
    )
    assert client_resp.status_code == 201, client_resp.text
    client_row = await db.get(Client, uuid.UUID(client_resp.json()["id"]))
    assert client_row is not None
    assert client_row.tenant_id == default_tenant_id

    prospect_resp = await client.post(
        "/v1/prospects",
        json={"company_name": f"Single Tenant Prospect {tag}", "pipeline_stage": "target"},
        headers=_jwt(admin),
    )
    assert prospect_resp.status_code == 201, prospect_resp.text
    prospect_row = await db.get(Prospect, uuid.UUID(prospect_resp.json()["id"]))
    assert prospect_row is not None
    assert prospect_row.tenant_id == default_tenant_id


async def test_bootstrap_superuser_can_create_user_without_tenant_slug(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _cross_tenant_superuser(db)
    await db.commit()
    default_tenant_id = await _default_tenant_id(db)
    tag = uuid.uuid4().hex[:8]

    resp = await client.post(
        "/v1/admin/users",
        json={
            "email": f"created-{tag}@example.com",
            "password": "password-1234",
            "display_name": f"Created {tag}",
            "is_superuser": False,
        },
        headers=_jwt(admin),
    )
    assert resp.status_code == 201, resp.text

    created = await db.scalar(select(User).where(User.email == f"created-{tag}@example.com"))
    assert created is not None
    assert created.tenant_id == default_tenant_id


async def test_bootstrap_superuser_can_create_webhook_and_api_key(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _cross_tenant_superuser(db)
    await db.commit()
    default_tenant_id = await _default_tenant_id(db)

    hook_resp = await client.post(
        "/v1/admin/webhook-subscriptions",
        json={
            "url": "https://example.test/hooks/tools-project",
            "events": ["client.created"],
            "label": f"hook-{uuid.uuid4().hex[:6]}",
        },
        headers=_jwt(admin),
    )
    assert hook_resp.status_code == 201, hook_resp.text
    hook = await db.get(WebhookSubscription, uuid.UUID(hook_resp.json()["id"]))
    assert hook is not None
    assert hook.tenant_id == default_tenant_id

    key_resp = await client.post(
        "/v1/me/keys",
        json={"label": f"agent-{uuid.uuid4().hex[:6]}"},
        headers=_jwt(admin),
    )
    assert key_resp.status_code == 201, key_resp.text
    key = await db.get(UserApiKey, uuid.UUID(key_resp.json()["id"]))
    assert key is not None
    assert key.tenant_id == default_tenant_id


async def test_tenant_bound_user_keeps_own_tenant(client: AsyncClient, db: AsyncSession) -> None:
    """Single-tenant mode must not change behaviour for tenant-bound users."""
    tenant_id = await _default_tenant_id(db)
    user = await _user_in(db, await get_default_tenant(db), is_superuser=False)
    await db.commit()

    resp = await client.post(
        "/v1/projects",
        json={"name": f"Bound User Project {uuid.uuid4().hex[:6]}"},
        headers=_jwt(user),
    )
    assert resp.status_code == 201, resp.text
    project = await db.get(Project, uuid.UUID(resp.json()["id"]))
    assert project is not None
    assert project.tenant_id == tenant_id


async def test_missing_default_tenant_fails_loudly(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A deployment without the `default` row must not write NULL tenant_id."""

    async def _no_default_tenant(_db):
        return None

    monkeypatch.setattr("app.deps.get_default_tenant", _no_default_tenant)
    admin = await _cross_tenant_superuser(db)
    await db.commit()

    resp = await client.post(
        "/v1/projects",
        json={"name": f"No Default Tenant {uuid.uuid4().hex[:6]}"},
        headers=_jwt(admin),
    )
    assert resp.status_code == 500, resp.text
    assert "No tenant context for this write" in resp.json()["detail"]


async def test_single_tenant_default_tenant_is_resolved(
    client: AsyncClient, db: AsyncSession
) -> None:
    """`GET /v1/auth/config` stays flag-driven; the default tenant is bootstrapped."""
    tenant = await get_default_tenant(db)
    assert tenant is not None
    assert tenant.slug == DEFAULT_TENANT_SLUG
    config = await client.get("/v1/auth/config")
    assert config.status_code == 200
    assert config.json()["multi_tenant"] is False


# --------------------------------------------------------------------------
# Multi-tenant mode (MULTI_TENANCY_ENABLED=true)
# --------------------------------------------------------------------------


@pytest.mark.usefixtures("multi_tenant_on")
async def test_user_jwt_resolves_own_tenant(client: AsyncClient, db: AsyncSession) -> None:
    """A tenant-bound user needs no subdomain / header — the JWT carries the tenant."""
    tenant = await _tenant(db, "acme")
    user = await _user_in(db, tenant)
    row = Client(
        name=f"Acme Client {uuid.uuid4().hex[:6]}",
        slug=f"acme-client-{uuid.uuid4().hex[:6]}",
        created_by=user.id,
        tenant_id=tenant.id,
    )
    db.add(row)
    await db.commit()

    resp = await client.get("/v1/clients", headers=_jwt(user))
    assert resp.status_code == 200, resp.text
    assert str(row.id) in [item["id"] for item in resp.json()["items"]]


@pytest.mark.usefixtures("multi_tenant_on")
async def test_foreign_tenant_slug_does_not_widen_access(
    client: AsyncClient, db: AsyncSession
) -> None:
    """X-Tenant-Slug selects a tenant; authorization still comes from the JWT (R2b)."""
    own = await _tenant(db, "own")
    other = await _tenant(db, "other")
    user = await _user_in(db, own)
    stranger = Client(
        name=f"Other Client {uuid.uuid4().hex[:6]}",
        slug=f"other-client-{uuid.uuid4().hex[:6]}",
        created_by=user.id,
        tenant_id=other.id,
    )
    db.add(stranger)
    await db.commit()

    foreign = await client.get("/v1/clients", headers={**_jwt(user), "X-Tenant-Slug": other.slug})
    assert foreign.status_code == 403, foreign.text

    matching = await client.get("/v1/clients", headers={**_jwt(user), "X-Tenant-Slug": own.slug})
    assert matching.status_code == 200, matching.text
    assert str(stranger.id) not in [item["id"] for item in matching.json()["items"]]


@pytest.mark.usefixtures("multi_tenant_on")
async def test_cross_tenant_superuser_writes_into_selected_tenant(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _cross_tenant_superuser(db)
    tenant = await _tenant(db, "target")
    await db.commit()

    without_context = await client.post(
        "/v1/projects",
        json={"name": f"No Context {uuid.uuid4().hex[:6]}"},
        headers=_jwt(admin),
    )
    assert without_context.status_code == 401, without_context.text

    selected = await client.post(
        "/v1/projects",
        json={"name": f"Target Tenant Project {uuid.uuid4().hex[:6]}"},
        headers={**_jwt(admin), "X-Tenant-Slug": tenant.slug},
    )
    assert selected.status_code == 201, selected.text
    project = await db.get(Project, uuid.UUID(selected.json()["id"]))
    assert project is not None
    assert project.tenant_id == tenant.id


@pytest.mark.usefixtures("multi_tenant_on")
async def test_cross_tenant_superuser_needs_tenant_slug_for_users(
    client: AsyncClient, db: AsyncSession
) -> None:
    """Multi-tenant mode keeps the explicit target-tenant requirement (R13a)."""
    admin = await _cross_tenant_superuser(db)
    tenant = await _tenant(db, "members")
    await db.commit()
    tag = uuid.uuid4().hex[:8]

    missing = await client.post(
        "/v1/admin/users",
        json={
            "email": f"no-slug-{tag}@example.com",
            "password": "password-1234",
            "display_name": f"No Slug {tag}",
        },
        headers=_jwt(admin),
    )
    assert missing.status_code == 400, missing.text
    assert "tenant_slug" in missing.json()["detail"]

    created = await client.post(
        "/v1/admin/users",
        json={
            "email": f"with-slug-{tag}@example.com",
            "password": "password-1234",
            "display_name": f"With Slug {tag}",
            "tenant_slug": tenant.slug,
        },
        headers=_jwt(admin),
    )
    assert created.status_code == 201, created.text
    row = await db.scalar(select(User).where(User.email == f"with-slug-{tag}@example.com"))
    assert row is not None
    assert row.tenant_id == tenant.id
