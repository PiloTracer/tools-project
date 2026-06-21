from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.deps import get_current_user
from app.models.client_contact import ClientContact
from app.models.project_client import ProjectClient
from app.models.project_client_access import ProjectClientAccess, CLIENT_ROLES
from app.models.user import User
from app.schemas import (
    ClientAccessCreate,
    ClientAccessListResponse,
    ClientAccessOut,
    ClientAccessUpdate,
    ProjectClientContactListResponse,
    ProjectClientContactOut,
)
from app.services.project_access import MemberRole, require_project_access, require_role

router = APIRouter(
    prefix="/v1/projects/{project_id}/client-access",
    tags=["client_access"],
)


@router.get("", response_model=ClientAccessListResponse)
async def list_client_access(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    require_role(acc, MemberRole.maintainer)
    result = await db.scalars(
        select(ProjectClientAccess)
        .options(
            selectinload(ProjectClientAccess.client_contact).selectinload(
                ClientContact.client
            )
        )
        .where(ProjectClientAccess.project_id == project_id)
        .order_by(ProjectClientAccess.created_at.desc())
    )
    rows = list(result.all())
    return ClientAccessListResponse(
        items=[
            ClientAccessOut(
                id=r.id,
                project_id=r.project_id,
                client_contact_id=r.client_contact_id,
                contact_name=r.client_contact.name if r.client_contact else None,
                contact_email=r.client_contact.email if r.client_contact else None,
                client_id=r.client_contact.client_id if r.client_contact else None,
                client_name=r.client_contact.client.name if r.client_contact and r.client_contact.client else None,
                role=r.role,
                can_view_tasks=r.can_view_tasks,
                can_view_tickets=r.can_view_tickets,
                can_create_tasks=r.can_create_tasks,
                created_by=r.created_by,
                created_at=r.created_at,
            )
            for r in rows
        ]
    )


@router.get("/contacts", response_model=ProjectClientContactListResponse)
async def list_project_client_contacts(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    require_role(acc, MemberRole.maintainer)
    linked = await db.scalars(
        select(ProjectClient).where(ProjectClient.project_id == project_id)
    )
    linked_ids = [r.client_id for r in linked.all()]
    if not linked_ids:
        return ProjectClientContactListResponse(items=[])
    contacts = await db.scalars(
        select(ClientContact)
        .options(selectinload(ClientContact.client))
        .where(ClientContact.client_id.in_(linked_ids))
        .order_by(ClientContact.name)
    )
    rows = list(contacts.all())
    return ProjectClientContactListResponse(
        items=[
            ProjectClientContactOut(
                id=r.id,
                client_id=r.client_id,
                client_name=r.client.name if r.client else None,
                name=r.name,
                email=r.email,
                phone=r.phone,
                title=r.title,
                role=r.role,
                is_primary=r.is_primary,
            )
            for r in rows
        ]
    )


@router.post("", response_model=ClientAccessOut, status_code=status.HTTP_201_CREATED)
async def create_client_access(
    project_id: uuid.UUID,
    body: ClientAccessCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    require_role(acc, MemberRole.maintainer)
    if body.role not in CLIENT_ROLES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{body.role}'. Must be one of {sorted(CLIENT_ROLES)}",
        )
    contact = await db.get(ClientContact, body.client_contact_id)
    if contact is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Client contact not found"
        )
    linked = await db.scalar(
        select(ProjectClient).where(
            ProjectClient.project_id == project_id,
            ProjectClient.client_id == contact.client_id,
        )
    )
    if linked is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Contact's client is not linked to this project",
        )
    existing = await db.scalar(
        select(ProjectClientAccess).where(
            ProjectClientAccess.project_id == project_id,
            ProjectClientAccess.client_contact_id == body.client_contact_id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="This contact already has access to the project",
        )
    row = ProjectClientAccess(
        project_id=project_id,
        client_contact_id=body.client_contact_id,
        role=body.role,
        can_view_tasks=True,
        can_view_tickets=body.role in ("contribute", "decision_maker"),
        can_create_tasks=body.can_create_tasks,
        created_by=user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    await db.refresh(row, attribute_names=["client_contact"])
    return ClientAccessOut(
        id=row.id,
        project_id=row.project_id,
        client_contact_id=row.client_contact_id,
        contact_name=row.client_contact.name if row.client_contact else None,
        contact_email=row.client_contact.email if row.client_contact else None,
        client_id=row.client_contact.client_id if row.client_contact else None,
        client_name=row.client_contact.client.name if row.client_contact and row.client_contact.client else None,
        role=row.role,
        can_view_tasks=row.can_view_tasks,
        can_view_tickets=row.can_view_tickets,
        can_create_tasks=row.can_create_tasks,
        created_by=row.created_by,
        created_at=row.created_at,
    )


@router.patch("/{access_id}", response_model=ClientAccessOut)
async def patch_client_access(
    project_id: uuid.UUID,
    access_id: uuid.UUID,
    body: ClientAccessUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    require_role(acc, MemberRole.maintainer)
    row = await db.get(ProjectClientAccess, access_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Access grant not found")
    if body.role is not None:
        if body.role not in CLIENT_ROLES:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role '{body.role}'. Must be one of {sorted(CLIENT_ROLES)}",
            )
        row.role = body.role
    if body.can_view_tasks is not None:
        row.can_view_tasks = body.can_view_tasks
    if body.can_view_tickets is not None:
        row.can_view_tickets = body.can_view_tickets
    if body.can_create_tasks is not None:
        row.can_create_tasks = body.can_create_tasks
    await db.commit()
    await db.refresh(row)
    await db.refresh(row, attribute_names=["client_contact"])
    return ClientAccessOut(
        id=row.id,
        project_id=row.project_id,
        client_contact_id=row.client_contact_id,
        contact_name=row.client_contact.name if row.client_contact else None,
        contact_email=row.client_contact.email if row.client_contact else None,
        client_id=row.client_contact.client_id if row.client_contact else None,
        client_name=row.client_contact.client.name if row.client_contact and row.client_contact.client else None,
        role=row.role,
        can_view_tasks=row.can_view_tasks,
        can_view_tickets=row.can_view_tickets,
        can_create_tasks=row.can_create_tasks,
        created_by=row.created_by,
        created_at=row.created_at,
    )


@router.delete("/{access_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_client_access(
    project_id: uuid.UUID,
    access_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    require_role(acc, MemberRole.maintainer)
    row = await db.get(ProjectClientAccess, access_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Access grant not found")
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
