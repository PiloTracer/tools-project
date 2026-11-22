"""Allocate human-readable refs like PRJ-123 for tasks and PRJ-T-45 for tickets."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_counter import ProjectCounter
from app.models.task import Task
from app.models.ticket import Ticket


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

    Returns None if the project has no ``project_key`` set or
    ``auto_prefix_enabled`` is false.
    """
    proj = await db.get(Project, project_id)
    if proj is None or not proj.project_key or not proj.auto_prefix_enabled:
        return None
    await _ensure_counter(db, project_id, counter_type)

    # A ref can already exist when a task or ticket was created outside this
    # counter (for example a registry stub). Keep moving forward until the
    # formatted ref is free. A failed insert used to roll the counter back and
    # then retry the same taken number forever.
    for _ in range(1000):
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
        if row is None:
            return None
        assigned_number = row[0] - 1
        if counter_type == "ticket":
            ref = f"{proj.project_key}-T-{assigned_number}"
            taken = await db.scalar(select(Ticket.id).where(Ticket.ref == ref).limit(1))
        else:
            ref = f"{proj.project_key}-{assigned_number}"
            taken = await db.scalar(select(Task.id).where(Task.ref == ref).limit(1))
        if taken is None:
            return ref
    return None
