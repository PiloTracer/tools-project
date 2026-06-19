"""Prospect-to-client promotion and pipeline helpers."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.prospect import Prospect
from app.schemas import slugify


async def ensure_unique_client_slug(db: AsyncSession, company_name: str) -> str:
    """Generate a unique slug for a client based on the company name."""
    client_slug = slugify(company_name)
    existing = await db.scalar(select(Client).where(Client.slug == client_slug))
    if not existing:
        return client_slug
    for i in range(1, 100):
        candidate = f"{client_slug}-{i}"
        dup = await db.scalar(select(Client).where(Client.slug == candidate))
        if not dup:
            return candidate
    raise ValueError("Could not allocate a unique client slug")


async def promote_prospect_to_client(
    db: AsyncSession,
    prospect: Prospect,
    *,
    created_by: uuid.UUID | None = None,
) -> Client:
    """Transactional promotion: when a prospect reaches `won`, create the client record.

    Args:
        db: active async SQLAlchemy session.
        prospect: the prospect being promoted (must already be in `won` stage).
        created_by: user ID to record as creator. Defaults to the prospect's creator.

    Returns:
        The newly created Client instance (already added to the session, not committed).
    """
    if prospect.pipeline_stage != "won":
        raise ValueError("Prospect must be in 'won' stage to promote to client")

    client_slug = await ensure_unique_client_slug(db, prospect.company_name)
    client = Client(
        name=prospect.company_name,
        slug=client_slug,
        prospect_id=prospect.id,
        created_by=created_by or prospect.created_by,
    )
    db.add(client)
    return client
