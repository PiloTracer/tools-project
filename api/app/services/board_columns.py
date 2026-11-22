"""Task status rules. A project with board columns uses those keys. Otherwise the global set."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_template import ProjectBoardColumn
from app.schemas import TASK_STATUSES

_GLOBAL_FINISHED = frozenset({"done", "cancelled"})


async def load_board_columns(db: AsyncSession, project_id: uuid.UUID) -> list[ProjectBoardColumn]:
    rows = await db.scalars(
        select(ProjectBoardColumn)
        .where(ProjectBoardColumn.project_id == project_id)
        .order_by(ProjectBoardColumn.sort_order, ProjectBoardColumn.label)
    )
    return list(rows.all())


async def task_status_sets(
    db: AsyncSession, project_id: uuid.UUID
) -> tuple[frozenset[str], frozenset[str]]:
    columns = await load_board_columns(db, project_id)
    if not columns:
        return TASK_STATUSES, _GLOBAL_FINISHED
    return (
        frozenset(column.key for column in columns),
        frozenset(column.key for column in columns if column.is_finished),
    )


async def project_has_board(db: AsyncSession, project_id: uuid.UUID) -> bool:
    found = await db.scalar(
        select(ProjectBoardColumn.id).where(ProjectBoardColumn.project_id == project_id).limit(1)
    )
    return found is not None


def apply_task_status(raw: str, allowed: frozenset[str], finished: frozenset[str]) -> tuple[str, datetime | None]:
    status_val = raw.strip()
    if status_val not in allowed:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_status")
    closed_at = datetime.now(UTC) if status_val in finished else None
    return status_val, closed_at
