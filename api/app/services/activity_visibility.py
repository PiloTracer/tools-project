"""Visibility rules for client participants reading a project's activity feed."""

from __future__ import annotations

import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models.activity import Activity
from app.models.task import Task
from app.models.ticket import Ticket
from app.services.project_access import (
    ProjectAccess,
    can_view_tasks,
    can_view_tickets,
    client_company_user_ids,
)


async def client_visible_subject_ids(
    db: AsyncSession,
    acc: ProjectAccess,
    project_id: uuid.UUID,
) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
    """Return task/ticket ids a client participant may see in a project.

    Uses the same assignee rule as the client task/ticket lists. Callers must
    only use this for a client participant (``acc.client_access is not None``).
    """
    peer_ids = await client_company_user_ids(db, acc)
    task_ids: list[uuid.UUID] = []
    ticket_ids: list[uuid.UUID] = []
    if can_view_tasks(acc) and peer_ids:
        task_ids = list(
            (
                await db.scalars(
                    select(Task.id).where(
                        Task.project_id == project_id,
                        Task.assignee_id.in_(peer_ids),
                    )
                )
            ).all()
        )
    if can_view_tickets(acc) and peer_ids:
        ticket_ids = list(
            (
                await db.scalars(
                    select(Ticket.id).where(
                        Ticket.project_id == project_id,
                        Ticket.assignee_id.in_(peer_ids),
                    )
                )
            ).all()
        )
    return task_ids, ticket_ids


async def client_activity_condition(
    db: AsyncSession,
    acc: ProjectAccess,
    project_id: uuid.UUID,
) -> ColumnElement[bool]:
    """Return the SQL predicate limiting activity to what a client may see.

    Project-wide entries are always visible. Task/ticket entries follow the same
    assignee rule as the client task/ticket lists, so a client never sees a
    comment on a work item they cannot open. Callers must only use this for a
    client participant (``acc.client_access is not None``).
    """
    task_ids, ticket_ids = await client_visible_subject_ids(db, acc, project_id)
    conditions: list = [Activity.subject_type == "project"]
    if task_ids:
        conditions.append(
            and_(
                Activity.subject_type == "task",
                Activity.subject_id.in_(task_ids),
            )
        )
    if ticket_ids:
        conditions.append(
            and_(
                Activity.subject_type == "ticket",
                Activity.subject_id.in_(ticket_ids),
            )
        )
    return or_(*conditions)
