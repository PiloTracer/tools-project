"""plan-sync: plan-manifest import API tests (SPEC .work/features/plan-sync/20260929-SPEC.md).

Covers SPEC test plan T1-T11 plus D6 (prefix gate decoupled) and D7 (X-Api-Key
on the import endpoint only).
"""

from __future__ import annotations

import copy
import os
import uuid
from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy import func, select

from app.config import get_settings
from app.models.activity import Activity
from app.models.task import Task
from app.services.project_access import MemberRole
from tests.factories import add_member, auth_header, create_project, create_user

# --------------------------------------------------------------------------
# Manifest builders
# --------------------------------------------------------------------------

SMALL_TASKS = [
    {"plan_ref": "M1-T1", "milestone_ref": "M1", "title": "First task", "status": "pending"},
    {"plan_ref": "M1-T2", "milestone_ref": "M1", "title": "Second task", "status": "pending"},
    {"plan_ref": "M1-T3", "milestone_ref": "M1", "title": "Third task", "status": "pending"},
    {"plan_ref": "M2-T1", "milestone_ref": "M2", "title": "Fourth task", "status": "pending"},
    {"plan_ref": "M2-T2", "milestone_ref": "M2", "title": "Fifth task", "status": "pending"},
]


def small_manifest(*, tasks: list[dict] | None = None) -> dict:
    return {
        "manifest_version": 1,
        "source_path": ".work/feedback/plans-import/plans/test-plan.md",
        "plan_version": "2026-09-29",
        "project": {"name": "Plan Sync Test"},
        "milestones": [
            {"plan_ref": "M1", "name": "Milestone One", "status": "active", "sort_order": 1},
            {"plan_ref": "M2", "name": "Milestone Two", "status": "pending", "sort_order": 2},
        ],
        "tasks": copy.deepcopy(tasks if tasks is not None else SMALL_TASKS),
    }


def big_manifest() -> dict:
    """12 milestones / 153 tasks — the shape of the real 20260925 full plan."""
    milestones = []
    for i in range(1, 13):
        milestones.append(
            {
                "plan_ref": f"M{i}",
                "name": f"Milestone {i}",
                "status": "active" if i == 1 else "pending",
                "sort_order": i,
            }
        )
    tasks = []
    for i in range(1, 13):
        count = 13 if i <= 9 else 12
        for j in range(1, count + 1):
            tasks.append(
                {
                    "plan_ref": f"M{i}-T{j}",
                    "milestone_ref": f"M{i}",
                    "title": f"Task {i}.{j}",
                    "status": "pending",
                }
            )
    assert len(tasks) == 153
    return {
        "manifest_version": 1,
        "source_path": ".work/feedback/plans-import/plans/20260925-full-plan.md",
        "plan_version": "2026-09-25",
        "project": {"name": "Full Plan Import"},
        "milestones": milestones,
        "tasks": tasks,
    }


def _keep_tasks(manifest: dict, keep: set[str]) -> dict:
    out = copy.deepcopy(manifest)
    out["tasks"] = [t for t in out["tasks"] if t["plan_ref"] in keep]
    return out


async def _setup_project(db, role: MemberRole = MemberRole.contributor):
    tag = uuid.uuid4().hex[:8]
    user = await create_user(db, email=f"plan-sync-{tag}@example.com")
    project = await create_project(
        db, name=f"Plan Sync {tag}", slug=f"plan-sync-{tag}", owner_id=user.id
    )
    await add_member(db, project.id, user.id, role)
    await db.commit()
    return user, project


def _import_url(project_id: uuid.UUID, *, dry_run: bool = False) -> str:
    url = f"/v1/projects/{project_id}/plan-import"
    return f"{url}?dry_run=true" if dry_run else url


async def _tasks_by_ref(client, user, project_id) -> dict[str, dict]:
    resp = await client.get(
        f"/v1/projects/{project_id}/tasks", headers=auth_header(user)
    )
    assert resp.status_code == 200, resp.text
    items = resp.json()["items"]
    return {t["plan_ref"]: t for t in items if t["plan_ref"]}


async def _set_local_statuses(
    db, project_id: uuid.UUID, statuses: dict[str, str]
) -> None:
    for ref, st in statuses.items():
        row = await db.scalar(
            select(Task).where(Task.project_id == project_id, Task.plan_ref == ref)
        )
        assert row is not None, f"task {ref} not found"
        row.status = st
        row.closed_at = (
            datetime.now(UTC) if st in ("done", "cancelled") else None
        )
    await db.commit()


# --------------------------------------------------------------------------
# Auth / permissions (D7, SPEC T8)
# --------------------------------------------------------------------------


