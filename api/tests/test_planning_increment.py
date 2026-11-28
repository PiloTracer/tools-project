"""Additive planning features must not change existing task or CRM responses."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import auth_header, create_project, create_user


async def test_plain_task_create_still_has_no_recurrence(client: AsyncClient, db: AsyncSession) -> None:
    user = await create_user(db, email=f"plan-{uuid.uuid4().hex[:8]}@example.com", is_superuser=True)
    project = await create_project(db, name="Plain board", slug=f"plain-{uuid.uuid4().hex[:6]}", owner_id=user.id)
    await db.commit()
    created = await client.post(
        f"/v1/projects/{project.id}/tasks",
        headers=auth_header(user),
        json={"title": "Ordinary task"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["recurrence"] is None
    assert created.json()["status"] == "todo"


async def test_dependency_cycle_is_rejected_and_dates_stay(client: AsyncClient, db: AsyncSession) -> None:
    user = await create_user(db, email=f"dep-{uuid.uuid4().hex[:8]}@example.com", is_superuser=True)
    project = await create_project(db, name="Deps", slug=f"deps-{uuid.uuid4().hex[:6]}", owner_id=user.id)
    await db.commit()
    headers = auth_header(user)
    due = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    a = await client.post(
        f"/v1/projects/{project.id}/tasks",
        headers=headers,
        json={"title": "A", "due_at": due},
    )
    b = await client.post(
        f"/v1/projects/{project.id}/tasks",
        headers=headers,
        json={"title": "B", "due_at": due},
    )
    assert a.status_code == 201 and b.status_code == 201
    a_id, b_id = a.json()["id"], b.json()["id"]
    first = await client.post(
        f"/v1/projects/{project.id}/dependencies",
        headers=headers,
        json={"predecessor_id": a_id, "successor_id": b_id},
    )
    assert first.status_code == 201, first.text
    cycle = await client.post(
        f"/v1/projects/{project.id}/dependencies",
        headers=headers,
        json={"predecessor_id": b_id, "successor_id": a_id},
    )
    assert cycle.status_code == 400
    again = await client.get(f"/v1/tasks/{a_id}", headers=headers)
    assert again.status_code == 200
    assert again.json()["due_at"][:19] == due[:19]


async def test_closing_weekly_task_creates_one_successor(client: AsyncClient, db: AsyncSession) -> None:
    user = await create_user(db, email=f"rec-{uuid.uuid4().hex[:8]}@example.com", is_superuser=True)
    project = await create_project(db, name="Recur", slug=f"rec-{uuid.uuid4().hex[:6]}", owner_id=user.id)
    await db.commit()
    headers = auth_header(user)
    due = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    created = await client.post(
        f"/v1/projects/{project.id}/tasks",
        headers=headers,
        json={"title": "Weekly check", "due_at": due, "recurrence": "weekly"},
    )
    assert created.status_code == 201, created.text
    task_id = created.json()["id"]
    closed = await client.post(
        f"/v1/tasks/{task_id}/transition",
        headers=headers,
        json={"status": "done"},
    )
    assert closed.status_code == 200, closed.text
    listed = await client.get(f"/v1/projects/{project.id}/tasks", headers=headers)
    titles = [row["title"] for row in listed.json()["items"]]
    assert titles.count("Weekly check") == 2
    closed_again = await client.post(
        f"/v1/tasks/{task_id}/transition",
        headers=headers,
        json={"status": "done"},
    )
    assert closed_again.status_code == 200
    listed_again = await client.get(f"/v1/projects/{project.id}/tasks", headers=headers)
    titles_again = [row["title"] for row in listed_again.json()["items"]]
    assert titles_again.count("Weekly check") == 2


async def test_report_query_rejects_unknown_dimension(client: AsyncClient, db: AsyncSession) -> None:
    user = await create_user(db, email=f"rep-{uuid.uuid4().hex[:8]}@example.com", is_superuser=True)
    await db.commit()
    bad = await client.post(
        "/v1/reports/query",
        headers=auth_header(user),
        json={"dataset": "prospects", "dimension": "secret_notes", "measure": "count"},
    )
    assert bad.status_code == 400
    ok = await client.post(
        "/v1/reports/query",
        headers=auth_header(user),
        json={"dataset": "prospects", "dimension": "pipeline_stage", "measure": "count"},
    )
    assert ok.status_code == 200, ok.text
    assert "rows" in ok.json()


async def test_custom_field_and_history_round_trip(client: AsyncClient, db: AsyncSession) -> None:
    user = await create_user(db, email=f"cf-{uuid.uuid4().hex[:8]}@example.com", is_superuser=True)
    await db.commit()
    headers = auth_header(user)
    created = await client.post(
        "/v1/prospects",
        headers=headers,
        json={"company_name": f"Field Co {uuid.uuid4().hex[:6]}", "custom_fields": {"contract_type": "fixed"}},
    )
    assert created.status_code == 201, created.text
    assert created.json()["custom_fields"]["contract_type"] == "fixed"
    prospect_id = created.json()["id"]
    patched = await client.patch(
        f"/v1/prospects/{prospect_id}",
        headers=headers,
        json={"zone": "Norte"},
    )
    assert patched.status_code == 200, patched.text
    history = await client.get(
        "/v1/planning/changes",
        headers=headers,
        params={"entity_type": "prospect", "entity_id": prospect_id},
    )
    assert history.status_code == 200, history.text
    fields = [row["field_name"] for row in history.json()["items"]]
    assert "zone" in fields
