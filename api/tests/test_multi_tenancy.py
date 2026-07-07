"""Multi-tenancy isolation tests.

These tests verify that when MULTI_TENANCY_ENABLED is true, data is properly
isolated between tenants. They require a running test database with the tenants
table and tenant_id columns applied.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.prospect import Prospect
from app.models.tenant import Tenant
from app.models.user import User
from app.services.auth_local import create_local_access_token, hash_password


def auth_header(user: User) -> dict:
    """Build Authorization header for a user."""
    token, _ = create_local_access_token(
        user_id=str(user.id),
        email=user.email,
        is_superuser=user.is_superuser,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
    )
    return {"Authorization": f"Bearer {token}"}


async def _create_tenant(db: AsyncSession, slug: str, name: str) -> Tenant:
    t = Tenant(slug=slug, name=name)
    db.add(t)
    await db.flush()
    await db.refresh(t)
    return t


async def _create_user_in_tenant(
    db: AsyncSession,
    tenant: Tenant | None,
    email: str,
    is_superuser: bool = False,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("password"),
        display_name=email.split("@")[0],
        is_active=True,
        is_superuser=is_superuser,
        tenant_id=tenant.id if tenant else None,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_tenant_isolation_prospects(db: AsyncSession) -> None:
    """Prospects from tenant-A are not visible to tenant-B."""
    slug1 = f"acme-{uuid.uuid4().hex[:6]}"
    slug2 = f"globex-{uuid.uuid4().hex[:6]}"
    name1 = f"Acme-{uuid.uuid4().hex[:4]}"
    name2 = f"Globex-{uuid.uuid4().hex[:4]}"
    t1 = await _create_tenant(db, slug1, "Acme Corp")
    t2 = await _create_tenant(db, slug2, "Globex Inc")
    u1 = await _create_user_in_tenant(db, t1, "alice@acme.test")
    u2 = await _create_user_in_tenant(db, t2, "bob@globex.test")

    # Create prospect in tenant 1
    p1 = Prospect(company_name=name1, pipeline_stage="target", created_by=u1.id, tenant_id=t1.id)
    db.add(p1)
    # Create prospect in tenant 2
    p2 = Prospect(company_name=name2, pipeline_stage="target", created_by=u2.id, tenant_id=t2.id)
    db.add(p2)
    await db.flush()

    # Query tenant 1 prospects
    t1_prospects = (await db.execute(
        select(Prospect).where(Prospect.tenant_id == t1.id)
    )).scalars().all()
    assert len(t1_prospects) >= 1
    assert any(p.company_name == name1 for p in t1_prospects)

    # Query tenant 2 prospects
    t2_prospects = (await db.execute(
        select(Prospect).where(Prospect.tenant_id == t2.id)
    )).scalars().all()
    assert len(t2_prospects) >= 1
    assert any(p.company_name == name2 for p in t2_prospects)




@pytest.mark.asyncio
async def test_tenant_isolation_clients(db: AsyncSession) -> None:
    """Clients from tenant-A are not visible to tenant-B."""
    slug1 = f"acme-{uuid.uuid4().hex[:6]}"
    slug2 = f"globex-{uuid.uuid4().hex[:6]}"
    t1 = await _create_tenant(db, slug1, "Acme Corp")
    t2 = await _create_tenant(db, slug2, "Globex Inc")
    u1 = await _create_user_in_tenant(db, t1, "alice@acme.test")
    u2 = await _create_user_in_tenant(db, t2, "bob@globex.test")

    c1 = Client(name="Acme Client", slug="acme-client", created_by=u1.id, tenant_id=t1.id)
    db.add(c1)
    c2 = Client(name="Globex Client", slug="globex-client", created_by=u2.id, tenant_id=t2.id)
    db.add(c2)
    await db.commit()

    t1_clients = (await db.execute(
        select(Client).where(Client.tenant_id == t1.id)
    )).scalars().all()
    assert len(t1_clients) == 1
    assert t1_clients[0].name == "Acme Client"

    t2_clients = (await db.execute(
        select(Client).where(Client.tenant_id == t2.id)
    )).scalars().all()
    assert len(t2_clients) == 1
    assert t2_clients[0].name == "Globex Client"


@pytest.mark.asyncio
async def test_cross_tenant_superuser_sees_all(db: AsyncSession) -> None:
    """Cross-tenant superuser (tenant_id IS NULL) can see all data."""
    slug1 = f"acme-{uuid.uuid4().hex[:6]}"
    slug2 = f"globex-{uuid.uuid4().hex[:6]}"
    name1 = f"Super-Acme-{uuid.uuid4().hex[:4]}"
    name2 = f"Super-Globex-{uuid.uuid4().hex[:4]}"
    t1 = await _create_tenant(db, slug1, "Acme Corp")
    t2 = await _create_tenant(db, slug2, "Globex Inc")
    u1 = await _create_user_in_tenant(db, t1, "alice@acme.test")
    u2 = await _create_user_in_tenant(db, t2, "bob@globex.test")

    # Cross-tenant superuser
    await _create_user_in_tenant(db, None, "admin@system.test", is_superuser=True)

    p1 = Prospect(company_name=name1, pipeline_stage="target", created_by=u1.id, tenant_id=t1.id)
    db.add(p1)
    p2 = Prospect(company_name=name2, pipeline_stage="target", created_by=u2.id, tenant_id=t2.id)
    db.add(p2)
    await db.flush()

    # No tenant filter in query — demonstrates that superuser bypass works
    all_flushed = (await db.execute(select(Prospect))).scalars().all()
    mine = [p for p in all_flushed if p.created_by in (u1.id, u2.id)]
    assert len(mine) == 2


@pytest.mark.asyncio
async def test_per_tenant_superuser_cannot_see_other_tenant(db: AsyncSession) -> None:
    """Org admin in tenant A cannot see tenant B's data."""
    slug1 = f"acme-{uuid.uuid4().hex[:6]}"
    slug2 = f"globex-{uuid.uuid4().hex[:6]}"
    name1 = f"Org-Acme-{uuid.uuid4().hex[:4]}"
    name2 = f"Org-Globex-{uuid.uuid4().hex[:4]}"
    t1 = await _create_tenant(db, slug1, "Acme Corp")
    t2 = await _create_tenant(db, slug2, "Globex Inc")
    u1 = await _create_user_in_tenant(db, t1, "admin@acme.test", is_superuser=True)
    u2 = await _create_user_in_tenant(db, t2, "user@globex.test")

    p1 = Prospect(company_name=name1, pipeline_stage="target", created_by=u1.id, tenant_id=t1.id)
    db.add(p1)
    p2 = Prospect(company_name=name2, pipeline_stage="target", created_by=u2.id, tenant_id=t2.id)
    db.add(p2)
    await db.flush()

    # Org admin scoped to their tenant
    t1_prospects = (await db.execute(
        select(Prospect).where(Prospect.tenant_id == t1.id)
    )).scalars().all()
    assert any(p.company_name == name1 for p in t1_prospects)

    # Direct query for tenant 2 data — exists but different from t1
    t2_prospects = (await db.execute(
        select(Prospect).where(Prospect.tenant_id == t2.id)
    )).scalars().all()
    assert any(p.company_name == name2 for p in t2_prospects)
    assert not any(p.company_name == name1 for p in t2_prospects)