async def test_import_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/v1/projects/" + str(uuid.uuid4()) + "/plan-import", json=small_manifest())
    assert resp.status_code == 401


async def test_x_api_key_rejected_on_regular_task_endpoint(
    client: AsyncClient, db
) -> None:
    user, project = await _setup_project(db)
    resp = await client.get(
        f"/v1/projects/{project.id}/tasks",
        headers={"X-Api-Key": "anything"},
    )
    assert resp.status_code == 401


async def test_agent_api_key_accepted_on_import(client: AsyncClient, db) -> None:
    user, project = await _setup_project(db)
    os.environ["AGENT_API_KEY"] = "test-agent-key-plan-sync"
    get_settings.cache_clear()
    try:
        resp = await client.post(
            _import_url(project.id),
            json=small_manifest(),
            headers={"X-Api-Key": "test-agent-key-plan-sync"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["milestones"]["created"] == 2
        assert body["tasks"]["created"] == 5

        # FK anchor: tasks must reference the persisted agent row.
        from app.services.agent_identity import AGENT_USER_ID

        tasks = await _tasks_by_ref(client, user, project.id)
        assert all(t["reporter_id"] == str(AGENT_USER_ID) for t in tasks.values())
    finally:
        os.environ.pop("AGENT_API_KEY", None)
        get_settings.cache_clear()


async def test_non_member_gets_404(client: AsyncClient, db) -> None:
    tag = uuid.uuid4().hex[:8]
    owner = await create_user(db, email=f"owner-{tag}@example.com")
    project = await create_project(
        db, name=f"Private {tag}", slug=f"private-{tag}", owner_id=owner.id
    )
    outsider = await create_user(db, email=f"outsider-{tag}@example.com")
    await db.commit()
    resp = await client.post(
        _import_url(project.id),
        json=small_manifest(),
        headers=auth_header(outsider),
    )
    assert resp.status_code == 404


async def test_viewer_cannot_import(client: AsyncClient, db) -> None:
    user, project = await _setup_project(db, role=MemberRole.viewer)
    resp = await client.post(
        _import_url(project.id),
        json=small_manifest(),
        headers=auth_header(user),
    )
    assert resp.status_code == 403
    assert "Not permitted" in resp.text


# --------------------------------------------------------------------------
# Fresh import / idempotency (SPEC T1, T2)
# --------------------------------------------------------------------------


async def test_fresh_import_creates_12_milestones_153_tasks(
    client: AsyncClient, db
) -> None:
    user, project = await _setup_project(db)
    resp = await client.post(
        _import_url(project.id), json=big_manifest(), headers=auth_header(user)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["dry_run"] is False
    assert body["milestones"] == {"created": 12, "updated": 0, "obsolete": 0, "reactivated": 0}
    assert body["tasks"] == {"created": 153, "updated": 0, "obsolete": 0, "reactivated": 0}
    assert body["conflicts"] == []

    ms_resp = await client.get(
        f"/v1/projects/{project.id}/milestones", headers=auth_header(user)
    )
    assert ms_resp.status_code == 200
    ms_items = ms_resp.json()["items"]
    assert len(ms_items) == 12
    assert sum(1 for m in ms_items if m["status"] == "active") == 1
    assert sum(m["task_total"] for m in ms_items) == 153
    assert all(m["plan_state"] == "active" for m in ms_items)

    tasks = await _tasks_by_ref(client, user, project.id)
    assert len(tasks) == 153
    assert all(t["plan_state"] == "active" for t in tasks.values())
    assert all(t["status"] == "todo" for t in tasks.values())
    assert all(t["milestone_id"] for t in tasks.values())


async def test_reimport_is_idempotent(client: AsyncClient, db) -> None:
    user, project = await _setup_project(db)
    manifest = small_manifest()
    first = await client.post(
        _import_url(project.id), json=manifest, headers=auth_header(user)
    )
    assert first.status_code == 200, first.text
    second = await client.post(
        _import_url(project.id), json=manifest, headers=auth_header(user)
    )
    assert second.status_code == 200, second.text
    body = second.json()
    assert body["tasks"]["created"] == 0
    assert body["tasks"]["obsolete"] == 0
    assert body["tasks"]["reactivated"] == 0
    assert body["tasks"]["updated"] == 5
    assert body["milestones"]["created"] == 0
    assert body["milestones"]["updated"] == 2
    assert body["conflicts"] == []

    tasks = await _tasks_by_ref(client, user, project.id)
    assert len(tasks) == 5


async def test_local_done_survives_reimport(client: AsyncClient, db) -> None:
    user, project = await _setup_project(db)
    manifest = small_manifest()
    assert (
        await client.post(
            _import_url(project.id), json=manifest, headers=auth_header(user)
        )
    ).status_code == 200

    tasks = await _tasks_by_ref(client, user, project.id)
    task_id = tasks["M1-T1"]["id"]
    patched = await client.patch(
        f"/v1/tasks/{task_id}", json={"status": "done"}, headers=auth_header(user)
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["status"] == "done"

    resp = await client.post(
        _import_url(project.id), json=manifest, headers=auth_header(user)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tasks"]["created"] == 0
    divergence = [
        c for c in body["conflicts"] if c["plan_ref"] == "M1-T1"
    ]
    assert len(divergence) == 1
    assert divergence[0]["kind"] == "status_divergence"

    after = await _tasks_by_ref(client, user, project.id)
    assert after["M1-T1"]["status"] == "done"
    assert after["M1-T1"]["closed_at"] is not None


# --------------------------------------------------------------------------
# Obsolete matrix / conflict / reactivation (SPEC T4, T5)
# --------------------------------------------------------------------------


async def test_obsolete_matrix_and_in_progress_conflict(
    client: AsyncClient, db
) -> None:
    user, project = await _setup_project(db)
    manifest = small_manifest()
    assert (
        await client.post(
            _import_url(project.id), json=manifest, headers=auth_header(user)
        )
    ).status_code == 200

    # Local statuses diverge from the plan before the next revision lands.
    await _set_local_statuses(
        db,
        project.id,
        {
            "M1-T1": "todo",
            "M1-T2": "in_progress",
            "M1-T3": "done",
            "M2-T1": "blocked",
            "M2-T2": "cancelled",
        },
    )

    next_manifest = _keep_tasks(manifest, {"M1-T1"})
    resp = await client.post(
        _import_url(project.id), json=next_manifest, headers=auth_header(user)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # T3(done), T4(blocked), T5(cancelled) -> obsolete; T2(in_progress) -> conflict.
    assert body["tasks"]["obsolete"] == 3
    assert body["tasks"]["reactivated"] == 0
    assert body["tasks"]["updated"] == 1
    orphan = [
        c for c in body["conflicts"] if c["kind"] == "in_progress_orphan"
    ]
    assert len(orphan) == 1
    assert orphan[0]["plan_ref"] == "M1-T2"

    after = await _tasks_by_ref(client, user, project.id)
    assert after["M1-T1"]["plan_state"] == "active"
    assert after["M1-T1"]["status"] == "todo"
    # in_progress is never auto-killed (D11)
    assert after["M1-T2"]["plan_state"] == "active"
    assert after["M1-T2"]["status"] == "in_progress"
    assert after["M1-T2"]["closed_at"] is None
    # done keeps its status but is marked obsolete
    assert after["M1-T3"]["plan_state"] == "obsolete"
    assert after["M1-T3"]["status"] == "done"
    # blocked -> cancelled + obsolete
    assert after["M2-T1"]["plan_state"] == "obsolete"
    assert after["M2-T1"]["status"] == "cancelled"
    assert after["M2-T1"]["closed_at"] is not None
    # already cancelled stays cancelled
    assert after["M2-T2"]["plan_state"] == "obsolete"
    assert after["M2-T2"]["status"] == "cancelled"

    # No deletions ever happen (R18)
    assert len(after) == 5


async def test_reactivated_task_returns_to_plan(client: AsyncClient, db) -> None:
    user, project = await _setup_project(db)
    manifest = small_manifest()
    assert (
        await client.post(
            _import_url(project.id), json=manifest, headers=auth_header(user)
        )
    ).status_code == 200

    drop = _keep_tasks(manifest, {"M1-T1", "M1-T2", "M1-T3"})
    resp = await client.post(
        _import_url(project.id), json=drop, headers=auth_header(user)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["tasks"]["obsolete"] == 2

    resp = await client.post(
        _import_url(project.id), json=manifest, headers=auth_header(user)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tasks"]["reactivated"] == 2
    assert body["tasks"]["obsolete"] == 0

    after = await _tasks_by_ref(client, user, project.id)
    assert after["M2-T1"]["plan_state"] == "active"
    assert after["M2-T1"]["status"] == "todo"
    assert after["M2-T1"]["closed_at"] is None


# --------------------------------------------------------------------------
# dry_run + activity (SPEC T6, T7)
# --------------------------------------------------------------------------


async def test_dry_run_writes_nothing(client: AsyncClient, db) -> None:
    user, project = await _setup_project(db)
    # Capture ids/headers before the request: the dry-run path rolls back the
    # session, which expires these ORM objects.
    project_id = project.id
    headers = auth_header(user)
    resp = await client.post(
        _import_url(project_id, dry_run=True),
        json=small_manifest(),
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["dry_run"] is True
    assert body["milestones"]["created"] == 2
    assert body["tasks"]["created"] == 5

    tasks = await client.get(f"/v1/projects/{project_id}/tasks", headers=headers)
    assert tasks.json()["total"] == 0
    ms = await client.get(
        f"/v1/projects/{project_id}/milestones", headers=headers
    )
    assert ms.json()["items"] == []
    activities = await db.scalar(
        select(func.count(Activity.id)).where(Activity.project_id == project_id)
    )
    assert activities == 0


async def test_exactly_one_summary_activity_per_import(
    client: AsyncClient, db
) -> None:
    user, project = await _setup_project(db)
    manifest = small_manifest()
    assert (
        await client.post(
            _import_url(project.id), json=manifest, headers=auth_header(user)
        )
    ).status_code == 200

    count = await db.scalar(
        select(func.count(Activity.id)).where(
            Activity.project_id == project.id, Activity.kind == "system"
        )
    )
    assert count == 1
    row = await db.scalar(
        select(Activity).where(
            Activity.project_id == project.id, Activity.kind == "system"
        )
    )
    assert row is not None
    assert row.meta_json["event"] == "plan_import"

    assert (
        await client.post(
            _import_url(project.id), json=manifest, headers=auth_header(user)
        )
    ).status_code == 200
    count = await db.scalar(
        select(func.count(Activity.id)).where(
            Activity.project_id == project.id, Activity.kind == "system"
        )
    )
    assert count == 2


# --------------------------------------------------------------------------
# Manifest validation (SPEC T9)
# --------------------------------------------------------------------------


async def test_manifest_validation_errors_are_400(
    client: AsyncClient, db
) -> None:
    user, project = await _setup_project(db)
    headers = auth_header(user)
    url = _import_url(project.id)

    bad_version = small_manifest()
    bad_version["manifest_version"] = 2
    resp = await client.post(url, json=bad_version, headers=headers)
    assert resp.status_code == 400
    assert "Unsupported manifest_version" in resp.text

    bad_ref = small_manifest()
    bad_ref["tasks"][0]["plan_ref"] = "T-9"
    resp = await client.post(url, json=bad_ref, headers=headers)
    assert resp.status_code == 400
    assert "Task ref must match" in resp.text

    orphan = small_manifest()
    orphan["tasks"][0]["milestone_ref"] = "M9"
    resp = await client.post(url, json=orphan, headers=headers)
    assert resp.status_code == 400
    assert "not in the manifest" in resp.text

    dup = small_manifest()
    dup["tasks"].append(copy.deepcopy(dup["tasks"][0]))
    resp = await client.post(url, json=dup, headers=headers)
    assert resp.status_code == 400
    assert "Duplicate task plan_ref" in resp.text

    empty_title = small_manifest()
    empty_title["tasks"][0]["title"] = ""
    resp = await client.post(url, json=empty_title, headers=headers)
    assert resp.status_code == 400

    # Nothing was written by any of the rejected payloads.
    tasks = await client.get(
        f"/v1/projects/{project.id}/tasks", headers=headers
    )
    assert tasks.json()["total"] == 0


# --------------------------------------------------------------------------
# D6: auto_prefix without GitHub link + registry gate preserved
# --------------------------------------------------------------------------


async def test_auto_prefix_works_without_github_link(
    client: AsyncClient, db
) -> None:
    user, project = await _setup_project(db, role=MemberRole.owner)
    headers = auth_header(user)

    resp = await client.patch(
        f"/v1/projects/{project.id}",
        json={"project_key": "PSYNC", "auto_prefix_enabled": True},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["auto_prefix_enabled"] is True

    # The registry setting still requires a linked repository.
    resp = await client.patch(
        f"/v1/projects/{project.id}",
        json={"github_task_registry_enabled": True},
        headers=headers,
    )
    assert resp.status_code == 400

    resp = await client.post(
        _import_url(project.id), json=small_manifest(), headers=headers
    )
    assert resp.status_code == 200, resp.text
    tasks = await _tasks_by_ref(client, user, project.id)
    refs = [t["ref"] for t in tasks.values()]
    assert all(r is not None and r.startswith("PSYNC-") for r in refs)


# --------------------------------------------------------------------------
# Filters + progress (SPEC T10)
# --------------------------------------------------------------------------


async def test_task_filters_by_milestone_and_plan_state(
    client: AsyncClient, db
) -> None:
    user, project = await _setup_project(db)
    headers = auth_header(user)
    manifest = small_manifest()
    assert (
        await client.post(
            _import_url(project.id), json=manifest, headers=headers
        )
    ).status_code == 200

    tasks = await _tasks_by_ref(client, user, project.id)
    m1_id = tasks["M1-T1"]["milestone_id"]
    m2_id = tasks["M2-T1"]["milestone_id"]
    assert m1_id is not None and m2_id is not None
    assert m1_id != m2_id

    resp = await client.get(
        f"/v1/projects/{project.id}/tasks?milestone_id={m1_id}", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 3

    resp = await client.get(
        f"/v1/projects/{project.id}/tasks?plan_state=obsolete", headers=headers
    )
    assert resp.json()["total"] == 0
    resp = await client.get(
        f"/v1/projects/{project.id}/tasks?plan_state=active", headers=headers
    )
    assert resp.json()["total"] == 5

    # Mark one done, verify progress + status filter.
    patch = await client.patch(
        f"/v1/tasks/{tasks['M1-T3']['id']}",
        json={"status": "done"},
        headers=headers,
    )
    assert patch.status_code == 200, patch.text
    resp = await client.get(
        f"/v1/projects/{project.id}/tasks?status=done", headers=headers
    )
    assert resp.json()["total"] == 1

    ms_resp = await client.get(
        f"/v1/projects/{project.id}/milestones", headers=headers
    )
    by_ref = {m["plan_ref"]: m for m in ms_resp.json()["items"]}
    assert by_ref["M1"]["task_total"] == 3
    assert by_ref["M1"]["task_done"] == 1
    assert by_ref["M2"]["task_total"] == 2
    assert by_ref["M2"]["task_done"] == 0

    # Drop M2's tasks -> they become obsolete; the filter reflects it.
    drop = _keep_tasks(manifest, {"M1-T1", "M1-T2", "M1-T3"})
    assert (
        await client.post(
            _import_url(project.id), json=drop, headers=headers
        )
    ).status_code == 200
    resp = await client.get(
        f"/v1/projects/{project.id}/tasks?plan_state=obsolete", headers=headers
    )
    body = resp.json()
    assert body["total"] == 2
    assert {t["plan_ref"] for t in body["items"]} == {"M2-T1", "M2-T2"}


# --------------------------------------------------------------------------
# Single-active milestone enforcement on import (SPEC R2)
# --------------------------------------------------------------------------


async def test_import_enforces_single_active_milestone(
    client: AsyncClient, db
) -> None:
    user, project = await _setup_project(db)
    headers = auth_header(user)
    first = small_manifest()  # M1 active, M2 pending
    assert (
        await client.post(
            _import_url(project.id), json=first, headers=headers
        )
    ).status_code == 200

    # R13: a plan-side status flip on existing milestones is reported,
    # never applied — local status wins unconditionally.
    second = small_manifest()
    second["milestones"][0]["status"] = "pending"
    second["milestones"][1]["status"] = "active"
    resp = await client.post(
        _import_url(project.id), json=second, headers=headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    divergences = [
        c
        for c in body["conflicts"]
        if c["kind"] == "status_divergence" and c["plan_ref"] in ("M1", "M2")
    ]
    assert len(divergences) == 2

    ms_resp = await client.get(
        f"/v1/projects/{project.id}/milestones", headers=headers
    )
    by_ref = {m["plan_ref"]: m for m in ms_resp.json()["items"]}
    assert by_ref["M1"]["status"] == "active"  # preserved, not flipped
    assert by_ref["M2"]["status"] == "pending"  # plan's "active" not applied
    assert sum(1 for m in by_ref.values() if m["status"] == "active") == 1

    # R2: a milestone CREATED active by the import demotes the current active
    # milestone inside the same transaction.
    third = copy.deepcopy(second)
    third["milestones"].append(
        {"plan_ref": "M3", "name": "Milestone Three", "status": "active", "sort_order": 3}
    )
    resp = await client.post(
        _import_url(project.id), json=third, headers=headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["milestones"]["created"] == 1

    ms_resp = await client.get(
        f"/v1/projects/{project.id}/milestones", headers=headers
    )
    items = ms_resp.json()["items"]
    active = [m for m in items if m["status"] == "active"]
    assert len(active) == 1
    assert active[0]["plan_ref"] == "M3"
    by_ref = {m["plan_ref"]: m for m in items}
    assert by_ref["M1"]["status"] == "pending"  # demoted by R2
