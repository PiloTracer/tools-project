"""A project counter that lags existing refs must still hand out a free ref."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_counter import ProjectCounter
from app.models.task import Task
from app.models.ticket import Ticket
from app.services.ref_alloc import allocate_ref
from tests.factories import create_project, create_user


async def test_task_ref_skips_numbers_already_in_use(db: AsyncSession):
    tag = uuid.uuid4().hex[:6].upper()
    key = f"R{tag}"
    user = await create_user(db, email=f"ref-{tag}@example.com")
    project = await create_project(
        db,
        name=f"Refs {tag}",
        slug=f"refs-{tag.lower()}",
        owner_id=user.id,
    )
    project.project_key = key
    project.auto_prefix_enabled = True
    db.add(
        ProjectCounter(
            project_id=project.id,
            counter_type="task",
            next_value=1,
        )
    )
    db.add(Task(project_id=project.id, title="Already one", ref=f"{key}-1", reporter_id=user.id))
    db.add(Task(project_id=project.id, title="Already two", ref=f"{key}-2", reporter_id=user.id))
    await db.commit()

    first = await allocate_ref(db, project.id, "task")
    second = await allocate_ref(db, project.id, "task")
    assert first == f"{key}-3"
    assert second == f"{key}-4"


async def test_ticket_ref_skips_numbers_already_in_use(db: AsyncSession):
    tag = uuid.uuid4().hex[:6].upper()
    key = f"Q{tag}"
    user = await create_user(db, email=f"tref-{tag}@example.com")
    project = await create_project(
        db,
        name=f"Ticket refs {tag}",
        slug=f"trefs-{tag.lower()}",
        owner_id=user.id,
    )
    project.project_key = key
    project.auto_prefix_enabled = True
    db.add(
        ProjectCounter(
            project_id=project.id,
            counter_type="ticket",
            next_value=1,
        )
    )
    db.add(
        Ticket(
            project_id=project.id,
            title="Already",
            ref=f"{key}-T-1",
            reporter_id=user.id,
        )
    )
    await db.commit()

    assigned = await allocate_ref(db, project.id, "ticket")
    assert assigned == f"{key}-T-2"
