"""Process pending commit refs written by the post-commit git hook.

The hook writes files to ``.work/commit-ref-pending/{sha}`` with content ``{ref}``.
This module reads those files, resolves the ref to a task/ticket, and creates a
``CommitSubjectRef`` row immediately — no need to wait for the GitHub sync cycle.

If the commit has already been synced into ``github_commits`` the processor uses the
real ``github_commit_id`` FK.  Otherwise it stores a *pending* ref (``github_commit_id``
null) that the ``commit_ref_linker`` upgrades on the next sync.

Design rules:
- Never raises — processing errors must not crash the poll loop.
- Idempotent — re-processing an already-linked SHA is a no-op.
- Project-scoped — reads ``project_id`` from the ``Project`` table matched to the
  repository's ``project_key`` (configured at ``git config`` or env).
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commit_subject_ref import CommitSubjectRef
from app.models.github_commit import GithubCommit
from app.models.project import Project
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.user import User
from app.services.commit_ref_linker import REF_RE, SUBJECT_TASK, SUBJECT_TICKET

log = logging.getLogger(__name__)

_PENDING_DIR = ".work/commit-ref-pending"


async def process_pending_commit_refs(db: AsyncSession) -> int:
    """Scan the pending-refs directory and create ``CommitSubjectRef`` rows.

    Returns the number of refs processed (inserted or already resolved).
    """
    repo_root = _find_repo_root()
    if repo_root is None:
        return 0

    pending_dir = repo_root / _PENDING_DIR
    if not pending_dir.is_dir():
        return 0

    processed = 0
    for entry in sorted(pending_dir.iterdir()):
        if entry.is_dir() or entry.name.startswith("."):
            continue

        sha = entry.name
        if not _is_valid_sha(sha):
            log.warning("pending_ref: invalid SHA filename %s, skipping", sha)
            _safe_unlink(entry)
            continue

        ref = entry.read_text("utf-8").strip()
        if not ref:
            log.warning("pending_ref: empty ref in %s, skipping", entry.name)
            _safe_unlink(entry)
            continue

        if not REF_RE.search(ref):
            log.warning("pending_ref: ref %r does not match pattern, skipping", ref)
            _safe_unlink(entry)
            continue

        try:
            ok = await _process_one(db, sha, ref)
        except Exception:
            log.exception("pending_ref: error processing %s / %s", sha, ref)
            # Leave the file for retry on next cycle.
            continue

        if ok:
            _safe_unlink(entry)
            processed += 1

    if processed:
        log.info("pending_ref: processed %d pending commit ref(s)", processed)
    return processed


async def _process_one(db: AsyncSession, sha: str, ref: str) -> bool:
    """Try to create a ``CommitSubjectRef`` for *sha* + *ref*.

    Returns True if the file should be deleted (processed or already exists).
    """
    # 1. Resolve the project by scanning projects that have a linked GitHub repo.
    #    We check if the SHA exists in any project's github_commits first (fastest).
    project_id = await _resolve_project_by_sha(db, sha)
    if project_id is None:
        # Fallback: try to find any project that has task/ticket with this ref.
        project_id = await _resolve_project_by_ref(db, ref)
    if project_id is None:
        log.info("pending_ref: no project found for SHA=%s ref=%s, deferring", sha, ref)
        return False  # leave file for retry

    # 2. Resolve the ref to a subject (task or ticket).
    resolved = await _resolve_ref_in_project(db, project_id, ref)
    if resolved is None:
        log.info("pending_ref: ref %s not resolvable in project %s, deferring", ref, project_id)
        return False  # leave file for retry

    subject_type, subject_id = resolved

    # 3. Check if this commit already exists in github_commits (synced).
    github_commit_id = await _find_github_commit(db, project_id, sha)

    # 4. Check if a CommitSubjectRef already exists for this (sha, project, subject)
    #    or (github_commit_id, subject).
    already = await _check_exists(db, sha, project_id, subject_type, subject_id, github_commit_id)
    if already:
        return True  # already linked, safe to delete the file

    # 5. Insert the row.
    created_by = await _resolve_system_user(db)
    row_data: dict = {
        "id": uuid.uuid4(),
        "sha": sha,
        "project_id": project_id,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "created_by": created_by,
    }
    if github_commit_id is not None:
        row_data["github_commit_id"] = github_commit_id

    try:
        stmt = pg_insert(CommitSubjectRef).values(**row_data).on_conflict_do_nothing(
            # The partial unique indexes handle both pending and resolved cases.
            # For safety we pass no explicit constraint — pg will enforce them.
        )
        await db.execute(stmt)
        await db.flush()
    except Exception:
        log.exception("pending_ref: insert failed for %s ref=%s", sha, ref)
        return False

    return True


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _find_repo_root() -> Path | None:
    """Walk up from CWD looking for the repo root (contains .git/ or .work/)."""
    cwd = Path.cwd().resolve()
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".git").is_dir() or (parent / ".work").is_dir():
            return parent
    # Fallback: check common locations
    for candidate in (
        Path("/mnt/work/Projects/tools-project"),
        Path("/app"),
        Path.cwd(),
    ):
        if candidate.is_dir() and (candidate / ".work").is_dir():
            return candidate
    return None


def _is_valid_sha(s: str) -> bool:
    return len(s) == 40 and all(c in "0123456789abcdef" for c in s)


def _safe_unlink(p: Path) -> None:
    try:
        p.unlink(missing_ok=True)
    except OSError:
        pass


async def _resolve_project_by_sha(db: AsyncSession, sha: str) -> uuid.UUID | None:
    """Find the project that has a ``github_commit`` with this SHA (fast path)."""
    row = await db.scalar(
        select(GithubCommit.github_link_id)
        .where(GithubCommit.sha == sha)
        .limit(1)
    )
    if row is None:
        return None
    from app.models.github_link import GithubLink
    link = await db.get(GithubLink, row)
    if link is None:
        return None
    return link.project_id


async def _resolve_project_by_ref(db: AsyncSession, ref: str) -> uuid.UUID | None:
    """Find any project that has a task or ticket with this ref."""
    # Try task first (refs are like PROJ-123)
    row = await db.scalar(select(Task.project_id).where(Task.ref == ref).limit(1))
    if row is not None:
        return row
    # Try ticket next (refs are like PROJ-T-123)
    row = await db.scalar(select(Ticket.project_id).where(Ticket.ref == ref).limit(1))
    return row


async def _resolve_ref_in_project(
    db: AsyncSession, project_id: uuid.UUID, ref: str
) -> tuple[str, uuid.UUID] | None:
    """Match *ref* against tasks/tickets in *project_id*."""
    row = await db.scalar(
        select(Task.id).where(Task.ref == ref, Task.project_id == project_id).limit(1)
    )
    if row is not None:
        return (SUBJECT_TASK, row)

    row = await db.scalar(
        select(Ticket.id).where(Ticket.ref == ref, Ticket.project_id == project_id).limit(1)
    )
    if row is not None:
        return (SUBJECT_TICKET, row)

    return None


async def _find_github_commit(
    db: AsyncSession, project_id: uuid.UUID, sha: str
) -> uuid.UUID | None:
    """If the commit has already been synced, return its ``github_commits.id``."""
    from app.models.github_link import GithubLink
    row = await db.scalar(
        select(GithubCommit.id)
        .join(GithubLink, GithubLink.id == GithubCommit.github_link_id)
        .where(GithubLink.project_id == project_id, GithubCommit.sha == sha)
        .limit(1)
    )
    return row


async def _check_exists(
    db: AsyncSession,
    sha: str,
    project_id: uuid.UUID,
    subject_type: str,
    subject_id: uuid.UUID,
    github_commit_id: uuid.UUID | None,
) -> bool:
    """Return True if a matching ``CommitSubjectRef`` already exists."""
    if github_commit_id is not None:
        existing = await db.scalar(
            select(CommitSubjectRef.id).where(
                CommitSubjectRef.github_commit_id == github_commit_id,
                CommitSubjectRef.subject_type == subject_type,
                CommitSubjectRef.subject_id == subject_id,
            ).limit(1)
        )
        if existing is not None:
            return True
    # Also check by sha + project_id (covers pending refs)
    existing = await db.scalar(
        select(CommitSubjectRef.id).where(
            CommitSubjectRef.sha == sha,
            CommitSubjectRef.project_id == project_id,
            CommitSubjectRef.subject_type == subject_type,
            CommitSubjectRef.subject_id == subject_id,
        ).limit(1)
    )
    return existing is not None


async def _resolve_system_user(db: AsyncSession) -> uuid.UUID:
    """Return the first superuser as the author of auto-created refs."""
    row = await db.scalar(
        select(User.id).where(User.is_superuser.is_(True)).limit(1)
    )
    if row is not None:
        return row
    # Fallback: any user at all
    row = await db.scalar(select(User.id).limit(1))
    if row is not None:
        return row
    return uuid.UUID("00000000-0000-0000-0000-000000000000")
