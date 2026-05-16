"""Allocate human-readable refs like PRJ-123 for tasks and PRJ-T-45 for tickets."""

from __future__ import annotations

import uuid

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_counter import ProjectCounter


async def _ensure_counter(
    db: AsyncSession, project_id: uuid.UUID, counter_type: str
) -> None:
    stmt = (
        pg_insert(ProjectCounter)
        .values(
            id=uuid.uuid4(),
            project_id=project_id,
            counter_type=counter_type,
            next_value=1,
        )
        .on_conflict_do_nothing(
            index_elements=["project_id", "counter_type"]
        )
    )
    await db.execute(stmt)
    await db.flush()


async def allocate_ref(
    db: AsyncSession,
    project_id: uuid.UUID,
    counter_type: str,
) -> str | None:
    """Atomically increment the project counter and return a human ref like PRJ-123.

    Returns None if the project has no ``project_key`` set.
    """
    proj = await db.get(Project, project_id)
    if proj is None or not proj.project_key:
        return None
    await _ensure_counter(db, project_id, counter_type)

    result = await db.execute(
        update(ProjectCounter)
        .where(
            ProjectCounter.project_id == project_id,
            ProjectCounter.counter_type == counter_type,
        )
        .values(next_value=ProjectCounter.next_value + 1)
        .returning(ProjectCounter.next_value)
    )
    row = result.fetchone()
    # next_value is the *new* value after increment; the one we just assigned
    # is (new_value - 1).  But RETURNING gives us the updated value.
    # Actually the returned value is the post-increment value.
    # We assigned this value. The previous value was (next_value - 1).
    if row is None:
        return None
    assigned_number = row[0] - 1  # the number we just allocated
    if counter_type == "ticket":
        return f"{proj.project_key}-T-{assigned_number}"
    return f"{proj.project_key}-{assigned_number}"
