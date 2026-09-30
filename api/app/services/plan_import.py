"""Transactional plan-manifest import — the single bulk write path (plan-sync SPEC R5-R20).

Rules implemented here:
- R6 cross-field validation (dup refs, milestone_ref membership)
- R8 single transaction: caller commits only on success; dry_run rolls back
- R9 side-effect suppression: no per-row activity, no registry pushes
- R12 match only by (project_id, plan_ref)
- R13 content refresh with local status preserved; divergence reported
- R14 create from plan status mapping
- R15/R16 obsolete matrix; R17 reactivation; R18 never delete
- R19 diff result {created, updated, obsolete, reactivated, conflicts}
- R2 single-active milestone enforcement for milestones activated by this import
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.milestone import Milestone
from app.models.task import Task
from app.schemas import (
    PLAN_TASK_STATUS_MAP,
    ImportConflict,
    ImportEntityCounts,
    PlanImportManifest,
    PlanImportResult,
)
from app.services.activity_writer import write_activity
from app.services.ref_alloc import allocate_ref

logger = logging.getLogger(__name__)

_TERMINAL_TASK_STATUSES: frozenset[str] = frozenset({"done", "cancelled"})


class ManifestError(ValueError):
    """Cross-field manifest violations — router maps to HTTP 400, nothing written."""

    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def _cross_validate(manifest: PlanImportManifest) -> list[str]:
    errors: list[str] = []
    ms_refs = [m.plan_ref for m in manifest.milestones]
    dup_ms = {r for r in ms_refs if ms_refs.count(r) > 1}
    if dup_ms:
        errors.append(f"Duplicate milestone plan_ref: {sorted(dup_ms)}")
    task_refs = [t.plan_ref for t in manifest.tasks]
    dup_tasks = {r for r in task_refs if task_refs.count(r) > 1}
    if dup_tasks:
        errors.append(f"Duplicate task plan_ref: {sorted(dup_tasks)}")
    known = set(ms_refs)
    for t in manifest.tasks:
        if t.milestone_ref not in known:
            errors.append(
                f"Task {t.plan_ref} references milestone {t.milestone_ref} "
                "which is not in the manifest"
            )
    return errors


def _status_divergence(plan_ref: str, local: str, plan: str) -> ImportConflict:
    return ImportConflict(
        kind="status_divergence",
        plan_ref=plan_ref,
        detail=(
            f"kept local status '{local}' (plan says '{plan}') — informational, no action needed"
        ),
    )


async def run_plan_import(
    db: AsyncSession,
    project_id: uuid.UUID,
    manifest: PlanImportManifest,
    *,
    dry_run: bool,
    actor_id: uuid.UUID | None,
) -> PlanImportResult:
    errors = _cross_validate(manifest)
    if errors:
        raise ManifestError(errors)

    logger.info(
        "plan_import.start project=%s dry_run=%s source=%s plan_version=%s "
        "milestones=%d tasks=%d",
        project_id, dry_run, manifest.source_path, manifest.plan_version,
        len(manifest.milestones), len(manifest.tasks),
    )

    ms_counts = ImportEntityCounts()
    task_counts = ImportEntityCounts()
    conflicts: list[ImportConflict] = []
    now = datetime.now(UTC)

    existing_ms = list(
        (
            await db.scalars(
                select(Milestone).where(Milestone.project_id == project_id)
            )
        ).all()
    )
    ms_by_ref = {m.plan_ref: m for m in existing_ms if m.plan_ref}

    existing_tasks = list(
        (
            await db.scalars(
                select(Task).where(
                    Task.project_id == project_id,
                    Task.plan_ref.is_not(None),
                )
            )
        ).all()
    )
    task_by_ref = {t.plan_ref: t for t in existing_tasks if t.plan_ref}

    # --- Milestones (R13/R14/R16/R17) ---
    manifest_ms_refs = {m.plan_ref for m in manifest.milestones}
    ms_resolved: dict[str, Milestone] = {}
    newly_active: list[Milestone] = []

    for m in manifest.milestones:
        cur = ms_by_ref.get(m.plan_ref)
        if cur is None:
            cur = Milestone(
                project_id=project_id,
                plan_ref=m.plan_ref,
                key=m.key or m.plan_ref,
                name=m.name.strip(),
                summary=m.summary,
                description=m.description,
                status=m.status,
                plan_state="active",
                sort_order=m.sort_order,
                start_at=m.start_at,
                due_at=m.due_at,
                created_by=actor_id,
            )
            db.add(cur)
            ms_counts.created += 1
            if cur.status == "active":
                newly_active.append(cur)
        else:
            cur.key = m.key or cur.key
            cur.name = m.name.strip()
            cur.summary = m.summary
            cur.description = m.description
            cur.sort_order = m.sort_order
            cur.start_at = m.start_at
            cur.due_at = m.due_at
            if cur.plan_state == "obsolete":
                cur.plan_state = "active"
                if cur.status == "cancelled":
                    cur.status = "pending"
                ms_counts.reactivated += 1
            else:
                ms_counts.updated += 1
                if cur.status != m.status:
                    conflicts.append(
                        _status_divergence(m.plan_ref, cur.status, m.status)
                    )
        ms_resolved[m.plan_ref] = cur

    for cur in existing_ms:
        if cur.plan_ref in manifest_ms_refs or cur.plan_ref is None:
            continue
        if cur.plan_state == "obsolete":
            continue
        if cur.status == "active":
            conflicts.append(
                ImportConflict(
                    kind="in_progress_orphan",
                    plan_ref=cur.plan_ref,
                    detail=(
                        f"milestone '{cur.name}' is active locally but absent from the "
                        "new plan — left unchanged; resolve manually"
                    ),
                )
            )
            continue
        if cur.status != "done" and cur.status != "cancelled":
            cur.status = "cancelled"
        cur.plan_state = "obsolete"
        ms_counts.obsolete += 1

    # The session runs with autoflush disabled: flush now so newly created
    # milestones receive their ids before tasks reference milestone_id.
    await db.flush()

    # R2: a milestone activated by this import clears 'active' on any other.
    if newly_active:
        others = list(
            (
                await db.scalars(
                    select(Milestone).where(
                        Milestone.project_id == project_id,
                        Milestone.status == "active",
                    )
                )
            ).all()
        )
        for other in others:
            if other not in newly_active:
                other.status = "pending"

    # --- Tasks (R12-R18, R24) ---
    manifest_task_refs = {t.plan_ref for t in manifest.tasks}

    for t in manifest.tasks:
        ms_obj = ms_resolved[t.milestone_ref]
        mapped = PLAN_TASK_STATUS_MAP.get(t.status, t.status)
        cur = task_by_ref.get(t.plan_ref)
        if cur is None:
            ref = await allocate_ref(db, project_id, "task")
            row = Task(
                project_id=project_id,
                ref=ref,
                title=t.title.strip(),
                description=t.description,
                status=mapped,
                priority=(t.priority or "normal").strip(),
                milestone_id=ms_obj.id,
                plan_ref=t.plan_ref,
                plan_state="active",
                reporter_id=actor_id,
                closed_at=now if mapped in _TERMINAL_TASK_STATUSES else None,
            )
            db.add(row)
            task_counts.created += 1
        else:
            cur.title = t.title.strip()
            cur.description = t.description
            cur.milestone_id = ms_obj.id
            if cur.plan_state == "obsolete":
                cur.plan_state = "active"
                if cur.status == "cancelled":
                    cur.status = "todo"
                    cur.closed_at = None
                task_counts.reactivated += 1
            else:
                task_counts.updated += 1
                if cur.status != mapped:
                    conflicts.append(
                        _status_divergence(t.plan_ref, cur.status, mapped)
                    )

    for cur in existing_tasks:
        if cur.plan_ref in manifest_task_refs:
            continue
        if cur.plan_state == "obsolete":
            continue
        if cur.status == "in_progress":
            conflicts.append(
                ImportConflict(
                    kind="in_progress_orphan",
                    plan_ref=cur.plan_ref,
                    detail=(
                        f"task '{cur.title}' is in progress locally but absent from the "
                        "new plan — left unchanged; resolve manually"
                    ),
                )
            )
            continue
        if cur.status not in ("done", "cancelled"):
            cur.status = "cancelled"
            cur.closed_at = now
        cur.plan_state = "obsolete"
        task_counts.obsolete += 1

    # R20: warn on sort_order collisions across the project's milestones.
    seen: dict[int, str] = {}
    all_ms = existing_ms + [m for m in ms_resolved.values() if m not in existing_ms]
    for m in all_ms:
        key = m.sort_order
        if key in seen:
            conflicts.append(
                ImportConflict(
                    kind="sort_order_collision",
                    plan_ref=m.plan_ref,
                    detail=(
                        f"milestone {m.plan_ref or m.name} shares sort_order={key} "
                        f"with {seen[key]}"
                    ),
                )
            )
        else:
            seen[key] = m.plan_ref or m.name

    result = PlanImportResult(
        dry_run=dry_run,
        milestones=ms_counts,
        tasks=task_counts,
        conflicts=conflicts,
    )

    if dry_run:
        await db.rollback()
        logger.info(
            "plan_import.dry_run project=%s ms_created=%d ms_updated=%d "
            "ms_obsolete=%d ms_reactivated=%d t_created=%d t_updated=%d "
            "t_obsolete=%d t_reactivated=%d conflicts=%d",
            project_id, ms_counts.created, ms_counts.updated, ms_counts.obsolete,
            ms_counts.reactivated, task_counts.created, task_counts.updated,
            task_counts.obsolete, task_counts.reactivated, len(conflicts),
        )
        return result

    # R9: exactly one summary activity per import; no registry pushes (R9 "or none").
    summary = (
        f"Plan import ({manifest.plan_version or 'unversioned'}): "
        f"milestones +{ms_counts.created} ~{ms_counts.updated} "
        f"-{ms_counts.obsolete} re{ms_counts.reactivated}; "
        f"tasks +{task_counts.created} ~{task_counts.updated} "
        f"-{task_counts.obsolete} re{task_counts.reactivated}; "
        f"{len(conflicts)} conflict(s)"
    )
    await write_activity(
        db=db,
        project_id=project_id,
        subject_type="project",
        subject_id=project_id,
        kind="system",
        actor_id=actor_id,
        body=summary,
        meta_json={
            "event": "plan_import",
            "source_path": manifest.source_path,
            "plan_version": manifest.plan_version,
            "milestones": ms_counts.model_dump(),
            "tasks": task_counts.model_dump(),
            "conflicts": len(conflicts),
        },
    )
    await db.commit()
    logger.info(
        "plan_import.complete project=%s ms_created=%d ms_updated=%d ms_obsolete=%d "
        "ms_reactivated=%d t_created=%d t_updated=%d t_obsolete=%d t_reactivated=%d "
        "conflicts=%d",
        project_id, ms_counts.created, ms_counts.updated, ms_counts.obsolete,
        ms_counts.reactivated, task_counts.created, task_counts.updated,
        task_counts.obsolete, task_counts.reactivated, len(conflicts),
    )
    return result