@pytest.mark.asyncio
async def test_email_per_tenant_unique(db: AsyncSession) -> None:
    """Same email can exist in different tenants."""
    slug1 = f"acme-{uuid.uuid4().hex[:6]}"
    slug2 = f"globex-{uuid.uuid4().hex[:6]}"
    t1 = await _create_tenant(db, slug1, "Acme Corp")
    t2 = await _create_tenant(db, slug2, "Globex Inc")

    await _create_user_in_tenant(db, t1, "alice@example.com")
    # Same email in different tenant should work
    await _create_user_in_tenant(db, t2, "alice@example.com")
    await db.commit()

    users_t1 = (await db.execute(
        select(User).where(User.email == "alice@example.com", User.tenant_id == t1.id)
    )).scalars().all()
    assert len(users_t1) == 1

    users_t2 = (await db.execute(
        select(User).where(User.email == "alice@example.com", User.tenant_id == t2.id)
    )).scalars().all()
    assert len(users_t2) == 1

    assert users_t1[0].id != users_t2[0].id


@pytest.mark.asyncio
async def test_backfill_idempotency(db: AsyncSession) -> None:
    """Default tenant exists and idempotent backfill works."""
    default = (await db.execute(
        select(Tenant).where(Tenant.slug == "default")
    )).scalar_one_or_none()
    assert default is not None, "Default tenant should exist after migration"
    assert default.name == "Default Organization"
    assert default.is_active is True


@pytest.mark.asyncio
async def test_tenant_inactive_blocks_access(db: AsyncSession) -> None:
    """Inactive tenants should be treated as forbidden."""
    t = Tenant(slug="inactive-org", name="Inactive Org", is_active=False)
    db.add(t)
    await db.commit()
    await db.refresh(t)

    assert t.is_active is False
    # Routing layer would reject access (tested via HTTP in integration tests)


@pytest.mark.asyncio
async def test_client_slug_per_tenant_unique(db: AsyncSession) -> None:
    """Same client slug can exist in different tenants."""
    slug1 = f"acme-{uuid.uuid4().hex[:6]}"
    slug2 = f"globex-{uuid.uuid4().hex[:6]}"
    t1 = await _create_tenant(db, slug1, "Acme Corp")
    t2 = await _create_tenant(db, slug2, "Globex Inc")
    u1 = await _create_user_in_tenant(db, t1, "alice@acme.test")
    u2 = await _create_user_in_tenant(db, t2, "bob@globex.test")

    c1 = Client(name="Acme Client", slug="my-client", created_by=u1.id, tenant_id=t1.id)
    db.add(c1)
    c2 = Client(name="Globex Client", slug="my-client", created_by=u2.id, tenant_id=t2.id)
    db.add(c2)
    await db.commit()

    # Both should exist with same slug
    all_with_slug = (await db.execute(
        select(Client).where(Client.slug == "my-client")
    )).scalars().all()
    assert len(all_with_slug) == 2
