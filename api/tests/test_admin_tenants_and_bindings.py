"""Admin tenant create + user/project tenant binding."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.tenant import Tenant
from app.models.user import User
from app.services.auth_local import create_local_access_token, hash_password


def _jwt(user: User) -> dict[str, str]:
    token, _ = create_local_access_token(
        user_id=str(user.id),
        email=user.email,
        is_superuser=user.is_superuser,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
    )
    return {"Authorization": f"Bearer {token}"}


async def _cross_tenant_admin(db: AsyncSession) -> User:
    user = User(
        email=f"xt-{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("password-1234"),
        display_name="Cross Admin",
        is_active=True,
        is_superuser=True,
        tenant_id=None,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_tenant_and_bind_user(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _cross_tenant_admin(db)
    await db.commit()
    tag = uuid.uuid4().hex[:8]
    slug = f"org-{tag}"

    created = await client.post(
        "/v1/admin/tenants",
        json={"slug": slug, "name": f"Org {tag}"},
        headers=_jwt(admin),
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["slug"] == slug
    assert body["name"] == f"Org {tag}"

    user_resp = await client.post(
        "/v1/admin/users",
        json={
            "email": f"member-{tag}@example.com",
            "password": "password-1234",
            "display_name": f"Member {tag}",
            "tenant_slug": slug,
        },
        headers=_jwt(admin),
    )
    assert user_resp.status_code == 201, user_resp.text
    user_body = user_resp.json()
    assert user_body["tenant_slug"] == slug
    assert user_body["tenant_name"] == f"Org {tag}"

    row = await db.scalar(select(User).where(User.email == f"member-{tag}@example.com"))
    assert row is not None
    tenant = await db.scalar(select(Tenant).where(Tenant.slug == slug))
    assert tenant is not None
    assert row.tenant_id == tenant.id

    # Reassign via PATCH
    other = await client.post(
        "/v1/admin/tenants",
        json={"slug": f"other-{tag}", "name": f"Other {tag}"},
        headers=_jwt(admin),
    )
    assert other.status_code == 201, other.text

    patched = await client.patch(
        f"/v1/admin/users/{row.id}",
        json={"tenant_slug": f"other-{tag}"},
        headers=_jwt(admin),
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["tenant_slug"] == f"other-{tag}"


@pytest.mark.asyncio
async def test_project_create_and_move_tenant(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _cross_tenant_admin(db)
    tag = uuid.uuid4().hex[:8]
    t1 = Tenant(slug=f"alpha-{tag}", name=f"Alpha {tag}")
    t2 = Tenant(slug=f"beta-{tag}", name=f"Beta {tag}")
    db.add_all([t1, t2])
    await db.commit()
    await db.refresh(t1)
    await db.refresh(t2)

    created = await client.post(
        "/v1/projects",
        json={"name": f"Alpha Project {tag}", "tenant_slug": t1.slug},
        headers=_jwt(admin),
    )
    assert created.status_code == 201, created.text
    assert created.json()["tenant_slug"] == t1.slug
    project_id = created.json()["id"]

    moved = await client.patch(
        f"/v1/projects/{project_id}",
        json={"tenant_slug": t2.slug},
        headers=_jwt(admin),
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["tenant_slug"] == t2.slug

    row = await db.get(Project, uuid.UUID(project_id))
    assert row is not None
    assert row.tenant_id == t2.id


@pytest.mark.asyncio
async def test_add_to_project_rejects_cross_tenant_membership(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _cross_tenant_admin(db)
    tag = uuid.uuid4().hex[:8]
    t1 = Tenant(slug=f"one-{tag}", name=f"One {tag}")
    t2 = Tenant(slug=f"two-{tag}", name=f"Two {tag}")
    db.add_all([t1, t2])
    await db.flush()
    u1 = User(
        email=f"u1-{tag}@example.com",
        password_hash=hash_password("password-1234"),
        is_active=True,
        is_superuser=False,
        tenant_id=t1.id,
    )
    db.add(u1)
    await db.commit()
    await db.refresh(t1)
    await db.refresh(t2)
    await db.refresh(u1)

    proj = await client.post(
        "/v1/projects",
        json={"name": f"Two Project {tag}", "tenant_slug": t2.slug},
        headers=_jwt(admin),
    )
    assert proj.status_code == 201, proj.text

    bad = await client.post(
        f"/v1/admin/users/{u1.id}/add-to-project",
        json={"project_id": proj.json()["id"], "role": "contributor"},
        headers=_jwt(admin),
    )
    assert bad.status_code == 400, bad.text
    assert "different tenants" in bad.json()["detail"]
