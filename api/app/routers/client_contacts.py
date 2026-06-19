from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.user import User
from app.schemas import (
    ClientContactCreate,
    ClientContactListResponse,
    ClientContactOut,
    ClientContactUpdate,
)

router = APIRouter(prefix="/v1/clients/{client_id}/contacts", tags=["client_contacts"])


async def _resolve_client(
    db: AsyncSession, client_id: uuid.UUID
) -> Client:
    row = await db.get(Client, client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return row


@router.get("", response_model=ClientContactListResponse)
async def list_contacts(
    client_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _resolve_client(db, client_id)
    q = (
        select(ClientContact)
        .where(ClientContact.client_id == client_id)
        .order_by(ClientContact.created_at.desc())
    )
    result = await db.scalars(q)
    rows = list(result.all())
    return ClientContactListResponse(items=[ClientContactOut.model_validate(r) for r in rows])


@router.post("", response_model=ClientContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact(
    client_id: uuid.UUID,
    body: ClientContactCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _resolve_client(db, client_id)
    row = ClientContact(
        client_id=client_id,
        prospect_id=body.prospect_id,
        user_id=body.user_id,
        name=body.name.strip(),
        email=body.email.strip(),
        phone=body.phone.strip() if body.phone else None,
        title=body.title.strip() if body.title else None,
        role=body.role,
        is_primary=body.is_primary,
        notes=body.notes.strip() if body.notes else None,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ClientContactOut.model_validate(row)


@router.get("/{contact_id}", response_model=ClientContactOut)
async def get_contact(
    client_id: uuid.UUID,
    contact_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _resolve_client(db, client_id)
    row = await db.get(ClientContact, contact_id)
    if not row or row.client_id != client_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ClientContactOut.model_validate(row)


@router.patch("/{contact_id}", response_model=ClientContactOut)
async def update_contact(
    client_id: uuid.UUID,
    contact_id: uuid.UUID,
    body: ClientContactUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _resolve_client(db, client_id)
    row = await db.get(ClientContact, contact_id)
    if not row or row.client_id != client_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    if body.name is not None:
        row.name = body.name.strip()
    if body.email is not None:
        row.email = body.email.strip()
    if body.phone is not None:
        row.phone = body.phone.strip() if body.phone else None
    if body.title is not None:
        row.title = body.title.strip() if body.title else None
    if body.role is not None:
        row.role = body.role
    if body.is_primary is not None:
        row.is_primary = body.is_primary
    if body.notes is not None:
        row.notes = body.notes.strip() if body.notes else None
    await db.commit()
    await db.refresh(row)
    return ClientContactOut.model_validate(row)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    client_id: uuid.UUID,
    contact_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _resolve_client(db, client_id)
    row = await db.get(ClientContact, contact_id)
    if not row or row.client_id != client_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
