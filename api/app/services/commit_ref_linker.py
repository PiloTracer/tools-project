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
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commit_subject_ref import CommitSubjectRef
from app.models.github_link import GithubLink
from app.models.task import Task
from app.models.ticket import Ticket
from app.services.github_task_registry import fetch_registry

log = logging.getLogger(__name__)

SUBJECT_TASK = "task"
SUBJECT_TICKET = "ticket"

REF_RE = re.compile(r"\b[A-Z][A-Z0-9_]*-(?:T-)?\d+\b")


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
            out[ref] = (SUBJECT_TASK, tid)

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
                out[ref] = (SUBJECT_TICKET, tid)

    return out


async def link_commit_refs(
    db: AsyncSession,
    link: GithubLink,
    commit_pairs: list[tuple[uuid.UUID, str, str]],
    author_id: uuid.UUID | None = None,
) -> int:
    """Auto-create ``commit_subject_refs`` for refs found in commit messages.

    Args:
        db: active async session (same one performing the sync upserts).
        link: the GitHub link the commits belong to (scopes project + author).
        commit_pairs: list of ``(commit_id, sha, message)`` for newly-synced commits.
        author_id: optional author override; defaults to ``link.created_by``.

    Returns the number of ref rows inserted (duplicates skipped via ON CONFLICT).
    Never raises — sync must always succeed even if linking fails.
    """
    if not commit_pairs:
        return 0
    try:
        project_id = link.project_id
        created_by = author_id if author_id is not None else link.created_by
        now = datetime.now(timezone.utc)

        # Collect every ref across all messages, then resolve in one batch.
        all_refs: list[str] = []
        for _cid, _sha, msg in commit_pairs:
            all_refs.extend(extract_refs(msg))
        if not all_refs:
            return 0

        resolved = await resolve_refs(db, project_id, all_refs)

        # Fallback: try the GitHub registry for any refs that didn't resolve
        # locally. The registry may have tickets created in other environments
        # (e.g. production). If found, create a stub ticket in this DB so the
        # link can be established.
        unmatched_refs = [r for r in all_refs if r not in resolved]
        if unmatched_refs:
            try:
                registry = await fetch_registry(db, project_id)
                if registry:
                    for entry in registry.get("tickets", []):
                        eref = entry.get("ref")
                        if eref in unmatched_refs:
                            existing = await db.scalar(
                                select(Ticket.id).where(Ticket.ref == eref).limit(1)
                            )
                            if existing is not None:
                                resolved[eref] = (SUBJECT_TICKET, existing)
                                unmatched_refs.remove(eref)
                            else:
                                stub = Ticket(
                                    id=uuid.uuid4(),
                                    project_id=project_id,
                                    ref=eref,
                                    title=entry.get("title", ""),
                                    description=entry.get("description"),
                                    status=entry.get("status", "open"),
                                    reporter_id=created_by,
                                )
                                db.add(stub)
                                await db.flush()
                                resolved[eref] = (SUBJECT_TICKET, stub.id)
                                unmatched_refs.remove(eref)
                    for entry in registry.get("tasks", []):
                        eref = entry.get("ref")
                        if eref in unmatched_refs:
                            existing = await db.scalar(
                                select(Task.id).where(Task.ref == eref).limit(1)
                            )
                            if existing is not None:
                                resolved[eref] = (SUBJECT_TASK, existing)
                            else:
                                stub = Task(
                                    id=uuid.uuid4(),
                                    project_id=project_id,
                                    ref=eref,
                                    title=entry.get("title", ""),
                                    description=entry.get("description"),
                                    status=entry.get("status", "todo"),
                                    reporter_id=created_by,
                                )
                                db.add(stub)
                                await db.flush()
                                resolved[eref] = (SUBJECT_TASK, stub.id)
            except Exception:
                log.warning("commit_ref_linker: registry fallback failed, continuing without stub")

        if not resolved:
            return 0

        # Step 1: resolve any pending refs (created by post-commit hook) that
        # match the newly synced SHAs — upgrade them with the real github_commit_id.
        new_shas = [sha for _cid, sha, _msg in commit_pairs]
        pending_map: dict[str, list[CommitSubjectRef]] = {}
        if new_shas:
            pending_rows = await db.scalars(
                select(CommitSubjectRef).where(
                    CommitSubjectRef.github_commit_id.is_(None),
                    CommitSubjectRef.project_id == project_id,
                    CommitSubjectRef.sha.in_(new_shas),
                )
            )
            for pr in pending_rows.all():
                pending_map.setdefault(pr.sha, []).append(pr)

        # Step 2: build rows for new links (skip if a pending row already covers it).
        rows: list[dict[str, Any]] = []
        for commit_id, sha, msg in commit_pairs:
            existing_pending = pending_map.get(sha, [])
            pending_subjects = {(r.subject_type, r.subject_id) for r in existing_pending}

            for ref in extract_refs(msg):
                hit = resolved.get(ref)
                if hit is None:
                    continue
                subject_type, subject_id = hit
                # Skip if a pending ref already covers this commit+subject.
                if (subject_type, subject_id) in pending_subjects:
                    continue
                rows.append(
                    {
                        "id": uuid.uuid4(),
                        "github_commit_id": commit_id,
                        "sha": sha,
                        "project_id": project_id,
                        "subject_type": subject_type,
                        "subject_id": subject_id,
                        "created_by": created_by,
                        "created_at": now,
                    }
                )

        # Step 3: upgrade pending refs with the real github_commit_id.
        for sha, pending_list in pending_map.items():
            # Find the commit_id for this SHA from the new commits.
            match_id = None
            for cid, csha, _cmsg in commit_pairs:
                if csha == sha:
                    match_id = cid
                    break
            if match_id is not None:
                for pr in pending_list:
                    pr.github_commit_id = match_id
                    db.add(pr)

        await db.flush()

        if not rows:
            return 0

        linked = 0
        for row_data in rows:
            stmt = pg_insert(CommitSubjectRef).values(**row_data).on_conflict_do_nothing()
            r = await db.execute(stmt)
            if r.rowcount:
                linked += 1
        await db.flush()

        if linked:
            log.info(
                "commit_ref_linker: linked %d ref(s) for link %s (%s/%s)",
                linked, link.id, link.owner, link.repo,
            )
        return linked
    except Exception:
        log.exception("commit_ref_linker: failed for link %s; sync continues", link.id)
        return 0
