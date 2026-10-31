"""Shared activity-feed filter and visibility rules.

The JWT project activity feed (`/v1/projects/{id}/activities`) and the agent
ticket feed (`/v1/agent/tickets/{ticket}/activities`, agent API 1.1.0) must
apply the same rules; this module is the single place where they are expressed
(SPEC amendment 01 §R6, C3).

Web behaviour preserved by the extraction:
- client participants see only non-internal activity on subjects assigned to
  their company (`client_activity_condition`);
- staff can filter `internal` / `external`;
- `kind` is normalized (legacy `note` → `comment`).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import ColumnElement, Select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.schemas import normalize_activity_kind
from app.services.activity_visibility import client_activity_condition
from app.services.project_access import ProjectAccess, is_client_participant

VISIBILITY_VALUES: frozenset[str] = frozenset({"internal", "external"})


def normalize_visibility(value: str | None) -> str | None:
    """Return `internal` / `external` / None (all), rejecting anything else."""
    if value is None:
        return None

    normalized = value.strip().lower()
    if normalized in ("", "all"):
        return None
    if normalized not in VISIBILITY_VALUES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="visibility must be 'internal', 'external' or 'all'",
        )
    return normalized


def assert_visibility_allowed(acc: ProjectAccess, visibility: str | None) -> None:
    """Internal notes are staff-only (same 403 as the web endpoint)."""
    if visibility == "internal" and is_client_participant(acc):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Client participants cannot view internal activities",
        )


async def activity_where_clauses(
    db: AsyncSession,
    acc: ProjectAccess,
    project_id: uuid.UUID,
    *,
    subject_type: str | None = None,
    subject_id: uuid.UUID | None = None,
    kind: str | None = None,
    visibility: str | None = None,
) -> list[ColumnElement[bool]]:
    """Return the shared WHERE clauses for an activity feed query.

    The caller composes `select(Activity).where(*clauses)`. Client-participant
    visibility always wins over the requested `visibility` value; callers must
    reject `visibility=internal` for clients with `assert_visibility_allowed`
    before building the query.
    """
    clauses: list[ColumnElement[bool]] = [Activity.project_id == project_id]

    if subject_type:
        clauses.append(Activity.subject_type == subject_type.strip().lower())
    if subject_id is not None:
        clauses.append(Activity.subject_id == subject_id)
    if kind is not None:
        clauses.append(Activity.kind == normalize_activity_kind(kind))

    normalized_visibility = normalize_visibility(visibility)
    if is_client_participant(acc):
        clauses.append(Activity.is_internal.is_(False))
        clauses.append(await client_activity_condition(db, acc, project_id))
    elif normalized_visibility == "internal":
        clauses.append(Activity.is_internal.is_(True))
    elif normalized_visibility == "external":
        clauses.append(Activity.is_internal.is_(False))

    return clauses


async def activity_count(db: AsyncSession, base: Select[Any]) -> int:
    """Count the rows a feed query matches, ignoring ordering and pagination."""
    total = await db.scalar(base.with_only_columns(func.count()).order_by(None))
    return int(total or 0)


def activity_order(order: str | None) -> ColumnElement[datetime]:
    """Newest-first by default; `asc` for chronological reading."""
    if order is not None and order.strip().lower() == "asc":
        return Activity.created_at.asc()
    return Activity.created_at.desc()


def activity_page(base: Select[Any], *, order: str | None, limit: int, offset: int) -> Select[Any]:
    """Apply ordering, offset and limit to a feed query."""
    return base.order_by(activity_order(order)).offset(offset).limit(limit)
