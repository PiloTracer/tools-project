from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.deps import get_current_user, require_superuser
from app.models.project_template import ProjectTemplate
from app.models.user import User
from app.schemas import (
    ProjectTemplateCreate,
    ProjectTemplateListResponse,
    ProjectTemplateOut,
    TemplateColumnOut,
    TemplateItemOut,
    TemplateWorkTypeOut,
)
from app.services.project_templates import build_template, slug_key, unique_template_key

router = APIRouter(prefix="/v1/project-templates", tags=["project-templates"])
logger = logging.getLogger(__name__)


def _out(row: ProjectTemplate) -> ProjectTemplateOut:
    return ProjectTemplateOut(
        id=row.id,
        key=row.key,
        name=row.name,
        team=row.team,
        description=row.description,
        is_builtin=row.is_builtin,
        columns=[
            TemplateColumnOut(
                key=column.key,
                label=column.label,
                sort_order=column.sort_order,
                is_finished=column.is_finished,
            )
            for column in row.columns
        ],
        work_types=[
            TemplateWorkTypeOut(
                key=work_type.key,
                name=work_type.name,
                description=work_type.description,
                is_default=work_type.is_default,
            )
            for work_type in row.work_types
        ],
        items=[
            TemplateItemOut(
                title=item.title,
                column_key=item.column_key,
                work_type_key=item.work_type_key,
            )
            for item in row.items
        ],
    )


@router.get("", response_model=ProjectTemplateListResponse)
async def list_project_templates(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    del user
    rows = list(
        (
            await db.scalars(
                select(ProjectTemplate)
                .options(
                    selectinload(ProjectTemplate.columns),
                    selectinload(ProjectTemplate.work_types),
                    selectinload(ProjectTemplate.items),
                )
                .order_by(ProjectTemplate.team.asc().nullsfirst(), ProjectTemplate.name.asc())
            )
        ).all()
    )
    return ProjectTemplateListResponse(items=[_out(row) for row in rows])


@router.post("", response_model=ProjectTemplateOut, status_code=status.HTTP_201_CREATED)
async def create_project_template(
    body: ProjectTemplateCreate,
    user: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    del user
    defaults = [row for row in body.work_types if row.is_default]
    if len(defaults) != 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_template")
    column_keys: dict[str, str] = {}
    columns: list[tuple[str, str, bool]] = []
    for column in body.columns:
        key = slug_key(column.label)
        if key in column_keys:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_template")
        column_keys[column.label.strip().lower()] = key
        columns.append((key, column.label.strip(), column.is_finished))
    type_keys: dict[str, str] = {}
    work_types: list[tuple[str, str, str | None, bool]] = []
    for work_type in body.work_types:
        key = slug_key(work_type.name)
        if key in {row[0] for row in work_types}:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_template")
        type_keys[work_type.name.strip().lower()] = key
        description = work_type.description.strip() if work_type.description else None
        work_types.append((key, work_type.name.strip(), description, work_type.is_default))
    items: list[tuple[str, str, str]] = []
    for item in body.items:
        column_key = column_keys.get(item.column_label.strip().lower())
        work_type_key = type_keys.get(item.work_type_name.strip().lower())
        if column_key is None or work_type_key is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_template")
        items.append((item.title.strip(), column_key, work_type_key))

    key = await unique_template_key(db, slug_key(body.name))
    row = build_template(
        key=key,
        name=body.name.strip(),
        team=body.team.strip(),
        description=body.description.strip() if body.description else None,
        columns=columns,
        work_types=work_types,
        items=items,
    )
    db.add(row)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="template_key_taken") from None
    await db.refresh(row)
    loaded = await db.scalar(
        select(ProjectTemplate)
        .where(ProjectTemplate.id == row.id)
        .options(
            selectinload(ProjectTemplate.columns),
            selectinload(ProjectTemplate.work_types),
            selectinload(ProjectTemplate.items),
        )
    )
    assert loaded is not None
    logger.info("project.template_created key=%s", loaded.key)
    return _out(loaded)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_template(
    template_id: uuid.UUID,
    user: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    del user
    row = await db.get(ProjectTemplate, template_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="template_not_found")
    if row.is_builtin:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="builtin_template")
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
