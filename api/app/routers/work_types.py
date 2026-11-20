from __future__ import annotations

import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.models.work_type import WorkType
from app.schemas import (
    WorkTypeCreate,
    WorkTypeListResponse,
    WorkTypeOut,
    WorkTypePatch,
)
from app.services.project_access import MemberRole, require_project_access, require_role

router = APIRouter(
    prefix="/v1/projects/{project_id}/work-types",
    tags=["work-types"],
)
detail_router = APIRouter(prefix="/v1/work-types", tags=["work-types"])

_KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _slug_key(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    slug = slug[:32].strip("-")
    if not slug or not _KEY_RE.match(slug):
        return "type"
    return slug


async def _unique_key(db: AsyncSession, project_id: uuid.UUID, base: str) -> str:
    candidate = base
    n = 2
    while True:
        taken = await db.scalar(
            select(WorkType.id).where(
                WorkType.project_id == project_id,
                WorkType.key == candidate,
            )
        )
        if taken is None:
            return candidate
        suffix = f"-{n}"
        candidate = f"{base[: 32 - len(suffix)]}{suffix}"
        n += 1


async def require_project_work_type(
    db: AsyncSession,
    project_id: uuid.UUID,
    work_type_id: uuid.UUID,
) -> WorkType:
    row = await db.get(WorkType, work_type_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="work_type_id must belong to this project",
        )
    return row


@router.get("", response_model=WorkTypeListResponse)
async def list_work_types(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await require_project_access(db, user, project_id)
    result = await db.scalars(
        select(WorkType)
        .where(WorkType.project_id == project_id)
        .order_by(WorkType.is_default.desc(), WorkType.name.asc())
    )
    rows = list(result.all())
    return WorkTypeListResponse(items=[WorkTypeOut.model_validate(r) for r in rows])


@router.post("", response_model=WorkTypeOut, status_code=status.HTTP_201_CREATED)
async def create_work_type(
    project_id: uuid.UUID,
    body: WorkTypeCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    require_role(acc, MemberRole.contributor)
    key = body.key.strip() if body.key else _slug_key(body.name)
    key = await _unique_key(db, project_id, key)
    row = WorkType(
        project_id=project_id,
        key=key,
        name=body.name.strip(),
        description=body.description.strip() if body.description else None,
        is_default=False,
    )
    db.add(row)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="A work type with this key already exists",
        ) from None
    await db.refresh(row)
    return WorkTypeOut.model_validate(row)


@detail_router.patch("/{work_type_id}", response_model=WorkTypeOut)
async def patch_work_type(
    work_type_id: uuid.UUID,
    body: WorkTypePatch,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(WorkType, work_type_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Work type not found")
    acc = await require_project_access(db, user, row.project_id)
    require_role(acc, MemberRole.contributor)
    if body.name is not None:
        row.name = body.name.strip()
    if body.description is not None:
        v = body.description.strip()
        row.description = v if v else None
    if body.is_default is True:
        await db.execute(
            update(WorkType)
            .where(
                WorkType.project_id == row.project_id,
                WorkType.id != row.id,
            )
            .values(is_default=False)
        )
        row.is_default = True
    elif body.is_default is False and row.is_default:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Choose another default work type before clearing this one",
        )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Could not update the work type",
        ) from None
    await db.refresh(row)
    return WorkTypeOut.model_validate(row)


@detail_router.delete("/{work_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_type(
    work_type_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(WorkType, work_type_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Work type not found")
    acc = await require_project_access(db, user, row.project_id)
    require_role(acc, MemberRole.maintainer)
    if row.is_default:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="The default work type cannot be deleted",
        )
    task_count = await db.scalar(
        select(func.count()).select_from(Task).where(Task.work_type_id == row.id)
    )
    ticket_count = await db.scalar(
        select(func.count()).select_from(Ticket).where(Ticket.work_type_id == row.id)
    )
    if (task_count or 0) > 0 or (ticket_count or 0) > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="This work type is still used by tasks or tickets",
        )
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
