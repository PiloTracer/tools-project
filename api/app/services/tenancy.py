"""Tenant resolution helpers shared by deps, bootstrap, and routers.

A tenant-bound user (``users.tenant_id`` set) is always scoped to that org for
reads and writes. ``MULTI_TENANCY_ENABLED`` only turns on multi-org login UX
(subdomain / ``X-Tenant-Slug`` / 300-choice). Cross-tenant superusers
(``tenant_id IS NULL``) with the flag off stamp new rows into the ``default``
tenant created by ``sql/schema_backfill.sql`` (SPEC R4c).
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.user import User

DEFAULT_TENANT_SLUG = "default"
DEFAULT_TENANT_NAME = "Default Organization"

# Tenant-scoped columns are NOT NULL, so a write with no resolvable tenant is a
# deployment defect (schema backfill never ran) rather than a client error.
NO_TENANT_CONTEXT_DETAIL = (
    "No tenant context for this write: the single-tenant 'default' tenant row is "
    "missing (apply sql/schema_backfill.sql) and no tenant was selected via "
    "subdomain or X-Tenant-Slug"
)


async def get_default_tenant(db: AsyncSession) -> Tenant | None:
    """Return the deployment's ``default`` tenant row, or None when absent."""
    return await db.scalar(select(Tenant).where(Tenant.slug == DEFAULT_TENANT_SLUG))


async def ensure_default_tenant(db: AsyncSession) -> Tenant:
    """Return the ``default`` tenant row, creating it when missing (idempotent)."""
    tenant = await get_default_tenant(db)
    if tenant is None:
        tenant = Tenant(slug=DEFAULT_TENANT_SLUG, name=DEFAULT_TENANT_NAME)
        db.add(tenant)
        await db.flush()
        await db.refresh(tenant)
    return tenant


def resolve_write_tenant_id(user: User, tenant: Tenant | None) -> uuid.UUID:
    """Tenant id to stamp on a newly created tenant-scoped row.

    - Tenant-bound user → their own tenant.
    - Cross-tenant superuser (``tenant_id IS NULL``) → the tenant resolved for
      this request: the subdomain / ``X-Tenant-Slug`` target when multi-tenancy
      is on, or the deployment's ``default`` tenant when it is off.
    """
    if user.tenant_id is not None:
        return user.tenant_id
    if tenant is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail=NO_TENANT_CONTEXT_DETAIL
        )
    return tenant.id
