"""Optional task recurrence and dependency checks. Dates are never moved."""

from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planning import TaskDependency
from app.models.task import Task
from app.services.board_columns import load_board_columns
from app.services.ref_alloc import allocate_ref

RECURRENCE = frozenset({"weekly", "monthly"})


async def _reaches(db: AsyncSession, start: uuid.UUID, target: uuid.UUID) -> bool:
    """True when following successor edges from start reaches target."""
    seen: set[uuid.UUID] = set()
    frontier = [start]
    while frontier:
        current = frontier.pop()
        if current in seen:
            continue
        seen.add(current)
        if current == target:
            return True
        rows = (
            await db.scalars(
                select(TaskDependency.successor_id).where(TaskDependency.predecessor_id == current)
            )
        ).all()
        frontier.extend(rows)
    return False


async def add_dependency(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    predecessor_id: uuid.UUID,
    successor_id: uuid.UUID,
) -> TaskDependency:
    if predecessor_id == successor_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="A task cannot depend on itself")
    tasks = list(
        (
            await db.scalars(
                select(Task).where(Task.id.in_([predecessor_id, successor_id]))
            )
        ).all()
    )
    if len(tasks) != 2 or any(task.project_id != project_id for task in tasks):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Both tasks must belong to this project")
    if await _reaches(db, successor_id, predecessor_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="That link would create a cycle")
    row = TaskDependency(
        project_id=project_id,
        predecessor_id=predecessor_id,
        successor_id=successor_id,
        dependency_type="finish_to_start",
    )
    db.add(row)
    await db.flush()
    return row


async def spawn_next_occurrence(db: AsyncSession, task: Task, reporter_id: uuid.UUID) -> None:
    """When a recurring task is closed, create the next open copy once."""
    if task.recurrence not in RECURRENCE or task.closed_at is None or task.due_at is None:
        return
    existing = await db.scalar(select(Task.id).where(Task.recurred_from_id == task.id))
    if existing is not None:
        return
    delta = timedelta(days=7 if task.recurrence == "weekly" else 30)
    columns = await load_board_columns(db, task.project_id)
    open_columns = [column for column in columns if not column.is_finished]
    next_status = open_columns[0].key if open_columns else "todo"
    ref = await allocate_ref(db, task.project_id, "task")
    db.add(
        Task(
            project_id=task.project_id,
            component_id=task.component_id,
            work_type_id=task.work_type_id,
            ref=ref,
            title=task.title,
            description=task.description,
            status=next_status,
            priority=task.priority,
            assignee_id=task.assignee_id,
            reporter_id=reporter_id,
            due_at=task.due_at + delta,
            recurrence=task.recurrence,
            recurred_from_id=task.id,
        )
    )
