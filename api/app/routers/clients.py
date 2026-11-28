from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_tenant, get_current_user, require_superuser
from app.models.client import Client
from app.models.project import Project
from app.models.project_client import ProjectClient
from app.models.user import User
from app.schemas import (
    ClientCreate,
    ClientListResponse,
    ClientOut,
    ClientProjectListResponse,
    ClientProjectOut,
    ClientUpdate,
    slugify,
)
from app.services.crm_audit import as_text, clean_custom_fields, record_changes
from app.services.crm_profile import CLIENT_PROFILE_KEYS, apply_profile_update, profile_kwargs
from app.services.tenancy import resolve_write_tenant_id
from app.services.webhook_dispatcher import dispatch_event

router = APIRouter(prefix="/v1/clients", tags=["clients"])


async def _unique_slug(db: AsyncSession, base: str, tenant_id: uuid.UUID) -> str:
    candidate = slugify(base)
    for _ in range(24):
        existing = await db.scalar(
            select(Client).where(Client.slug == candidate, Client.tenant_id == tenant_id)
        )
        if existing is None:
            return candidate
        suffix = uuid.uuid4().hex[:6]
        candidate = f"{slugify(base)[:72]}-{suffix}"
    raise HTTPException(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not allocate a unique slug",
    )


@router.get("", response_model=ClientListResponse)
async def list_clients(
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    tenant = await get_current_tenant(request, db)
    tenant_id = tenant.id if tenant else None
    is_cross_tenant_superuser = user.tenant_id is None
    base = select(func.count()).select_from(Client)
    if tenant_id is not None and not is_cross_tenant_superuser:
        base = base.where(Client.tenant_id == tenant_id)
    total = (await db.scalar(base)) or 0
    q = select(Client)
    if tenant_id is not None and not is_cross_tenant_superuser:
        q = q.where(Client.tenant_id == tenant_id)
    q = q.order_by(Client.created_at.desc()).offset(offset).limit(limit)
    result = await db.scalars(q)
    rows = list(result.all())
    return ClientListResponse(
        items=[ClientOut.model_validate(r) for r in rows],
        total=total,
        has_more=(offset + len(rows)) < total,
    )

@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(
    body: ClientCreate,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    tenant = await get_current_tenant(request, db)
    effective_tenant_id = resolve_write_tenant_id(user, tenant)
    slug = await _unique_slug(db, body.name, effective_tenant_id)
    row = Client(
        name=body.name.strip(),
        slug=slug,
        industry=body.industry.strip() if body.industry else None,
        notes=body.notes.strip() if body.notes else None,
        created_by=user.id,
        tenant_id=effective_tenant_id,
        custom_fields=clean_custom_fields(body.custom_fields),
        **profile_kwargs(body, CLIENT_PROFILE_KEYS),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    dispatch_event(
        "client.created",
        {"client_id": str(row.id), "name": row.name},
        tenant_id=row.tenant_id,
    )
    return ClientOut.model_validate(row)


@router.get("/{client_id}", response_model=ClientOut)
async def get_client(
    client_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    tenant = await get_current_tenant(request, db)
    row = await db.get(Client, client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    if tenant is not None and user.tenant_id is not None and row.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientOut.model_validate(row)


@router.get("/{client_id}/projects", response_model=ClientProjectListResponse)
async def list_client_projects(
    client_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """Projects linked to this client — the operational slice of the customer workspace."""
    tenant = await get_current_tenant(request, db)
    row = await db.get(Client, client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    if tenant is not None and user.tenant_id is not None and row.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Client not found")
    q = (
        select(Project)
        .join(ProjectClient, ProjectClient.project_id == Project.id)
        .where(ProjectClient.client_id == client_id)
        .order_by(Project.created_at.desc())
    )
    if user.tenant_id is not None:
        q = q.where(Project.tenant_id == user.tenant_id)
    projects = list((await db.scalars(q)).all())
    return ClientProjectListResponse(
        items=[
            ClientProjectOut(
                id=p.id,
                name=p.name,
                slug=p.slug,
                status=p.status,
                template_key=p.template_key,
            )
            for p in projects
        ]
    )


@router.patch("/{client_id}", response_model=ClientOut)
async def update_client(
    client_id: uuid.UUID,
    body: ClientUpdate,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    tenant = await get_current_tenant(request, db)
    row = await db.get(Client, client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    if tenant is not None and user.tenant_id is not None and row.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Client not found")
    tracked = ("name", "industry", "zone", "source", "service", "email", "custom_fields")
    before = {key: as_text(getattr(row, key)) for key in tracked}
    if body.name is not None:
        row.name = body.name.strip()
    if body.industry is not None:
        row.industry = body.industry.strip() if body.industry else None
    if body.notes is not None:
        row.notes = body.notes.strip() if body.notes else None
    apply_profile_update(row, body, CLIENT_PROFILE_KEYS)
    if "custom_fields" in body.model_fields_set:
        row.custom_fields = clean_custom_fields(body.custom_fields)
    record_changes(
        db,
        tenant_id=row.tenant_id,
        entity_type="client",
        entity_id=row.id,
        actor_id=user.id,
        before=before,
        after={key: as_text(getattr(row, key)) for key in tracked},
    )
    await db.commit()
    await db.refresh(row)
    return ClientOut.model_validate(row)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    tenant = await get_current_tenant(request, db)
    row = await db.get(Client, client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    if tenant is not None and user.tenant_id is not None and row.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Client not found")
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
