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
from app.models.project import Project
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas import (
    CommitBrief,
    CommitSubjectRefCreate,
    CommitSubjectRefListResponse,
    CommitSubjectRefOut,
    CommitSubjectRefPendingCreate,
)
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
    sha: str | None = Query(None, min_length=40, max_length=40),
):
    """List commit-subject references. Optionally filter by commit, subject, or SHA."""
    await require_project_access(db, user, project_id)
    stmt = (
        select(CommitSubjectRef)
        .options(
            joinedload(CommitSubjectRef.commit).joinedload(GithubCommit.link)
        )
        .where(CommitSubjectRef.project_id == project_id)
    )
    if github_commit_id:
        stmt = stmt.where(CommitSubjectRef.github_commit_id == github_commit_id)
    if subject_type:
        stmt = stmt.where(CommitSubjectRef.subject_type == subject_type)
    if subject_id:
        stmt = stmt.where(CommitSubjectRef.subject_id == subject_id)
    if sha:
        stmt = stmt.where(CommitSubjectRef.sha == sha)
    stmt = stmt.order_by(CommitSubjectRef.created_at.desc())
    rows = (await db.scalars(stmt)).all()

    items: list[CommitSubjectRefOut] = []
    for r in rows:
        d = CommitSubjectRefOut(
            id=r.id,
            github_commit_id=r.github_commit_id,
            sha=r.sha,
            project_id=r.project_id,
            subject_type=r.subject_type,
            subject_id=r.subject_id,
            created_by=r.created_by,
            created_at=r.created_at,
            commit=None,
        )
        if r.commit:
            msg = r.commit.message or ""
            d.commit = CommitBrief(
                sha=r.commit.sha,
                short_sha=r.commit.sha[:7],
                message_preview=msg[:120] + "…" if len(msg) > 120 else msg,
                html_url=r.commit.html_url,
                author_name=r.commit.author_name,
                committed_at=r.commit.committed_at,
                owner=r.commit.link.owner,
                repo=r.commit.link.repo,
            )
        items.append(d)

    return CommitSubjectRefListResponse(items=items)


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
        sha=commit.sha,
        project_id=project_id,
        subject_type=body.subject_type,
        subject_id=body.subject_id,
        created_by=user.id,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return CommitSubjectRefOut(
        id=row.id,
        github_commit_id=row.github_commit_id,
        sha=row.sha,
        project_id=row.project_id,
        subject_type=row.subject_type,
        subject_id=row.subject_id,
        created_by=row.created_by,
        created_at=row.created_at,
        commit=None,
    )


@router.post("/pending", status_code=status.HTTP_201_CREATED)
async def create_pending_commit_ref(
    project_id: uuid.UUID,
    body: CommitSubjectRefPendingCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a pending commit-subject reference for a commit that hasn't synced yet.

    This is called by a custom post-receive hook or CI pipeline to link a local
    commit SHA + ref immediately, before GitHub sync brings it into ``github_commits``.
    The row's ``github_commit_id`` is set later when the background sync resolves
    the SHA.

    The ref is automatically resolved to a task or ticket in this project.
    """
    await require_project_access(db, user, project_id)

    # Verify the SHA is valid (40 hex chars — already validated by the schema)
    sha = body.sha.strip().lower()

    # Check if this commit already exists in github_commits (fast path).
    commit = await db.scalar(
        select(GithubCommit.id)
        .join(GithubLink, GithubLink.id == GithubCommit.github_link_id)
        .where(GithubLink.project_id == project_id, GithubCommit.sha == sha)
        .limit(1)
    )

    # Resolve the ref to a task or ticket.
    subject_type: str | None = None
    subject_id: uuid.UUID | None = None
    ref = body.ref.strip()

    task = await db.scalar(
        select(Task.id).where(Task.ref == ref, Task.project_id == project_id).limit(1)
    )
    if task is not None:
        subject_type = "task"
        subject_id = task
    else:
        ticket = await db.scalar(
            select(Ticket.id).where(Ticket.ref == ref, Ticket.project_id == project_id).limit(1)
        )
        if ticket is not None:
            subject_type = "ticket"
            subject_id = ticket

    if subject_type is None or subject_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Ref {ref} does not match any task or ticket in this project",
        )

    # Check for existing ref (by github_commit_id or by sha+project_id).
    if commit is not None:
        existing = await db.scalar(
            select(CommitSubjectRef.id).where(
                CommitSubjectRef.github_commit_id == commit,
                CommitSubjectRef.subject_type == subject_type,
                CommitSubjectRef.subject_id == subject_id,
            ).limit(1)
        )
    else:
        existing = await db.scalar(
            select(CommitSubjectRef.id).where(
                CommitSubjectRef.github_commit_id.is_(None),
                CommitSubjectRef.sha == sha,
                CommitSubjectRef.project_id == project_id,
                CommitSubjectRef.subject_type == subject_type,
                CommitSubjectRef.subject_id == subject_id,
            ).limit(1)
        )

    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Reference already exists for this commit + subject",
        )

    row = CommitSubjectRef(
        github_commit_id=commit,  # None if not yet synced
        sha=sha,
        project_id=project_id,
        subject_type=subject_type,
        subject_id=subject_id,
        created_by=user.id,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return CommitSubjectRefOut(
        id=row.id,
        github_commit_id=row.github_commit_id,
        sha=row.sha,
        project_id=row.project_id,
        subject_type=row.subject_type,
        subject_id=row.subject_id,
        created_by=row.created_by,
        created_at=row.created_at,
        commit=None,
    )


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
    if row is None or row.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Reference not found")
    await db.delete(row)
    await db.flush()
