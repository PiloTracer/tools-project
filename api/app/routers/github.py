"""GitHub repo links + cached commits (per project)."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Annotated

import httpx

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db import get_db
from app.deps import get_current_user
from app.models.activity import Activity
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
from app.services.activity_writer import write_activity
from app.services.github_sync import sync_github_link
from app.services.github_task_registry import empty_registry, fetch_registry
from app.services.github_token_crypto import decrypt_github_token, encrypt_github_token
from app.services.project_access import can_edit_project_meta, require_project_access

from datetime import timedelta

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

    # Create github_commit activity entries for new commits.
    for c in out.get("commits", []):
        if not c.get("is_new"):
            continue
        c_sha = c.get("sha", "")
        preview = (c["message"] or "").split("\n")[0][:100]
        body_md = f"{c_sha[:7]} {out['owner']}/{out['repo']} {preview}"
        meta: dict[str, object] = {
            "link_id": str(link_id),
            "sha": c_sha,
            "owner": str(out["owner"]),
            "repo": str(out["repo"]),
            "html_url": c.get("html_url", ""),
            "message_preview": preview,
            "full_message": c.get("message", ""),
        }
        if c.get("id"):
            meta["commit_id"] = c["id"]
        await write_activity(
            db=db,
            project_id=row.project_id,
            subject_type="project",
            subject_id=row.project_id,
            kind="github_commit",
            actor_id=None,
            body=body_md,
            meta_json=meta,
            is_internal=False,
        )

    row.last_synced_at = datetime.now(timezone.utc)
    row.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return GithubSyncResult(
        upserted=int(out["upserted"]),
        owner=str(out["owner"]),
        repo=str(out["repo"]),
        linked_refs=int(out.get("linked_refs") or 0),
    )


@router.post("/links/{link_id}/test")
async def test_github_link(
    project_id: uuid.UUID,
    link_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Test whether the GitHub token can access the repository.

    Makes a lightweight API call without syncing commits.
    Returns ``{ ok: true }`` or raises an appropriate HTTP error.
    """
    acc = await require_project_access(db, user, project_id)
    if not can_edit_project_meta(acc.role):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    row = await db.get(GithubLink, link_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Link not found")

    token = decrypt_github_token(row.token_cipher)
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"https://api.github.com/repos/{row.owner}/{row.repo}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=headers)
    if resp.status_code == 401:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token rejected by GitHub (401)")
    if resp.status_code == 403:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Token lacks access to this repository (403)")
    if resp.status_code == 404:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Repository not found (404)")
    resp.raise_for_status()
    data = resp.json()
    return {
        "ok": True,
        "repo": f"{row.owner}/{row.repo}",
        "private": data.get("private", False),
        "description": data.get("description") or "",
    }


@router.post("/sync-backfill")
async def sync_backfill(
    project_id: uuid.UUID,
    body: dict[str, object],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Re-sync all GitHub links for this project, looking back N days.

    Request body: { "since_days": 30 }
    Only owners and maintainers can trigger a backfill sync.
    Returns per-link results.
    """
    acc = await require_project_access(db, user, project_id)
    if not can_edit_project_meta(acc.role):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    since_days = body.get("since_days", 30)
    if not isinstance(since_days, int) or since_days < 1 or since_days > 365:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="since_days must be an integer between 1 and 365")

    cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=since_days)

    links = (await db.scalars(
        select(GithubLink).where(GithubLink.project_id == project_id)
    )).all()

    if not links:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No GitHub links configured for this project")

    results: list[dict[str, object]] = []
    for link in links:
        try:
            out = await sync_github_link(db, link.id, since=cutoff)
            commits = out.get("commits", [])
            shas = [c["sha"] for c in commits if isinstance(c.get("sha"), str)]

            if shas:
                existing = set()
                for row in await db.scalars(
                    select(Activity).where(
                        Activity.kind == "github_commit",
                        Activity.meta_json["sha"].as_string().in_(shas),
                    )
                ):
                    sha = (row.meta_json or {}).get("sha")
                    if isinstance(sha, str):
                        existing.add(sha)

                for c in commits:
                    sha = c.get("sha")
                    if not isinstance(sha, str) or sha in existing:
                        continue
                    preview = (c["message"] or "").split("\n")[0][:100]
                    commit_id_uuid = c.get("id")
                    body_md = f"{sha[:7]} {out['owner']}/{out['repo']} {preview}"
                    meta: dict[str, object] = {
                        "link_id": str(link.id),
                        "sha": sha,
                        "owner": out["owner"],
                        "repo": out["repo"],
                        "html_url": c["html_url"],
                        "message_preview": preview,
                        "full_message": c["message"],
                    }
                    if commit_id_uuid:
                        meta["commit_id"] = commit_id_uuid
                    await write_activity(
                        db=db,
                        project_id=link.project_id,
                        subject_type="project",
                        subject_id=link.project_id,
                        kind="github_commit",
                        actor_id=None,
                        body=body_md,
                        meta_json=meta,
                        is_internal=False,
                    )

            await db.commit()
            results.append({
                "owner": out["owner"],
                "repo": out["repo"],
                "upserted": int(out["upserted"]),
                "linked_refs": int(out.get("linked_refs") or 0),
            })
        except PermissionError as e:
            await db.rollback()
            results.append({"owner": link.owner, "repo": link.repo, "error": str(e)})
        except Exception as e:
            log.exception("backfill sync failed for %s/%s", link.owner, link.repo)
            await db.rollback()
            results.append({"owner": link.owner, "repo": link.repo, "error": str(e)})

    return {"results": results}


@router.get("/commits", response_model=GithubCommitListResponse)
async def list_github_commits(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    link_id: uuid.UUID | None = Query(default=None),
    q: str | None = Query(default=None),
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
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            GithubCommit.sha.ilike(like)
            | GithubCommit.message.ilike(like)
            | GithubLink.owner.ilike(like)
            | GithubLink.repo.ilike(like)
        )
    result = await db.execute(stmt)
    items = [_to_commit_summary(c, project_id, pname) for c, pname in result.all()]
    return GithubCommitListResponse(items=items)


@router.get("/task-registry", response_model=dict)
async def get_task_registry(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return the task/ticket registry from GitHub (.github/task-registry.json).

    The registry contains all tracked tasks and tickets with their refs,
    titles, and descriptions. The AI queries this to discover the correct
    task/ticket ref for commit messages by matching descriptions against
    changed files.

    No authentication required — the registry contains only metadata.
    Returns an empty registry if the feature is disabled or GitHub is
    unreachable — never blocks the caller.
    """
    proj = await db.get(Project, project_id)
    if not proj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")
    registry = await fetch_registry(db, project_id)
    if registry is None:
        return empty_registry()
    return registry


@router.get("/readiness")
async def github_readiness(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Check the project's readiness for commit↔task/ticket auto-association.

    Returns a checklist with ``met`` / ``unmet`` status per requirement.
    Each unmet item includes an ``action`` hint and, where possible,
    a direct ``api`` path the UI can call to fix it.
    """
    await require_project_access(db, user, project_id)
    proj = await db.get(Project, project_id)

    links = (
        await db.scalars(
            select(GithubLink).where(GithubLink.project_id == project_id)
        )
    ).all()

    has_link = len(links) > 0
    has_synced = any(l.last_synced_at is not None for l in links)

    checks: list[dict[str, object]] = [
        {
            "id": "project_key",
            "label": "Project key set",
            "met": bool(proj and proj.project_key),
            "action": "Set a project key in settings (e.g. PROJ) so task/ticket refs can be generated.",
            "api": f"/v1/projects/{project_id}",
        },
        {
            "id": "github_link",
            "label": "GitHub repository linked",
            "met": has_link,
            "action": "Add a GitHub repository link with a valid PAT.",
            "api": f"/v1/projects/{project_id}/github/links",
        },
        {
            "id": "commits_synced",
            "label": "Commits synced from GitHub",
            "met": has_synced,
            "action": "Sync the linked repository to pull in commit history.",
            "api": f"/v1/projects/{project_id}/github/links/{links[0].id}/sync" if has_link and links[0].id else None,
        },
        {
            "id": "registry_enabled",
            "label": "Task registry enabled",
            "met": bool(proj and proj.github_task_registry_enabled),
            "action": "Enable the GitHub task registry setting so task/ticket refs are pushed to the linked repo.",
            "api": f"/v1/projects/{project_id}",
        },
        {
            "id": "auto_prefix",
            "label": "Auto-prefix enabled",
            "met": bool(proj and proj.auto_prefix_enabled),
            "action": "Enable auto-prefix so new tasks/tickets get automatic refs (e.g. PROJ-123).",
            "api": f"/v1/projects/{project_id}",
        },
    ]

    met_count = sum(1 for c in checks if c["met"])
    total = len(checks)

    return {
        "ready": met_count == total,
        "score": f"{met_count}/{total}",
        "checks": checks,
    }


# Simple in-memory cache for token health checks (5 min TTL).
# Key: project_id, Value: (timestamp, result_dict)
_token_health_cache: dict[str, tuple[float, dict[str, object]]] = {}
_TOKEN_HEALTH_CACHE_TTL = 300  # 5 seconds → 300 seconds (5 minutes)


@router.get("/token-health")
async def github_token_health(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh: bool = Query(False),
):
    """Check whether the GitHub token(s) for this project are valid.

    Results are cached for 5 minutes to avoid hitting GitHub API rate
    limits on every page load. Pass ``?refresh=true`` to bypass cache.
    403 (rate limit) is reported as unknown rather than invalid — the
    sync path uses the same token and will surface real auth errors.
    """
    await require_project_access(db, user, project_id)

    pid = str(project_id)
    now = time.time()
    if not refresh:
        cached = _token_health_cache.get(pid)
        if cached and (now - cached[0]) < _TOKEN_HEALTH_CACHE_TTL:
            return cached[1]

    links = (
        await db.scalars(
            select(GithubLink).where(GithubLink.project_id == project_id)
        )
    ).all()

    results: list[dict[str, object]] = []
    for link in links:
        entry: dict[str, object] = {
            "link_id": str(link.id),
            "owner": link.owner,
            "repo": link.repo,
        }
        try:
            token = decrypt_github_token(link.token_cipher)
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"https://api.github.com/repos/{link.owner}/{link.repo}",
                    headers=headers,
                )
            if resp.status_code == 401:
                entry["ok"] = False
                entry["error"] = "Token is invalid or expired"
            elif resp.status_code == 403:
                if link.last_synced_at is not None:
                    entry["ok"] = True
                    entry["info"] = "Rate limited — syncs have succeeded before"
                else:
                    entry["ok"] = False
                    entry["error"] = "Rate limited and never synced"
            elif resp.status_code == 404:
                entry["ok"] = False
                entry["error"] = "Repository not found"
            elif resp.is_success:
                entry["ok"] = True
            else:
                entry["ok"] = False
                entry["error"] = f"GitHub returned HTTP {resp.status_code}"
        except httpx.TimeoutException:
            log.warning("token health timeout for %s/%s", link.owner, link.repo)
            if link.last_synced_at is not None:
                entry["ok"] = True
                entry["info"] = "Timed out — syncs have succeeded before"
            else:
                entry["ok"] = False
                entry["error"] = "GitHub API timed out"
        except Exception as exc:
            log.warning("token health exception for %s/%s: %s", link.owner, link.repo, exc)
            if link.last_synced_at is not None:
                entry["ok"] = True
                entry["info"] = f"Validation check failed — syncs have succeeded before"
            else:
                entry["ok"] = False
                entry["error"] = "Could not validate token"
        results.append(entry)

    result: dict[str, object] = {"links": results}
    _token_health_cache[pid] = (now, result)
    return result
