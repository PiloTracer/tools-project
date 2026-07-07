from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db import get_db
from app.deps import require_agent_or_user
from app.models.client_contact import ClientContact
from app.models.user import User
from app.schemas import WhoamiCompany, WhoamiResponse, WhoamiUser

router = APIRouter(prefix="/v1/platform", tags=["platform"])


@router.get("/whoami", response_model=WhoamiResponse)
async def platform_whoami(
    user: Annotated[User, Depends(require_agent_or_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    contacts = (
        await db.execute(
            select(ClientContact)
            .options(joinedload(ClientContact.client))
            .where(ClientContact.user_id == user.id)
        )
    ).scalars().all()

    companies = [
        WhoamiCompany(
            client_id=c.client_id,
            name=c.client.name,
            role=c.role,
        )
        for c in contacts
        if c.client is not None
    ]

    return WhoamiResponse(
        user=WhoamiUser(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
        ),
        companies=companies,
    )
