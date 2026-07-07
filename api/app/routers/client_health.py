from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_tenant, get_current_user
from app.models.activity import Activity
from app.models.client import Client
from app.models.project import Project
from app.models.project_client import ProjectClient
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas import ClientHealthItem, ClientHealthListResponse

router = APIRouter(prefix="/v1/clients", tags=["clients"])

TASK_DONE_STATUSES = frozenset({"done", "cancelled"})
TICKET_OPEN_STATUSES = frozenset({"open", "in_progress", "waiting_customer"})


def _compute_health(
    task_completion_pct: float | None,
    open_ticket_count: int,
    days_since_last_activity: int | None,
    days_since_project_update: int | None,
) -> tuple[int | None, str | None]:
    if task_completion_pct is None:
        return None, None

    score = 0
    score += int(task_completion_pct * 40)
    if open_ticket_count == 0:
        score += 25
    elif open_ticket_count <= 3:
        score += 18
    elif open_ticket_count <= 6:
        score += 10
    elif open_ticket_count <= 10:
        score += 5
    else:
        score += 0

    if days_since_last_activity is None or days_since_last_activity <= 3:
        score += 20
    elif days_since_last_activity <= 7:
        score += 15
    elif days_since_last_activity <= 14:
        score += 10
    elif days_since_last_activity <= 30:
        score += 5
    else:
        score += 0

    if days_since_project_update is None or days_since_project_update <= 7:
        score += 15
    elif days_since_project_update <= 14:
        score += 10
    elif days_since_project_update <= 30:
        score += 5
    elif days_since_project_update <= 60:
        score += 3
    else:
        score += 0

    label: str | None = None
    if score >= 80:
        label = "green"
    elif score >= 50:
        label = "yellow"
    else:
        label = "red"

    return score, label


@router.get("/health", response_model=ClientHealthListResponse)
async def list_client_health(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    tenant = await get_current_tenant(request, db)
    tenant_id = tenant.id if tenant else None
    is_cross_tenant_superuser = user.tenant_id is None
    now = datetime.now(UTC)

    base = select(Client)
    if tenant_id is not None and not is_cross_tenant_superuser:
        base = base.where(Client.tenant_id == tenant_id)
    clients_result = await db.execute(base.order_by(Client.name))
    all_clients = list(clients_result.scalars().all())

    items: list[ClientHealthItem] = []
    for client in all_clients:
        project_ids = (
            await db.execute(
                select(ProjectClient.project_id).where(
                    ProjectClient.client_id == client.id
                )
            )
        ).scalars().all()

        project_count = len(project_ids)
        if project_count == 0:
            items.append(
                ClientHealthItem(
                    client_id=client.id,
                    client_name=client.name,
                    client_slug=client.slug,
                    project_count=0,
                    open_ticket_count=0,
                )
            )
            continue

        task_data = (
            await db.execute(
                select(
                    func.count().label("total"),
                    func.sum(
                        func.cast(Task.status.in_(TASK_DONE_STATUSES), Integer)
                    ).label("done_count"),
                ).where(Task.project_id.in_(project_ids))
            )
        ).one()
        total_tasks = task_data.total or 0
        done_tasks = task_data.done_count or 0
        task_completion_pct = (
            round(done_tasks / total_tasks, 2) if total_tasks > 0 else None
        )

        ticket_count = (
            await db.scalar(
                select(func.count()).where(
                    Ticket.project_id.in_(project_ids),
                    Ticket.status.in_(TICKET_OPEN_STATUSES),
                )
            )
        ) or 0

        last_activity = (
            await db.scalar(
                select(func.max(Activity.created_at)).where(
                    Activity.project_id.in_(project_ids)
                )
            )
        )
        days_since_last_activity = (
            (now - last_activity).days if last_activity else None
        )

        last_project_update = (
            await db.scalar(
                select(func.max(Project.updated_at)).where(
                    Project.id.in_(project_ids)
                )
            )
        )
        days_since_project_update = (
            (now - last_project_update).days if last_project_update else None
        )

        score, label = _compute_health(
            task_completion_pct,
            ticket_count,
            days_since_last_activity,
            days_since_project_update,
        )

        items.append(
            ClientHealthItem(
                client_id=client.id,
                client_name=client.name,
                client_slug=client.slug,
                project_count=project_count,
                task_completion_pct=task_completion_pct,
                open_ticket_count=ticket_count,
                days_since_last_activity=days_since_last_activity,
                days_since_project_update=days_since_project_update,
                health_score=score,
                health_label=label,
            )
        )

    return ClientHealthListResponse(items=items)
