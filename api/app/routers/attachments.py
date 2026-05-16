from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.attachment import Attachment
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas import AttachmentOut
from app.services.attachment_storage import path_for_key
from app.services.image_sniff import ALLOWED_IMAGE_MIMES, MIME_TO_EXT, sniff_image_mime
from app.services.project_access import can_mutate_tasks, require_project_access

MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024

ticket_router = APIRouter(
    prefix="/v1/projects/{project_id}/tickets/{ticket_id}/attachments",
    tags=["attachments"],
)
file_router = APIRouter(prefix="/v1/attachments", tags=["attachments"])


async def _read_limited(upload: UploadFile) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_ATTACHMENT_BYTES:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large (max {MAX_ATTACHMENT_BYTES} bytes)",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _safe_filename(name: str | None) -> str:
    base = (name or "image").strip() or "image"
    base = Path(base).name
    if not base or base in {".", ".."}:
        base = "image"
    return base[:500]


@ticket_router.post("", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_ticket_attachment(
    project_id: uuid.UUID,
    ticket_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: Annotated[UploadFile, File()],
):
    acc = await require_project_access(db, user, project_id)
    if not can_mutate_tasks(acc.role):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Viewers cannot upload attachments",
        )
    row = await db.get(Ticket, ticket_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    raw = await _read_limited(file)
    if not raw:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Empty file")

    sniffed = sniff_image_mime(raw[:32])
    if sniffed is None or sniffed not in ALLOWED_IMAGE_MIMES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Only image/png, image/jpeg, image/gif, image/webp are allowed",
        )

    ext = MIME_TO_EXT.get(sniffed, ".bin")
    storage_key = f"{uuid.uuid4().hex}{ext}"
    disk_path = path_for_key(storage_key)
    disk_path.write_bytes(raw)

    att = Attachment(
        project_id=project_id,
        ticket_id=ticket_id,
        activity_id=None,
        filename=_safe_filename(file.filename),
        mime=sniffed,
        size_bytes=len(raw),
        storage_key=storage_key,
        created_by=user.id,
    )
    db.add(att)
    await db.commit()
    await db.refresh(att)
    return AttachmentOut.model_validate(att)


@file_router.get("/{attachment_id}")
async def download_attachment(
    attachment_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Attachment, attachment_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    await require_project_access(db, user, row.project_id)
    try:
        path = path_for_key(row.storage_key)
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Attachment file missing")
    return FileResponse(
        path,
        media_type=row.mime,
        filename=row.filename,
        content_disposition_type="inline",
    )
