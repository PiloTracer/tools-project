"""Copy a process template onto one new project. Basic keeps the existing work-type seed."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project_template import (
    ProjectBoardColumn,
    ProjectTemplate,
    ProjectTemplateColumn,
    ProjectTemplateItem,
    ProjectTemplateWorkType,
)
from app.models.task import Task
from app.models.work_type import WorkType
from app.services.ref_alloc import allocate_ref

logger = logging.getLogger(__name__)

_KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def slug_key(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    slug = slug[:32].strip("-")
    if not slug or not _KEY_RE.match(slug):
        return "item"
    return slug


async def unique_template_key(db: AsyncSession, base: str) -> str:
    candidate = base
    n = 2
    while await db.scalar(select(ProjectTemplate.id).where(ProjectTemplate.key == candidate)):
        suffix = f"-{n}"
        candidate = f"{base[: 32 - len(suffix)]}{suffix}"
        n += 1
    return candidate


async def get_template(db: AsyncSession, key: str) -> ProjectTemplate | None:
    return await db.scalar(
        select(ProjectTemplate)
        .where(ProjectTemplate.key == key)
        .options(
            selectinload(ProjectTemplate.columns),
            selectinload(ProjectTemplate.work_types),
            selectinload(ProjectTemplate.items),
        )
    )


async def apply_template(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    template_key: str,
    reporter_id: uuid.UUID,
) -> None:
    """Copy a non-basic template. The caller has already skipped the general seed."""
    template = await get_template(db, template_key)
    if template is None or template.key == "basic":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="unknown_template")
    if not template.columns or not template.work_types:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_template")
    defaults = [row for row in template.work_types if row.is_default]
    if len(defaults) != 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_template")

    type_ids: dict[str, uuid.UUID] = {}
    for row in template.work_types:
        created = WorkType(
            project_id=project_id,
            key=row.key,
            name=row.name,
            description=row.description,
            is_default=row.is_default,
        )
        db.add(created)
        await db.flush()
        type_ids[row.key] = created.id

    finished = set()
    for row in template.columns:
        db.add(
            ProjectBoardColumn(
                project_id=project_id,
                key=row.key,
                label=row.label,
                sort_order=row.sort_order,
                is_finished=row.is_finished,
            )
        )
        if row.is_finished:
            finished.add(row.key)
    await db.flush()

    now = datetime.now(UTC)
    for item in template.items:
        work_type_id = type_ids.get(item.work_type_key)
        if work_type_id is None or item.column_key not in {col.key for col in template.columns}:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_template")
        ref = await allocate_ref(db, project_id, "task")
        db.add(
            Task(
                project_id=project_id,
                work_type_id=work_type_id,
                ref=ref,
                title=item.title,
                status=item.column_key,
                priority="normal",
                reporter_id=reporter_id,
                is_todo=False,
                closed_at=now if item.column_key in finished else None,
            )
        )
    logger.info("project.template_applied template_key=%s project_id=%s", template.key, project_id)


def build_template(
    *,
    key: str,
    name: str,
    team: str,
    description: str | None,
    columns: list[tuple[str, str, bool]],
    work_types: list[tuple[str, str, str | None, bool]],
    items: list[tuple[str, str, str]],
) -> ProjectTemplate:
    template = ProjectTemplate(
        key=key,
        name=name,
        team=team,
        description=description,
        is_builtin=False,
    )
    template.columns = [
        ProjectTemplateColumn(key=col_key, label=label, sort_order=index, is_finished=finished)
        for index, (col_key, label, finished) in enumerate(columns)
    ]
    template.work_types = [
        ProjectTemplateWorkType(
            key=type_key,
            name=type_name,
            description=type_description,
            is_default=is_default,
            sort_order=index,
        )
        for index, (type_key, type_name, type_description, is_default) in enumerate(work_types)
    ]
    template.items = [
        ProjectTemplateItem(
            title=title,
            column_key=column_key,
            work_type_key=work_type_key,
            sort_order=index,
        )
        for index, (title, column_key, work_type_key) in enumerate(items)
    ]
    return template
