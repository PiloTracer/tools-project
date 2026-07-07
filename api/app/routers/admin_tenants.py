from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user_local
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas import TenantCreate, TenantOut, TenantUpdate

router = APIRouter(prefix="/v1/admin/tenants", tags=["admin-tenants"])


@router.get("", response_model=list[TenantOut])
async def list_tenants(
    admin: Annotated[User, Depends(get_current_user_local)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    if not admin.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

    # Cross-tenant superuser sees all; per-tenant admin sees only own tenant
    if admin.tenant_id is not None:
        tenant = await db.get(Tenant, admin.tenant_id)
        if tenant is None:
            return []
        return [TenantOut.model_validate(tenant)]

    rows = list((await db.scalars(select(Tenant).order_by(Tenant.name.asc()))).all())
    return [TenantOut.model_validate(r) for r in rows]


@router.post("", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: TenantCreate,
    admin: Annotated[User, Depends(get_current_user_local)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not admin.is_superuser or admin.tenant_id is not None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only cross-tenant superusers can create tenants",
        )
    slug = body.slug.strip().lower()
    existing = await db.scalar(select(Tenant).where(Tenant.slug == slug))
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Tenant slug already exists")
    tenant = Tenant(
        slug=slug,
        name=body.name.strip(),
        settings=body.settings or {},
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return TenantOut.model_validate(tenant)


@router.patch("/{tenant_id}", response_model=TenantOut)
async def update_tenant(
    tenant_id: uuid.UUID,
    body: TenantUpdate,
    admin: Annotated[User, Depends(get_current_user_local)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not admin.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    # Cross-tenant superuser can edit any; per-tenant admin only own
    if admin.tenant_id is not None and tenant.id != admin.tenant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot modify another tenant")

    if body.name is not None:
        tenant.name = body.name.strip()
    if body.settings is not None:
        tenant.settings = {**tenant.settings, **body.settings}
    if body.is_active is not None:
        tenant.is_active = body.is_active

    await db.commit()
    await db.refresh(tenant)
    return TenantOut.model_validate(tenant)
