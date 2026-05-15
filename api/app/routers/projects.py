from __future__ import annotations

import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.project import Project
from app.models.user import User
from app.schemas import ProjectCreate, ProjectListResponse, ProjectOut

router = APIRouter(prefix="/v1/projects", tags=["projects"])

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")[:80]
    return s or "project"


async def _unique_slug(db: AsyncSession, base: str) -> str:
    candidate = base[:80]
    for _ in range(24):
        if not _SLUG_RE.match(candidate):
            candidate = _slugify(candidate) or "project"
        existing = await db.scalar(select(Project).where(Project.slug == candidate))
        if existing is None:
            return candidate
        suffix = uuid.uuid4().hex[:6]
        trimmed = base[: max(1, 80 - 7 - len(suffix))]
        candidate = f"{trimmed}-{suffix}"
    raise HTTPException(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not allocate a unique slug",
    )


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.scalars(
        select(Project)
        .where(Project.owner_id == user.id)
        .order_by(Project.created_at.desc()),
    )
    rows = list(result.all())
    return ProjectListResponse(items=[ProjectOut.model_validate(r) for r in rows])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    base_slug = (body.slug.strip() if body.slug else _slugify(body.name)).strip()
    slug = await _unique_slug(db, base_slug)
    row = Project(
        name=body.name.strip(),
        slug=slug,
        description=body.description.strip() if body.description else None,
        owner_id=user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ProjectOut.model_validate(row)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Project, project_id)
    if row is None or row.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectOut.model_validate(row)
