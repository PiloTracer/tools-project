"""GitHub task/ticket registry via Contents API.

Manages a lightweight `.github/task-registry.json` file in the project's
linked GitHub repo. The AI queries this registry to discover the correct
task/ticket ref for commit messages.

Optional — gated by ``project.github_task_registry_enabled``.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_link import GithubLink
from app.models.project import Project
from app.services.github_token_crypto import decrypt_github_token

log = logging.getLogger(__name__)

REGISTRY_PATH = ".github/task-registry.json"
MAX_RETRIES = 3
RETRY_DELAY_S = 0.5

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _empty_registry() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": datetime.now(UTC).isoformat(),
        "tasks": [],
        "tickets": [],
    }


# Public alias used by routers / API responses.
empty_registry = _empty_registry


def _entry(ref: str, title: str, status: str, project_id: uuid.UUID, description: str | None = None) -> dict[str, str]:
    entry: dict[str, str] = {
        "ref": ref,
        "title": title,
        "status": status,
        "project_id": str(project_id),
    }
    if description:
        entry["description"] = description
    return entry


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def _auth_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def _first_link(db: AsyncSession, project_id: uuid.UUID) -> GithubLink | None:
    """Return the first GitHub link for *project_id* (cheapest)."""
    row = await db.scalar(
        select(GithubLink)
        .where(GithubLink.project_id == project_id)
        .limit(1)
    )
    return row


async def _read_registry(
    owner: str, repo: str, token: str,
) -> tuple[dict[str, Any], str | None]:
    """Fetch the current registry file + its SHA.

    Returns ``(registry_dict, sha)``.  If the file does not exist yet,
    ``registry_dict`` is the default empty registry and *sha* is ``None``.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{REGISTRY_PATH}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=_auth_headers(token))
    if resp.status_code == 404:
        return _empty_registry(), None
    if resp.status_code == 403:
        log.warning("GitHub API 403 reading registry; may be rate-limited")
        return _empty_registry(), None
    resp.raise_for_status()
    data = resp.json()
    sha: str | None = data.get("sha")
    raw = data.get("content", "")
    try:
        decoded = base64.b64decode(raw).decode("utf-8")
        registry = json.loads(decoded)
    except Exception:
        log.exception("Failed to decode registry file; resetting")
        return _empty_registry(), sha
    return registry, sha


async def _write_registry(
    owner: str, repo: str, token: str,
    registry: dict[str, Any], sha: str | None,
    commit_msg: str,
) -> None:
    """Write (or create) the registry file via Contents API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{REGISTRY_PATH}"
    registry["updated_at"] = datetime.now(UTC).isoformat()
    raw = json.dumps(registry, indent=2, ensure_ascii=False)
    payload: dict[str, object] = {
        "message": commit_msg,
        "content": base64.b64encode(raw.encode("utf-8")).decode("ascii"),
    }
    if sha:
        payload["sha"] = sha
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.put(url, json=payload, headers=_auth_headers(token))
    if resp.status_code == 409:
        raise ValueError("Registry file conflict (SHA mismatch); retry")
    if resp.status_code == 422:
        raise ValueError(f"GitHub rejected registry write: {resp.json()}")
    resp.raise_for_status()


async def _update_registry(
    db: AsyncSession,
    project_id: uuid.UUID,
    mutator: Any,  # callable(registry) -> str | None (commit msg, or None to skip)
) -> bool:
    """Idempotent registry update with optimistic-lock retry.

    Returns ``True`` if the registry was updated.
    """
    link = await _first_link(db, project_id)
    if link is None:
        log.warning("skip registry – no GitHub link for project %s", project_id)
        return False

    proj = await db.get(Project, project_id)
    if proj is None or not proj.github_task_registry_enabled:
        return False

    token = decrypt_github_token(link.token_cipher)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            registry, sha = await _read_registry(link.owner, link.repo, token)
            commit_msg = mutator(registry)
            if commit_msg is None:
                return True
            await _write_registry(link.owner, link.repo, token, registry, sha, commit_msg)
            return True
        except ValueError as e:
            if "conflict" in str(e).lower() and attempt < MAX_RETRIES:
                log.warning("registry conflict, retry %d/%d", attempt, MAX_RETRIES)
                await asyncio.sleep(RETRY_DELAY_S)
                continue
            log.error("registry write failed: %s", e)
            return False
        except Exception:
            log.exception("registry update failed")
            return False

    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def push_task_ref(
    db: AsyncSession,
    project_id: uuid.UUID,
    ref: str,
    title: str,
    status: str,
    description: str | None = None,
) -> bool:
    """Add or update a task entry in the GitHub registry."""
    def _mutate(registry: dict[str, Any]) -> str | None:
        tasks = registry.setdefault("tasks", [])
        for t in tasks:
            if t.get("ref") == ref:
                if t.get("title") == title and t.get("status") == status:
                    return None
                t.update(title=title, status=status, project_id=str(project_id))
                if description:
                    t["description"] = description
                return f"registry: update task {ref}"
        tasks.append(_entry(ref, title, status, project_id, description))
        return f"registry: add task {ref}"
    return await _update_registry(db, project_id, _mutate)


async def push_ticket_ref(
    db: AsyncSession,
    project_id: uuid.UUID,
    ref: str,
    title: str,
    status: str,
    description: str | None = None,
) -> bool:
    """Add or update a ticket entry in the GitHub registry."""
    def _mutate(registry: dict[str, Any]) -> str | None:
        tickets = registry.setdefault("tickets", [])
        for t in tickets:
            if t.get("ref") == ref:
                if t.get("title") == title and t.get("status") == status:
                    return None
                t.update(title=title, status=status, project_id=str(project_id))
                if description:
                    t["description"] = description
                return f"registry: update ticket {ref}"
        tickets.append(_entry(ref, title, status, project_id, description))
        return f"registry: add ticket {ref}"
    return await _update_registry(db, project_id, _mutate)


async def remove_ref(
    db: AsyncSession,
    project_id: uuid.UUID,
    ref: str,
) -> bool:
    """Remove a task or ticket ref from the GitHub registry."""
    def _mutate(registry: dict[str, Any]) -> str | None:
        removed = False
        for key in ("tasks", "tickets"):
            before = len(registry.get(key, []))
            registry[key] = [e for e in registry.get(key, []) if e.get("ref") != ref]
            if len(registry[key]) < before:
                removed = True
        return f"registry: remove ref {ref}" if removed else None
    return await _update_registry(db, project_id, _mutate)


async def fetch_registry(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Fetch the current registry from GitHub.

    Returns ``None`` if the feature is disabled, no GitHub link is
    configured, or the registry is unreachable.
    """
    link = await _first_link(db, project_id)
    if link is None:
        return None
    proj = await db.get(Project, project_id)
    if proj is None or not proj.github_task_registry_enabled:
        return None
    try:
        token = decrypt_github_token(link.token_cipher)
        registry, _sha = await _read_registry(link.owner, link.repo, token)
        return registry
    except Exception:
        log.exception("fetch_registry failed")
        return None


