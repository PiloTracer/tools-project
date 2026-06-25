"""Inbound commit → task/ticket linking (Gap #1).

When commits are synced from GitHub into ``github_commits``, their messages
often carry a task/ticket ref prefix (e.g. ``PROJ-456: Add login form`` or
``PROJ-T-23: Fix login``).  This module extracts those refs, resolves them to
task/ticket rows via ``tasks.ref`` / ``tickets.ref``, and writes idempotent
``commit_subject_refs`` rows so the app can answer "which commits touched this
task?".

Design notes:
- Refs are project-scoped: a ref only links when its task/ticket belongs to the
  same project as the GitHub link.
- Ticket refs use the ``{KEY}-T-{n}`` form; task refs use ``{KEY}-{n}``.
- Insertion is ``ON CONFLICT DO NOTHING`` on the
  ``(github_commit_id, subject_type, subject_id)`` unique constraint, so
  re-syncs never duplicate rows.
- Auto-linked rows are authored by the GitHub link's owner (``link.created_by``)
  — a real user, no schema change required.
- Linking never raises: a failure here must not break the sync.
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commit_subject_ref import CommitSubjectRef
from app.models.github_link import GithubLink
from app.models.task import Task
from app.models.ticket import Ticket

log = logging.getLogger(__name__)

# Matches PROJ-456 (task) and PROJ-T-23 (ticket).  Word-bounded, uppercase.
REF_RE = re.compile(r"\b[A-Z][A-Z0-9_]*-(?:T-)?\d+\b")

_SUBJECT_TASK = "task"
_SUBJECT_TICKET = "ticket"


def extract_refs(message: str) -> list[str]:
    """Return deduplicated refs found in *message*, in first-seen order."""
    if not message:
        return []
    seen: set[str] = set()
    refs: list[str] = []
    for m in REF_RE.findall(message):
        if m not in seen:
            seen.add(m)
            refs.append(m)
    return refs


async def resolve_refs(
    db: AsyncSession,
    project_id: uuid.UUID,
    refs: list[str],
) -> dict[str, tuple[str, uuid.UUID]]:
    """Batch-resolve refs to ``(subject_type, subject_id)`` within *project_id*.

    Returns a mapping ``ref -> ("task" | "ticket", id)``.  Refs that don't
    resolve to a task/ticket in this project are omitted.
    """
    if not refs:
        return {}
    unique_refs = list(dict.fromkeys(refs))  # dedupe, keep order

    out: dict[str, tuple[str, uuid.UUID]] = {}

    task_rows = await db.execute(
        select(Task.ref, Task.id).where(
            Task.ref.in_(unique_refs),
            Task.project_id == project_id,
        )
    )
    for ref, tid in task_rows.all():
        if ref is not None:
            out[ref] = (_SUBJECT_TASK, tid)

    remaining = [r for r in unique_refs if r not in out]
    if remaining:
        ticket_rows = await db.execute(
            select(Ticket.ref, Ticket.id).where(
                Ticket.ref.in_(remaining),
                Ticket.project_id == project_id,
            )
        )
        for ref, tid in ticket_rows.all():
            if ref is not None:
                out[ref] = (_SUBJECT_TICKET, tid)

    return out


async def link_commit_refs(
    db: AsyncSession,
    link: GithubLink,
    commit_pairs: list[tuple[uuid.UUID, str]],
    author_id: uuid.UUID | None = None,
) -> int:
    """Auto-create ``commit_subject_refs`` for refs found in commit messages.

    Args:
        db: active async session (same one performing the sync upserts).
        link: the GitHub link the commits belong to (scopes project + author).
        commit_pairs: list of ``(commit_id, message)`` for newly-synced commits.
        author_id: optional author override; defaults to ``link.created_by``.

    Returns the number of ref rows inserted (duplicates skipped via ON CONFLICT).
    Never raises — sync must always succeed even if linking fails.
    """
    if not commit_pairs:
        return 0
    try:
        project_id = link.project_id
        created_by = author_id if author_id is not None else link.created_by

        # Collect every ref across all messages, then resolve in one batch.
        all_refs: list[str] = []
        for _cid, msg in commit_pairs:
            all_refs.extend(extract_refs(msg))
        if not all_refs:
            return 0

        resolved = await resolve_refs(db, project_id, all_refs)
        if not resolved:
            return 0

        rows: list[dict[str, Any]] = []
        for commit_id, msg in commit_pairs:
            for ref in extract_refs(msg):
                hit = resolved.get(ref)
                if hit is None:
                    continue
                subject_type, subject_id = hit
                rows.append(
                    {
                        "id": uuid.uuid4(),
                        "github_commit_id": commit_id,
                        "subject_type": subject_type,
                        "subject_id": subject_id,
                        "created_by": created_by,
                    }
                )
        if not rows:
            return 0

        stmt = (
            pg_insert(CommitSubjectRef)
            .values(rows)
            .on_conflict_do_nothing(
                index_elements=["github_commit_id", "subject_type", "subject_id"]
            )
        )
        result = await db.execute(stmt)
        await db.flush()
        linked = result.rowcount or 0
        if linked:
            log.info(
                "commit_ref_linker: linked %d ref(s) for link %s (%s/%s)",
                linked, link.id, link.owner, link.repo,
            )
        return linked
    except Exception:
        log.exception("commit_ref_linker: failed for link %s; sync continues", link.id)
        return 0
