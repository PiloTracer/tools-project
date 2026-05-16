from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.component import Component
from app.models.user import User
from app.schemas import (
    ComponentCreate,
    ComponentListResponse,
    ComponentOut,
    ComponentPatch,
)
from app.services.project_access import MemberRole, require_project_access, require_role

router = APIRouter(
    prefix="/v1/projects/{project_id}/components",
    tags=["components"],
)
detail_router = APIRouter(prefix="/v1/components", tags=["components"])


@router.get("", response_model=ComponentListResponse)
async def list_components(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await require_project_access(db, user, project_id)
    result = await db.scalars(
        select(Component)
        .where(Component.project_id == project_id)
        .order_by(Component.name.asc())
    )
    rows = list(result.all())
    return ComponentListResponse(items=[ComponentOut.model_validate(r) for r in rows])


@router.post("", response_model=ComponentOut, status_code=status.HTTP_201_CREATED)
async def create_component(
    project_id: uuid.UUID,
    body: ComponentCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    require_role(acc, MemberRole.contributor)
    key_val = body.key.strip() if body.key else None
    row = Component(
        project_id=project_id,
        key=key_val,
        name=body.name.strip(),
        description=body.description.strip() if body.description else None,
        lead_user_id=body.lead_user_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ComponentOut.model_validate(row)


@detail_router.patch("/{component_id}", response_model=ComponentOut)
async def patch_component(
    component_id: uuid.UUID,
    body: ComponentPatch,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Component, component_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Component not found")
    acc = await require_project_access(db, user, row.project_id)
    require_role(acc, MemberRole.contributor)
    if body.name is not None:
        row.name = body.name.strip()
    if body.description is not None:
        v = body.description.strip()
        row.description = v if v else None
    if body.key is not None:
        v = body.key.strip()
        row.key = v if v else None
    if body.lead_user_id is not None:
        row.lead_user_id = body.lead_user_id
    await db.commit()
    await db.refresh(row)
    return ComponentOut.model_validate(row)


@detail_router.delete(
    "/{component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_component(
    component_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Component, component_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Component not found")
    acc = await require_project_access(db, user, row.project_id)
    require_role(acc, MemberRole.maintainer)
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
