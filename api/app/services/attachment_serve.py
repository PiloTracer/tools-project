"""Shared attachment access + serving rules (web JWT route and agent route).

SPEC amendment 01 §R7 / §I3–I7: attachments are served only after an access
check on their own project, internal-note files and files on subjects a client
participant cannot see are 404 (never 403-with-details), the stored mime is
re-validated against the upload allowlist, and the bytes are streamed with
`nosniff` / `CSP: sandbox` / `no-store` headers. `storage_key` never leaves the
server; `path_for_key` rejects traversal.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.attachment import Attachment
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.services.attachment_storage import path_for_key
from app.services.file_sniff import ALLOWED_MIMES
from app.services.project_access import (
    ProjectAccess,
    can_view_tasks,
    can_view_tickets,
    client_company_user_ids,
    is_client_participant,
    require_project_access,
)

_NOT_FOUND = "attachment_not_found"


def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)


async def is_attachment_visible(
    db: AsyncSession,
    acc: ProjectAccess,
    row: Attachment,
) -> bool:
    """Return whether this caller may see the attachment's metadata and bytes.

    Staff always may (project access is checked by the caller). For client
    participants the rule mirrors the web lists and activity feed: project-wide
    files are visible, files on a ticket/task are visible only when the subject
    is assigned to the participant's company, and internal-note files never are.
    """
    if not is_client_participant(acc):
        return True

    peer_ids = await client_company_user_ids(db, acc)
    if not peer_ids:
        return False

    subject_type: str | None = None
    subject_id: uuid.UUID | None = None

    if row.activity_id is not None:
        activity = await db.get(Activity, row.activity_id)
        if activity is None:
            return False
        if activity.is_internal:
            return False
        subject_type, subject_id = activity.subject_type, activity.subject_id
    elif row.ticket_id is not None:
        subject_type, subject_id = "ticket", row.ticket_id
    elif row.task_id is not None:
        subject_type, subject_id = "task", row.task_id
    else:
        # Project-level attachment: project access was already checked.
        return True

    if subject_type == "project" or subject_id is None:
        return True
    if subject_type == "ticket":
        if not can_view_tickets(acc):
            return False
        ticket = await db.get(Ticket, subject_id)
        return ticket is not None and ticket.assignee_id in peer_ids
    if subject_type == "task":
        if not can_view_tasks(acc):
            return False
        task = await db.get(Task, subject_id)
        return task is not None and task.assignee_id in peer_ids
    return False


async def resolve_attachment(
    db: AsyncSession,
    user: User,
    attachment_id: uuid.UUID,
) -> tuple[Attachment, ProjectAccess]:
    """Load an attachment for a caller or raise the single opaque 404.

    Every failure — unknown id, missing project, foreign tenant, hidden subject —
    is reported as `attachment_not_found` so existence never leaks.
    """
    row = await db.get(Attachment, attachment_id)
    if row is None:
        raise _not_found()

    try:
        acc = await require_project_access(db, user, row.project_id)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            raise _not_found() from None
        raise

    if not await is_attachment_visible(db, acc, row):
        raise _not_found()

    return row, acc


def attachment_path(row: Attachment) -> Path:
    """Resolve the on-disk file, rejecting traversal and missing files with a 404."""
    try:
        path = path_for_key(row.storage_key)
    except ValueError:
        raise _not_found() from None
    if not path.is_file():
        raise _not_found()
    return path


def content_disposition_filename(name: str) -> str:
    """Sanitize a stored filename for the Content-Disposition header."""
    cleaned = name.replace("\r", " ").replace("\n", " ").replace('"', "").strip()
    return (cleaned or "attachment")[:200]


def serve_attachment(row: Attachment, *, download: bool = False) -> FileResponse:
    """Stream the stored bytes with the SPEC R7 headers (no ETag)."""
    if row.mime not in ALLOWED_MIMES:
        raise _not_found()

    path = attachment_path(row)
    try:
        stat_result = path.stat()
    except OSError:
        raise _not_found() from None

    response = FileResponse(
        path,
        stat_result=stat_result,
        media_type=row.mime,
        filename=content_disposition_filename(row.filename),
        content_disposition_type="attachment" if download else "inline",
    )
    response.headers["Cache-Control"] = "private, max-age=0, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "sandbox"
    response.headers["Referrer-Policy"] = "no-referrer"
    if "etag" in response.headers:  # SPEC R7: no validators in 1.1.0
        del response.headers["etag"]
    return response
