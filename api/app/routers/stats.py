from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user, require_superuser
from app.models.client import Client
from app.models.inbox_item import InboxItem
from app.models.mention import Mention
from app.models.project import Project
from app.models.prospect import PIPELINE_STAGE_ORDER, TERMINAL_STAGES, Prospect
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas import (
    GlobalStatsOut,
    MyStatsOut,
    PipelineStageStats,
    PipelineStatsOut,
)

router = APIRouter(prefix="/v1/stats", tags=["stats"])

STAGE_LABELS: dict[str, str] = {
    "target": "Target",
    "connected": "Connected",
    "engaged": "Engaged",
    "call_scheduled": "Call Scheduled",
    "call_done": "Call Done",
    "proposal_sent": "Proposal Sent",
    "negotiating": "Negotiating",
    "won": "Won",
    "lost": "Lost",
}


@router.get("/pipeline", response_model=PipelineStatsOut)
async def pipeline_stats(
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = await db.scalars(select(Prospect))
    prospects = list(rows.all())

    stage_map: dict[str, dict] = {}
    for s in PIPELINE_STAGE_ORDER:
        stage_map[s] = {"count": 0, "value": 0.0}

    for p in prospects:
        v = float(p.pipeline_value) if p.pipeline_value is not None else 0.0
        stage_map[p.pipeline_stage]["count"] += 1
        stage_map[p.pipeline_stage]["value"] += v

    by_stage = [
        PipelineStageStats(
            stage=s,
            label=STAGE_LABELS.get(s, s),
            count=stage_map[s]["count"],
            value=round(stage_map[s]["value"], 2),
        )
        for s in PIPELINE_STAGE_ORDER
    ]

    total_value = sum(s.value for s in by_stage)
    won_amt = stage_map["won"]["value"]
    lost_amt = stage_map["lost"]["value"]
    total_terminal = stage_map["won"]["count"] + stage_map["lost"]["count"]
    conversion_rate = round(stage_map["won"]["count"] / total_terminal, 4) if total_terminal > 0 else None

    today = datetime.now(UTC).date()
    needs_attention_count = sum(
        1 for p in prospects
        if p.next_action_date is not None
        and p.next_action_date <= today
        and p.pipeline_stage not in TERMINAL_STAGES
    )

    return PipelineStatsOut(
        by_stage=by_stage,
        total_value=round(total_value, 2),
        won_value=round(won_amt, 2),
        lost_value=round(lost_amt, 2),
        conversion_rate=conversion_rate,
        needs_attention_count=needs_attention_count,
    )


@router.get("/global", response_model=GlobalStatsOut)
async def global_stats(
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    projects_count = await db.scalar(select(func.count(Project.id)))
    active_count = await db.scalar(
        select(func.count(Project.id)).where(Project.status == "active")
    )
    open_tasks = await db.scalar(
        select(func.count(Task.id)).where(Task.status.not_in(("done", "cancelled")))
    )
    open_tickets = await db.scalar(
        select(func.count(Ticket.id)).where(Ticket.status.not_in(("closed", "resolved")))
    )
    prospects_count = await db.scalar(select(func.count(Prospect.id)))
    clients_count = await db.scalar(select(func.count(Client.id)))

    return GlobalStatsOut(
        total_projects=projects_count or 0,
        active_projects=active_count or 0,
        open_tasks=open_tasks or 0,
        open_tickets=open_tickets or 0,
        total_prospects=prospects_count or 0,
        total_clients=clients_count or 0,
    )


@router.get("/me", response_model=MyStatsOut)
async def my_stats(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)

    open_tasks = await db.scalar(
        select(func.count(Task.id)).where(
            Task.assignee_id == user.id,
            Task.status.not_in(("done", "cancelled")),
        )
    )
    overdue_tasks = await db.scalar(
        select(func.count(Task.id)).where(
            Task.assignee_id == user.id,
            Task.status.not_in(("done", "cancelled")),
            Task.due_at < now,
        )
    )
    done_this_week = await db.scalar(
        select(func.count(Task.id)).where(
            Task.assignee_id == user.id,
            Task.status == "done",
            Task.closed_at >= week_ago,
        )
    )
    inbox_count = await db.scalar(
        select(func.count(InboxItem.id)).where(
            InboxItem.owner_id == user.id,
            InboxItem.triaged_to_id.is_(None),
        )
    )
    mention_count = await db.scalar(
        select(func.count(Mention.id)).where(
            Mention.mentioned_user_id == user.id,
            Mention.created_at >= week_ago,
        )
    )
    open_tickets = await db.scalar(
        select(func.count(Ticket.id)).where(
            Ticket.assignee_id == user.id,
            Ticket.status.not_in(("closed", "resolved")),
        )
    )

    return MyStatsOut(
        open_tasks=open_tasks or 0,
        overdue_tasks=overdue_tasks or 0,
        done_this_week=done_this_week or 0,
        inbox_count=inbox_count or 0,
        mention_count=mention_count or 0,
        open_tickets=open_tickets or 0,
    )
