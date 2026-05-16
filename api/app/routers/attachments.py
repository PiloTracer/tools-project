from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.config import get_settings
from app.models.attachment import Attachment
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas import AttachmentOut
from app.services.attachment_storage import path_for_key
from app.services.file_sniff import ALLOWED_MIMES, MIME_TO_EXT, sniff_file_mime
from app.services.project_access import can_mutate_tasks, require_project_access

MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024
_MAX_ATTACHMENTS_PER_PROJECT = 500

router = APIRouter(
    prefix="/v1/projects/{project_id}/attachments",
    tags=["attachments"],
)
ticket_router = APIRouter(
    prefix="/v1/projects/{project_id}/tickets/{ticket_id}/attachments",
    tags=["attachments"],
)
task_router = APIRouter(
    prefix="/v1/projects/{project_id}/tasks/{task_id}/attachments",
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
    return await _upload_attachment(
        project_id, ticket_subject_id=ticket_id, task_subject_id=None,
        user=user, db=db, file=file,
    )


@task_router.post("", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_task_attachment(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: Annotated[UploadFile, File()],
):
    return await _upload_attachment(
        project_id, ticket_subject_id=None, task_subject_id=task_id,
        user=user, db=db, file=file,
    )


async def _upload_attachment(
    project_id: uuid.UUID,
    *,
    ticket_subject_id: uuid.UUID | None,
    task_subject_id: uuid.UUID | None,
    user: User,
    db: AsyncSession,
    file: UploadFile,
):
    acc = await require_project_access(db, user, project_id)
    if not can_mutate_tasks(acc.role):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Viewers cannot upload attachments",
        )

    # Per-project soft quota (MVP; driven by ATTACHMENT_MAX_PER_PROJECT config, default 500)
    _max = get_settings().attachment_max_per_project or _MAX_ATTACHMENTS_PER_PROJECT
    current_count = int(
        await db.scalar(select(func.count(Attachment.id)).where(Attachment.project_id == project_id))
        or 0
    )
    if _max > 0 and current_count >= _max:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Project attachment limit reached ({_max} files per project)",
        )
    if ticket_subject_id is not None:
        row = await db.get(Ticket, ticket_subject_id)
        if row is None or row.project_id != project_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if task_subject_id is not None:
        row = await db.get(Task, task_subject_id)
        if row is None or row.project_id != project_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")

    raw = await _read_limited(file)
    if not raw:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Empty file")

    sniffed = sniff_file_mime(raw[:64])
    if sniffed is None or sniffed not in ALLOWED_MIMES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Only image/png, image/jpeg, image/gif, image/webp, application/pdf, text/plain are allowed",
        )

    ext = MIME_TO_EXT.get(sniffed, ".bin")
    storage_key = f"{uuid.uuid4().hex}{ext}"
    disk_path = path_for_key(storage_key)
    disk_path.write_bytes(raw)

    att = Attachment(
        project_id=project_id,
        ticket_id=ticket_subject_id,
        task_id=task_subject_id,
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


@router.post("", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: Annotated[UploadFile, File()],
):
    return await _upload_attachment(
        project_id, ticket_subject_id=None, task_subject_id=None,
        user=user, db=db, file=file,
    )


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
