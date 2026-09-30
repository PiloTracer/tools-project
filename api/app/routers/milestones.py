from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user, require_agent_or_user
from app.models.milestone import Milestone
from app.models.task import Task
from app.models.user import User
from app.schemas import (
    MilestoneCreate,
    MilestoneListResponse,
    MilestoneOut,
    MilestonePatch,
    PlanImportManifest,
    PlanImportResult,
)
from app.services.agent_identity import ensure_agent_user
from app.services.plan_import import ManifestError, run_plan_import
from app.services.project_access import (
    MemberRole,
    can_create_tasks,
    require_project_access,
    require_role,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/projects/{project_id}/milestones",
    tags=["milestones"],
)
detail_router = APIRouter(prefix="/v1/milestones", tags=["milestones"])
import_router = APIRouter(
    prefix="/v1/projects/{project_id}/plan-import",
    tags=["plan-import"],
)


async def _progress_map(db: AsyncSession, project_id: uuid.UUID) -> dict[uuid.UUID, tuple[int, int]]:
    rows = (
        await db.execute(
            select(
                Task.milestone_id,
                func.count(Task.id),
                func.coalesce(
                    func.sum(case((Task.status == "done", 1), else_=0)),
                    0,
                ),
            )
            .where(Task.project_id == project_id)
            .group_by(Task.milestone_id)
        )
    ).all()
    return {mid: (total, done) for mid, total, done in rows if mid is not None}


def _out(row: Milestone, progress: tuple[int, int] | None) -> MilestoneOut:
    out = MilestoneOut.model_validate(row)
    if progress is not None:
        out.task_total, out.task_done = progress
    return out


async def _ensure_key_free(
    db: AsyncSession, project_id: uuid.UUID, key: str | None, exclude_id: uuid.UUID | None = None
) -> None:
    if not key:
        return
    stmt = select(Milestone.id).where(
        Milestone.project_id == project_id, Milestone.key == key
    )
    if exclude_id is not None:
        stmt = stmt.where(Milestone.id != exclude_id)
    if await db.scalar(stmt) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"Milestone key '{key}' already exists in this project",
        )


@router.get("", response_model=MilestoneListResponse)
async def list_milestones(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await require_project_access(db, user, project_id)
    rows = list(
        (
            await db.scalars(
                select(Milestone)
                .where(Milestone.project_id == project_id)
                .order_by(Milestone.sort_order.asc(), Milestone.created_at.asc())
            )
        ).all()
    )
    progress = await _progress_map(db, project_id)
    return MilestoneListResponse(items=[_out(r, progress.get(r.id)) for r in rows])


@router.post("", response_model=MilestoneOut, status_code=status.HTTP_201_CREATED)
async def create_milestone(
    project_id: uuid.UUID,
    body: MilestoneCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    require_role(acc, MemberRole.contributor)
    await _ensure_key_free(db, project_id, body.key)
    row = Milestone(
        project_id=project_id,
        key=body.key,
        name=body.name.strip(),
        summary=body.summary,
        description=body.description,
        status=body.status,
        plan_state="active",
        sort_order=body.sort_order,
        start_at=body.start_at,
        due_at=body.due_at,
        created_by=user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _out(row, (0, 0))


@detail_router.patch("/{milestone_id}", response_model=MilestoneOut)
async def patch_milestone(
    milestone_id: uuid.UUID,
    body: MilestonePatch,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Milestone, milestone_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Milestone not found")
    acc = await require_project_access(db, user, row.project_id)
    require_role(acc, MemberRole.contributor)
    if body.key is not None:
        await _ensure_key_free(db, row.project_id, body.key, exclude_id=row.id)
        row.key = body.key
    if body.name is not None:
        row.name = body.name.strip()
    if body.summary is not None:
        row.summary = body.summary
    if body.description is not None:
        row.description = body.description
    if body.sort_order is not None:
        row.sort_order = body.sort_order
    if body.start_at is not None:
        row.start_at = body.start_at
    if body.due_at is not None:
        row.due_at = body.due_at
    if body.status is not None and body.status != row.status:
        # SPEC R2: activating one milestone clears 'active' on the rest.
        if body.status == "active":
            others = list(
                (
                    await db.scalars(
                        select(Milestone).where(
                            Milestone.project_id == row.project_id,
                            Milestone.status == "active",
                            Milestone.id != row.id,
                        )
                    )
                ).all()
            )
            for other in others:
                other.status = "pending"
        row.status = body.status
    await db.commit()
    await db.refresh(row)
    progress = await _progress_map(db, row.project_id)
    return _out(row, progress.get(row.id))


@import_router.post("", response_model=PlanImportResult)
async def plan_import(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(require_agent_or_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    dry_run: bool = Query(default=False),
    body: dict = Body(...),
):
    acc = await require_project_access(db, user, project_id)
    if not can_create_tasks(acc):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Not permitted to import into this project",
        )
    try:
        manifest = PlanImportManifest.model_validate(body)
    except ValidationError as exc:
        errors = [
            f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        ]
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=errors) from exc
    # The agent key synthesizes a user id that is not in the users table;
    # reporter_id/created_by/actor_id are FKs, so resolve to the persisted
    # agent row first (idempotent). JWT users already exist in the table.
    actor_id = user.id
    if await db.get(User, user.id) is None:
        actor_id = await ensure_agent_user(db, acc.project.tenant_id)
    try:
        return await run_plan_import(
            db, project_id, manifest, dry_run=dry_run, actor_id=actor_id
        )
    except ManifestError as exc:
        await db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.errors) from exc
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        logger.exception("plan_import.failed project=%s", project_id)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Import failed; no changes applied",
        ) from None
