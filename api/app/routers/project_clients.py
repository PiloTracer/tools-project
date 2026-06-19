from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.deps import get_current_user
from app.models.client import Client
from app.models.project_client import ProjectClient
from app.models.user import User
from app.schemas import (
    ProjectClientLinkRequest,
    ProjectClientListResponse,
    ProjectClientOut,
)
from app.services.project_access import MemberRole, require_project_access, require_role

router = APIRouter(
    prefix="/v1/projects/{project_id}/clients",
    tags=["project_clients"],
)


@router.get("", response_model=ProjectClientListResponse)
async def list_linked_clients(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    require_role(acc, MemberRole.maintainer)
    result = await db.scalars(
        select(ProjectClient)
        .options(selectinload(ProjectClient.client))
        .where(ProjectClient.project_id == project_id)
        .order_by(ProjectClient.created_at.desc())
    )
    rows = list(result.all())
    return ProjectClientListResponse(
        items=[
            ProjectClientOut(
                id=r.id,
                project_id=r.project_id,
                client_id=r.client_id,
                client_name=r.client.name,
                client_slug=r.client.slug,
                created_at=r.created_at,
            )
            for r in rows
        ]
    )


@router.post("", response_model=ProjectClientOut, status_code=status.HTTP_201_CREATED)
async def link_client(
    project_id: uuid.UUID,
    body: ProjectClientLinkRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    require_role(acc, MemberRole.maintainer)
    client = await db.get(Client, body.client_id)
    if client is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client not found")
    existing = await db.scalar(
        select(ProjectClient).where(
            ProjectClient.project_id == project_id,
            ProjectClient.client_id == body.client_id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Client is already linked to this project",
        )
    row = ProjectClient(
        project_id=project_id,
        client_id=body.client_id,
        created_by=user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ProjectClientOut(
        id=row.id,
        project_id=row.project_id,
        client_id=row.client_id,
        client_name=client.name,
        client_slug=client.slug,
        created_at=row.created_at,
    )


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_client(
    project_id: uuid.UUID,
    client_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    require_role(acc, MemberRole.maintainer)
    row = await db.scalar(
        select(ProjectClient).where(
            ProjectClient.project_id == project_id,
            ProjectClient.client_id == client_id,
        )
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client link not found")
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
