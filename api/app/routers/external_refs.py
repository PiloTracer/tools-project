from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.commit_subject_ref import CommitSubjectRef
from app.models.user import User
from app.services.activity_writer import write_activity
from app.services.project_access import require_project_access

router = APIRouter(prefix="/v1/projects/{project_id}/external-refs", tags=["external-refs"])


class CommitSubjectRefCreate(BaseModel):
    source_app: str = Field(min_length=1, max_length=30)
    external_id: str = Field(min_length=1, max_length=200)
    external_url: str | None = Field(default=None, max_length=2000)
    label: str | None = Field(default=None, max_length=200)
    subject_type: str = Field(min_length=1, max_length=40)
    subject_id: uuid.UUID


class CommitSubjectRefOut(BaseModel):
    id: uuid.UUID
    source_app: str
    external_id: str
    external_url: str | None
    label: str | None
    subject_type: str
    subject_id: uuid.UUID
    created_by: uuid.UUID


class CommitSubjectRefList(BaseModel):
    items: list[CommitSubjectRefOut]


@router.post("", response_model=CommitSubjectRefOut, status_code=status.HTTP_201_CREATED)
async def create_external_ref(
    project_id: uuid.UUID,
    body: CommitSubjectRefCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await require_project_access(db, user, project_id)
    ref = CommitSubjectRef(
        source_app=body.source_app,
        subject_type=body.subject_type,
        subject_id=body.subject_id,
        external_id=body.external_id,
        external_url=body.external_url,
        label=body.label,
        sha=body.external_id[:40],
        project_id=project_id,
        created_by=user.id,
    )
    db.add(ref)
    await db.flush()
    await db.refresh(ref)

    display_label = body.label or body.external_id
    await write_activity(
        db=db,
        project_id=project_id,
        subject_type=body.subject_type,
        subject_id=body.subject_id,
        kind="system",
        actor_id=user.id,
        body=f"Linked external reference from {body.source_app}: {display_label}",
        meta_json={
            "external_ref_id": str(ref.id),
            "source_app": body.source_app,
            "external_id": body.external_id,
            "external_url": body.external_url,
        },
        is_internal=True,
    )
    await db.commit()
    await db.refresh(ref)
    return CommitSubjectRefOut(
        id=ref.id,
        source_app=ref.source_app,
        external_id=ref.external_id or "",
        external_url=ref.external_url,
        label=ref.label,
        subject_type=ref.subject_type,
        subject_id=ref.subject_id,
        created_by=ref.created_by,
    )


@router.get("", response_model=CommitSubjectRefList)
async def list_external_refs(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    subject_type: str | None = None,
    subject_id: uuid.UUID | None = None,
):
    await require_project_access(db, user, project_id)
    base = select(CommitSubjectRef).where(CommitSubjectRef.project_id == project_id)
    if subject_type:
        base = base.where(CommitSubjectRef.subject_type == subject_type)
    if subject_id:
        base = base.where(CommitSubjectRef.subject_id == subject_id)
    rows = (await db.execute(base.order_by(CommitSubjectRef.created_at.desc()))).scalars().all()
    return CommitSubjectRefList(items=[
        CommitSubjectRefOut(
            id=r.id, source_app=r.source_app, external_id=r.external_id or "",
            external_url=r.external_url, label=r.label,
            subject_type=r.subject_type, subject_id=r.subject_id,
            created_by=r.created_by,
        )
        for r in rows
    ])


@router.delete("/{ref_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_external_ref(
    project_id: uuid.UUID,
    ref_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await require_project_access(db, user, project_id)
    row = await db.scalar(
        select(CommitSubjectRef).where(
            CommitSubjectRef.id == ref_id,
            CommitSubjectRef.project_id == project_id,
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="External ref not found")
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
