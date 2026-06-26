from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.client import Client
from app.models.user import User
from app.schemas import (
    ClientCreate,
    ClientListResponse,
    ClientOut,
    ClientUpdate,
    slugify,
)

router = APIRouter(prefix="/v1/clients", tags=["clients"])


async def _unique_slug(db: AsyncSession, base: str) -> str:
    candidate = slugify(base)
    for _ in range(24):
        existing = await db.scalar(select(Client).where(Client.slug == candidate))
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
    db: Annotated[AsyncSession, Depends(get_db)],
):
    q = select(Client).order_by(Client.created_at.desc())
    result = await db.scalars(q)
    rows = list(result.all())
    return ClientListResponse(items=[ClientOut.model_validate(r) for r in rows])

@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(
    body: ClientCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    slug = await _unique_slug(db, body.name)
    row = Client(
        name=body.name.strip(),
        slug=slug,
        industry=body.industry.strip() if body.industry else None,
        notes=body.notes.strip() if body.notes else None,
        created_by=user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ClientOut.model_validate(row)


@router.get("/{client_id}", response_model=ClientOut)
async def get_client(
    client_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Client, client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientOut.model_validate(row)


@router.patch("/{client_id}", response_model=ClientOut)
async def update_client(
    client_id: uuid.UUID,
    body: ClientUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Client, client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    if body.name is not None:
        row.name = body.name.strip()
    if body.industry is not None:
        row.industry = body.industry.strip() if body.industry else None
    if body.notes is not None:
        row.notes = body.notes.strip() if body.notes else None
    await db.commit()
    await db.refresh(row)
    return ClientOut.model_validate(row)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Client, client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
