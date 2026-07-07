"""Test helpers for creating users, projects, clients, and auth tokens."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.prospect import Prospect
from app.models.tenant import Tenant
from app.models.user import User
from app.services.auth_local import create_local_access_token, hash_password
from app.services.project_access import MemberRole


async def _default_tenant_id(db: AsyncSession) -> uuid.UUID:
    tenant = await db.scalar(select(Tenant).where(Tenant.slug == "default"))
    if tenant is None:
        tenant = Tenant(slug="default", name="Default Organization")
        db.add(tenant)
        await db.flush()
        await db.refresh(tenant)
    return tenant.id


async def create_user(
    db: AsyncSession,
    *,
    email: str = "user@example.com",
    password: str = "password",
    display_name: str = "Test User",
    is_superuser: bool = False,
    tenant_id: uuid.UUID | None = None,
) -> User:
    if tenant_id is None:
        tenant_id = await _default_tenant_id(db)
    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name,
        is_active=True,
        is_superuser=is_superuser,
        tenant_id=tenant_id,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


def auth_header(user: User) -> dict[str, str]:
    token, _expires = create_local_access_token(
        user_id=str(user.id),
        email=user.email,
        is_superuser=user.is_superuser,
    )
    return {"Authorization": f"Bearer {token}"}


async def create_project(
    db: AsyncSession,
    *,
    name: str = "Test Project",
    slug: str = "test-project",
    owner_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
) -> Project:
    if tenant_id is None:
        tenant_id = await _default_tenant_id(db)
    project = Project(name=name, slug=slug, owner_id=owner_id, tenant_id=tenant_id)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def add_member(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    role: MemberRole = MemberRole.contributor,
) -> ProjectMember:
    member = ProjectMember(project_id=project_id, user_id=user_id, role=role.value)
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return member


async def create_client(
    db: AsyncSession,
    *,
    name: str = "Test Client",
    slug: str = "test-client",
    created_by: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
) -> Client:
    if tenant_id is None:
        tenant_id = await _default_tenant_id(db)
    client = Client(name=name, slug=slug, created_by=created_by, tenant_id=tenant_id)
    db.add(client)
    await db.flush()
    await db.refresh(client)
    return client


async def create_client_contact(
    db: AsyncSession,
    *,
    client_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
    email: str = "contact@example.com",
    name: str = "Test Contact",
    role: str = "contact",
    tenant_id: uuid.UUID | None = None,
) -> ClientContact:
    if tenant_id is None:
        tenant_id = await _default_tenant_id(db)
    contact = ClientContact(
        client_id=client_id,
        user_id=user_id,
        email=email,
        name=name,
        role=role,
        tenant_id=tenant_id,
    )
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    return contact


async def create_prospect(
    db: AsyncSession,
    *,
    company_name: str = "Test Prospect",
    created_by: uuid.UUID,
    pipeline_stage: str = "target",
    tenant_id: uuid.UUID | None = None,
) -> Prospect:
    if tenant_id is None:
        tenant_id = await _default_tenant_id(db)
    prospect = Prospect(
        company_name=company_name,
        created_by=created_by,
        pipeline_stage=pipeline_stage,
        tenant_id=tenant_id,
    )
    db.add(prospect)
    await db.flush()
    await db.refresh(prospect)
    return prospect
