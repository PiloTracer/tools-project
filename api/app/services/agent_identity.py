"""Persistent identity for the server-wide agent API key.

``deps.require_agent_or_user`` synthesizes an in-memory superuser for
``X-Api-Key`` requests, but that id does not exist in the ``users`` table —
and ``tasks.reporter_id`` / ``activities.actor_id`` / ``milestones.created_by``
are foreign keys into it. Any write path reached with the agent key must
resolve the synthetic id to this persisted row first (idempotent upsert,
safe under concurrency via ON CONFLICT DO NOTHING).
"""

from __future__ import annotations

import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

# Must match the id synthesized by deps.require_agent_or_user.
AGENT_USER_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "agent.localhost")
AGENT_USER_EMAIL = "agent@localhost"


async def ensure_agent_user(
    db: AsyncSession, tenant_id: uuid.UUID | None = None
) -> uuid.UUID:
    """Return the persisted agent user's id, creating the row if absent.

    The row carries no password (``password_hash`` is NULL) so the account
    cannot be used for local login; it exists only as an FK anchor for
    agent-driven writes.
    """
    if await db.get(User, AGENT_USER_ID) is not None:
        return AGENT_USER_ID
    stmt = (
        pg_insert(User)
        .values(
            id=AGENT_USER_ID,
            email=AGENT_USER_EMAIL,
            password_hash=None,
            display_name="Agent",
            is_active=True,
            is_superuser=False,
            auth_source="local",
            tenant_id=tenant_id,
        )
        .on_conflict_do_nothing(index_elements=["id"])
    )
    await db.execute(stmt)
    return AGENT_USER_ID
