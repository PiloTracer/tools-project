"""Normalized cross-link table for commit references (I10f).

Allows querying "which tasks/tickets reference this commit" and
powers watcher notifications when a commit is cited.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db import get_db
from app.deps import get_current_user
from app.models.commit_subject_ref import CommitSubjectRef
from app.models.github_commit import GithubCommit
from app.models.github_link import GithubLink
from app.models.user import User
from app.schemas import CommitSubjectRefCreate, CommitSubjectRefListResponse, CommitSubjectRefOut
from app.services.project_access import require_project_access

router = APIRouter(
    prefix="/v1/projects/{project_id}/github/refs",
    tags=["github"],
)


@router.get("", response_model=CommitSubjectRefListResponse)
async def list_commit_refs(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    github_commit_id: uuid.UUID | None = Query(None),
    subject_type: str | None = Query(None),
    subject_id: uuid.UUID | None = Query(None),
):
    """List commit-subject references. Optionally filter by commit, subject type, or subject id."""
    await require_project_access(db, user, project_id)
    stmt = select(CommitSubjectRef).options(joinedload(CommitSubjectRef.commit))
    if github_commit_id:
        stmt = stmt.where(CommitSubjectRef.github_commit_id == github_commit_id)
    if subject_type:
        stmt = stmt.where(CommitSubjectRef.subject_type == subject_type)
    if subject_id:
        stmt = stmt.where(CommitSubjectRef.subject_id == subject_id)
    stmt = stmt.order_by(CommitSubjectRef.created_at.desc())
    rows = (await db.scalars(stmt)).all()
    return CommitSubjectRefListResponse(
        items=[CommitSubjectRefOut.model_validate(r) for r in rows]
    )


@router.post("", response_model=CommitSubjectRefOut, status_code=status.HTTP_201_CREATED)
async def create_commit_ref(
    project_id: uuid.UUID,
    body: CommitSubjectRefCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a commit-subject reference. The commit must belong to this project."""
    await require_project_access(db, user, project_id)

    # Validate commit belongs to this project
    commit = await db.get(GithubCommit, body.github_commit_id)
    if commit is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Commit not found")
    link = await db.get(GithubLink, commit.github_link_id)
    if link is None or link.project_id != project_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Commit does not belong to this project",
        )

    # Check for duplicate
    existing = await db.scalar(
        select(CommitSubjectRef).where(
            CommitSubjectRef.github_commit_id == body.github_commit_id,
            CommitSubjectRef.subject_type == body.subject_type,
            CommitSubjectRef.subject_id == body.subject_id,
        )
    )
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Reference already exists for this commit + subject",
        )

    row = CommitSubjectRef(
        github_commit_id=body.github_commit_id,
        subject_type=body.subject_type,
        subject_id=body.subject_id,
        created_by=user.id,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return CommitSubjectRefOut.model_validate(row)


@router.delete("/{ref_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_commit_ref(
    project_id: uuid.UUID,
    ref_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a commit-subject reference."""
    await require_project_access(db, user, project_id)
    row = await db.get(CommitSubjectRef, ref_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Reference not found")
    await db.delete(row)
    await db.flush()
