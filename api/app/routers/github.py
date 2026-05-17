"""GitHub repo links + cached commits (per project)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db import get_db
from app.deps import get_current_user
from app.models.github_commit import GithubCommit
from app.models.github_link import GithubLink
from app.models.project import Project
from app.models.user import User
from app.schemas import (
    CommitSummary,
    GithubCommitListResponse,
    GithubLinkCreate,
    GithubLinkOut,
    GithubSyncResult,
)
from app.services.github_sync import sync_github_link
from app.services.github_token_crypto import encrypt_github_token
from app.services.project_access import can_edit_project_meta, require_project_access

log = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/projects/{project_id}/github", tags=["github"])


def _message_preview(message: str, n: int = 120) -> str:
    if len(message) <= n:
        return message
    return message[:n] + "…"


def _to_commit_summary(c: GithubCommit, project_id: uuid.UUID, project_name: str) -> CommitSummary:
    link = c.link
    sha = c.sha
    short = sha[:7] if len(sha) >= 7 else sha
    msg = c.message or ""
    return CommitSummary(
        id=c.id,
        project_id=project_id,
        project_name=project_name,
        github_link_id=c.github_link_id,
        owner=link.owner,
        repo=link.repo,
        sha=sha,
        short_sha=short,
        message=msg,
        message_preview=_message_preview(msg),
        html_url=c.html_url,
        committed_at=c.committed_at,
        author_name=c.author_name,
        author_email=c.author_email,
    )


@router.get("/links", response_model=list[GithubLinkOut])
async def list_github_links(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await require_project_access(db, user, project_id)
    rows = (
        await db.scalars(
            select(GithubLink)
            .where(GithubLink.project_id == project_id)
            .order_by(GithubLink.created_at.desc())
        )
    ).all()
    return [GithubLinkOut.model_validate(r) for r in rows]


@router.post("/links", response_model=GithubLinkOut, status_code=status.HTTP_201_CREATED)
async def create_github_link(
    project_id: uuid.UUID,
    body: GithubLinkCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not can_edit_project_meta(acc.role):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only owners and maintainers can configure GitHub links",
        )
    now = datetime.now(timezone.utc)
    cipher = encrypt_github_token(body.github_token)
    row = GithubLink(
        project_id=project_id,
        component_id=body.component_id,
        owner=body.owner or "",
        repo=body.repo or "",
        token_cipher=cipher,
        poll_interval_seconds=body.poll_interval_seconds,
        created_by=user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="This repository is already linked to the project",
        ) from None
    try:
        await sync_github_link(db, row.id)
    except Exception as e:
        await db.rollback()
        if isinstance(e, PermissionError):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
        if isinstance(e, FileNotFoundError):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        if isinstance(e, ValueError):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        log.exception("initial github sync failed")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach GitHub or parse the response",
        ) from e
    await db.commit()
    await db.refresh(row)
    return GithubLinkOut.model_validate(row)


@router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_github_link(
    project_id: uuid.UUID,
    link_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not can_edit_project_meta(acc.role):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    row = await db.get(GithubLink, link_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Link not found")
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/links/{link_id}/sync", response_model=GithubSyncResult)
async def sync_github_link_route(
    project_id: uuid.UUID,
    link_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not can_edit_project_meta(acc.role):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    row = await db.get(GithubLink, link_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Link not found")
    try:
        out = await sync_github_link(db, link_id)
    except PermissionError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        log.exception("github sync failed")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach GitHub or parse the response",
        ) from e
    row.last_synced_at = datetime.now(timezone.utc)
    row.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return GithubSyncResult(
        upserted=int(out["upserted"]),
        owner=str(out["owner"]),
        repo=str(out["repo"]),
    )


@router.get("/commits", response_model=GithubCommitListResponse)
async def list_github_commits(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    link_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    await require_project_access(db, user, project_id)
    stmt = (
        select(GithubCommit, Project.name)
        .join(GithubLink, GithubLink.id == GithubCommit.github_link_id)
        .join(Project, Project.id == GithubLink.project_id)
        .where(GithubLink.project_id == project_id)
        .options(joinedload(GithubCommit.link))
        .order_by(GithubCommit.committed_at.desc())
        .limit(limit)
    )
    if link_id is not None:
        stmt = stmt.where(GithubCommit.github_link_id == link_id)
    result = await db.execute(stmt)
    items = [_to_commit_summary(c, project_id, pname) for c, pname in result.all()]
    return GithubCommitListResponse(items=items)
