from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.mention import Mention
from app.models.user import User
from app.services.mention_parse import mention_emails_from_text


async def write_activity(
    *,
    db: AsyncSession,
    project_id: uuid.UUID,
    subject_type: str,
    subject_id: uuid.UUID,
    kind: str,
    actor_id: uuid.UUID | None = None,
    body: str,
    parent_activity_id: uuid.UUID | None = None,
    meta_json: dict | None = None,
    is_internal: bool = False,
) -> Activity:
    row = Activity(
        project_id=project_id,
        subject_type=subject_type,
        subject_id=subject_id,
        kind=kind,
        actor_id=actor_id,
        body=body,
        parent_activity_id=parent_activity_id,
        meta_json=meta_json,
        is_internal=is_internal,
    )
    db.add(row)
    await db.flush()
    if actor_id is not None:
        for email in mention_emails_from_text(body):
            user = await db.scalar(select(User).where(User.email == email))
            if user is None or user.id == actor_id:
                continue
            stmt = (
                pg_insert(Mention)
                .values(
                    id=uuid.uuid4(),
                    project_id=project_id,
                    activity_id=row.id,
                    mentioned_user_id=user.id,
                )
                .on_conflict_do_nothing(index_elements=["activity_id", "mentioned_user_id"])
            )
            await db.execute(stmt)
    return row
