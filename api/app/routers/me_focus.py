from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.activity import Activity
from app.models.mention import Mention
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas import (
    MentionListResponse,
    MentionWithContext,
    TaskOut,
    TodayResponse,
    TodayTaskBundle,
)

router = APIRouter(prefix="/v1/me", tags=["me"])


@router.get("/today", response_model=TodayResponse)
async def my_today(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=7, ge=1, le=30),
):
    """Assigned tasks with a due date in the rolling window (default 7 days from today UTC)."""
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    horizon = start + timedelta(days=days + 1)
    stmt = (
        select(Task, Project.name)
        .join(Project, Task.project_id == Project.id)
        .where(Task.assignee_id == user.id)
        .where(Task.due_at.is_not(None))
        .where(Task.due_at >= start)
        .where(Task.due_at < horizon)
        .where(Task.status.not_in(["done", "cancelled"]))
        .order_by(Task.due_at.asc())
        .limit(100)
    )
    result = await db.execute(stmt)
    bundles: list[TodayTaskBundle] = []
    for task, project_name in result.all():
        bundles.append(
            TodayTaskBundle(
                task=TaskOut.model_validate(task),
                project_name=project_name,
            )
        )
    return TodayResponse(items=bundles)


@router.get("/mentions", response_model=MentionListResponse)
async def my_mentions(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
):
    stmt = (
        select(Mention, Activity.body, Project.name)
        .join(Activity, Mention.activity_id == Activity.id)
        .join(Project, Mention.project_id == Project.id)
        .where(Mention.mentioned_user_id == user.id)
        .order_by(Mention.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    items: list[MentionWithContext] = []
    for m, body, project_name in result.all():
        excerpt = (body or "")[:200]
        if len(body or "") > 200:
            excerpt += "…"
        items.append(
            MentionWithContext(
                id=m.id,
                project_id=m.project_id,
                project_name=project_name,
                activity_id=m.activity_id,
                excerpt=excerpt,
                created_at=m.created_at,
            )
        )
    return MentionListResponse(items=items)
