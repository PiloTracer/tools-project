"""Agent-facing binary attachment endpoint (SPEC amendment 01 §R7).

Read-only: streams the stored bytes after the same access checks as the web
download route — project access, subject visibility for client participants,
internal-note denial, storage-key traversal rejection and the upload-allowlist
mime re-check.
"""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_agent_superuser
from app.models.user import User
from app.services.attachment_serve import resolve_attachment, serve_attachment

router = APIRouter(prefix="/v1/agent", tags=["agent"])

log = logging.getLogger(__name__)


@router.get("/attachments/{attachment_id}")
async def agent_download_attachment(
    attachment_id: uuid.UUID,
    admin: Annotated[User, Depends(require_agent_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    download: bool = Query(
        default=False,
        description="Serve as an attachment instead of inline",
    ),
):
    """Stream an attachment's bytes for an authenticated agent."""
    try:
        row, _acc = await resolve_attachment(db, admin, attachment_id)
        response = serve_attachment(row, download=download)
    except HTTPException:
        log.warning("agent.attachment_read attachment_id=%s result=not_found", attachment_id)
        raise

    log.info(
        "agent.attachment_read attachment_id=%s project_id=%s bytes=%s mime=%s result=ok",
        row.id,
        row.project_id,
        row.size_bytes,
        row.mime,
    )
    return response