# ---------------------------------------------------------------------------
# Background helpers (own session — safe for fire-and-forget)
# ---------------------------------------------------------------------------

# Strong references so scheduled tasks are not garbage-collected mid-flight.
_BG_TASKS: set[asyncio.Task] = set()


async def _background_push_task_ref(
    project_id: uuid.UUID,
    ref: str,
    title: str,
    status: str,
    description: str | None = None,
) -> None:
    """Fire-and-forget wrapper — creates its own DB session. Never raises."""
    from app.db import session_factory
    try:
        async with session_factory()() as db:
            await push_task_ref(db, project_id, ref, title, status, description)
    except Exception:
        log.exception("background push_task_ref failed for %s", ref)


async def _background_push_ticket_ref(
    project_id: uuid.UUID,
    ref: str,
    title: str,
    status: str,
    description: str | None = None,
) -> None:
    """Fire-and-forget wrapper — creates its own DB session. Never raises."""
    from app.db import session_factory
    try:
        async with session_factory()() as db:
            await push_ticket_ref(db, project_id, ref, title, status, description)
    except Exception:
        log.exception("background push_ticket_ref failed for %s", ref)


async def _background_remove_ref(
    project_id: uuid.UUID,
    ref: str,
) -> None:
    """Fire-and-forget wrapper — creates its own DB session. Never raises."""
    from app.db import session_factory
    try:
        async with session_factory()() as db:
            await remove_ref(db, project_id, ref)
    except Exception:
        log.exception("background remove_ref failed for %s", ref)


def _spawn(coro: Any) -> None:
    """Schedule *coro* on the running loop, retaining a strong ref until done."""
    task = asyncio.ensure_future(coro)
    _BG_TASKS.add(task)
    task.add_done_callback(_BG_TASKS.discard)


def spawn_push_task_ref(
    project_id: uuid.UUID, ref: str, title: str, status: str,
    description: str | None = None,
) -> None:
    """Schedule a registry push for a task (fire-and-forget, never blocks)."""
    _spawn(_background_push_task_ref(project_id, ref, title, status, description))


def spawn_push_ticket_ref(
    project_id: uuid.UUID, ref: str, title: str, status: str,
    description: str | None = None,
) -> None:
    """Schedule a registry push for a ticket (fire-and-forget, never blocks)."""
    _spawn(_background_push_ticket_ref(project_id, ref, title, status, description))


def spawn_remove_ref(project_id: uuid.UUID, ref: str) -> None:
    """Schedule a registry removal (fire-and-forget, never blocks)."""
    _spawn(_background_remove_ref(project_id, ref))
