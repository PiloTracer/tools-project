from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user, require_superuser
from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.user import User
from app.schemas import (
    ClientContactCreate,
    ClientContactListResponse,
    ClientContactOut,
    ClientContactUpdate,
    UserSearchResult,
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
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _resolve_client(db, client_id)
    result = await db.execute(
        select(ClientContact, User)
        .outerjoin(User, User.id == ClientContact.user_id)
        .where(ClientContact.client_id == client_id)
        .order_by(ClientContact.created_at.desc())
    )
    rows = result.all()
    return ClientContactListResponse(
        items=[
            ClientContactOut(
                id=cc.id,
                client_id=cc.client_id,
                prospect_id=cc.prospect_id,
                user_id=cc.user_id,
                user_email=u.email if u else None,
                user_name=u.display_name if u else None,
                name=cc.name,
                email=cc.email,
                phone=cc.phone,
                title=cc.title,
                role=cc.role,
                is_primary=cc.is_primary,
                notes=cc.notes,
                created_at=cc.created_at,
                updated_at=cc.updated_at,
            )
            for cc, u in rows
        ]
    )


@router.post("", response_model=ClientContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact(
    client_id: uuid.UUID,
    body: ClientContactCreate,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
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


@router.get("/search-users", response_model=list[UserSearchResult])
async def search_linkable_users(
    client_id: uuid.UUID,
    q: Annotated[str, Query(min_length=1, max_length=200)],
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _resolve_client(db, client_id)
    term = f"%{q.strip()}%"
    already_linked = select(ClientContact.user_id).where(
        ClientContact.user_id.is_not(None)
    )
    result = await db.execute(
        select(User.id, User.email, User.display_name)
        .where(User.is_active.is_(True))
        .where(~User.id.in_(already_linked))
        .where(
            or_(
                User.email.ilike(term),
                User.display_name.ilike(term),
            )
        )
        .order_by(User.email.asc())
        .limit(20)
    )
    rows = result.all()
    return [UserSearchResult(id=uid, email=email, display_name=name) for uid, email, name in rows]


@router.get("/{contact_id}", response_model=ClientContactOut)
async def get_contact(
    client_id: uuid.UUID,
    contact_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
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
    _admin: Annotated[User, Depends(require_superuser)],
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
    if body.user_id is not None:
        linked = await db.get(User, body.user_id)
        if linked is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        if row.user_id != body.user_id:
            clash = await db.scalar(
                select(ClientContact).where(
                    ClientContact.user_id == body.user_id,
                    ClientContact.id != row.id,
                )
            )
            if clash is not None:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail="This user is already linked to another contact",
                )
        row.user_id = body.user_id
    elif "user_id" in body.model_dump(exclude_unset=True):
        row.user_id = None
    await db.commit()
    await db.refresh(row)
    return ClientContactOut.model_validate(row)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    client_id: uuid.UUID,
    contact_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _resolve_client(db, client_id)
    row = await db.get(ClientContact, contact_id)
    if not row or row.client_id != client_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
