"""Process templates copy columns, item types, and starter tasks onto a new project.

Basic keeps today's work-type seed and the global task statuses. Existing
projects are not rewritten.
"""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_template import ProjectBoardColumn, ProjectTemplate
from app.models.task import Task
from app.services.project_access import MemberRole
from tests.factories import add_member, auth_header, create_project, create_user


async def _owner(db: AsyncSession, *, superuser: bool = False):
    tag = uuid.uuid4().hex[:10]
    user = await create_user(
        db,
        email=f"template-{tag}@example.com",
        is_superuser=superuser,
    )
    await db.commit()
    return user


async def test_catalog_lists_basic_and_the_ten_processes(db: AsyncSession, client: AsyncClient):
    user = await _owner(db)
    resp = await client.get("/v1/project-templates", headers=auth_header(user))
    assert resp.status_code == 200, resp.text
    items = resp.json()["items"]
    keys = [row["key"] for row in items]
    assert keys[0] == "basic"
    assert set(keys) >= {
        "basic",
        "bug-tracking",
        "recruitment",
        "web-design",
        "contract-review",
        "month-end-close",
        "service-requests",
        "project-board",
        "sales-pipeline",
        "campaign",
        "procurement",
        "customer-onboarding",
        "engineering-delivery",
        "support-queue",
        "implementation",
        "renewal",
    }
    bug = next(row for row in items if row["key"] == "bug-tracking")
    assert [column["label"] for column in bug["columns"]] == [
        "Captured",
        "Triaged",
        "In progress",
        "Verify",
        "Done",
    ]
    assert bug["columns"][-1]["is_finished"] is True


async def test_omitted_template_is_basic_and_keeps_todays_board(
    db: AsyncSession, client: AsyncClient
):
    user = await _owner(db)
    created = await client.post(
        "/v1/projects",
        headers=auth_header(user),
        json={"name": "Plain"},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["template_key"] == "basic"
    columns = await client.get(
        f"/v1/projects/{body['id']}/board-columns",
        headers=auth_header(user),
    )
    assert columns.status_code == 200, columns.text
    assert columns.json()["items"] == []
    tasks = await client.get(f"/v1/projects/{body['id']}/tasks", headers=auth_header(user))
    assert tasks.json()["total"] == 0
    types = await client.get(
        f"/v1/projects/{body['id']}/work-types",
        headers=auth_header(user),
    )
    assert "programming" in {row["key"] for row in types.json()["items"]}


async def test_bug_tracking_copies_its_process(db: AsyncSession, client: AsyncClient):
    user = await _owner(db)
    created = await client.post(
        "/v1/projects",
        headers=auth_header(user),
        json={"name": "Bugs", "template_key": "bug-tracking"},
    )
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]
    headers = auth_header(user)
    columns = (await client.get(f"/v1/projects/{project_id}/board-columns", headers=headers)).json()
    assert [row["key"] for row in columns["items"]] == [
        "captured",
        "triaged",
        "in-progress",
        "verify",
        "done",
    ]
    types = (await client.get(f"/v1/projects/{project_id}/work-types", headers=headers)).json()
    assert {row["key"] for row in types["items"]} == {"bug", "improvement", "investigation"}
    tasks = (await client.get(f"/v1/projects/{project_id}/tasks", headers=headers)).json()
    by_title = {row["title"]: row for row in tasks["items"]}
    assert by_title["Login fails on an empty password"]["status"] == "captured"
    assert by_title["Confirm severity and owner"]["status"] == "triaged"
    assert by_title["Write the failing check"]["status"] == "in-progress"

    hired = await client.post(
        f"/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Legacy status", "status": "todo"},
    )
    assert hired.status_code == 400, hired.text
    assert "invalid_status" in hired.text


async def test_recruitment_finished_column_sets_and_clears_closed_at(
    db: AsyncSession, client: AsyncClient
):
    user = await _owner(db)
    created = await client.post(
        "/v1/projects",
        headers=auth_header(user),
        json={"name": "Hiring", "template_key": "recruitment"},
    )
    project_id = created.json()["id"]
    headers = auth_header(user)
    tasks = (await client.get(f"/v1/projects/{project_id}/tasks", headers=headers)).json()
    task_id = tasks["items"][0]["id"]
    moved = await client.post(
        f"/v1/tasks/{task_id}/transition",
        headers=headers,
        json={"status": "hired"},
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["closed_at"] is not None
    back = await client.post(
        f"/v1/tasks/{task_id}/transition",
        headers=headers,
        json={"status": "interview"},
    )
    assert back.status_code == 200, back.text
    assert back.json()["closed_at"] is None


async def test_unknown_template_creates_nothing(db: AsyncSession, client: AsyncClient):
    user = await _owner(db)
    before = await db.scalar(select(func.count()).select_from(Project))
    resp = await client.post(
        "/v1/projects",
        headers=auth_header(user),
        json={"name": "Nope", "template_key": "nope"},
    )
    assert resp.status_code == 400, resp.text
    assert "unknown_template" in resp.text
    after = await db.scalar(select(func.count()).select_from(Project))
    assert after == before


async def test_existing_project_keeps_global_statuses(db: AsyncSession, client: AsyncClient):
    user = await _owner(db)
    project = await create_project(db, name="Already here", slug=f"old-{uuid.uuid4().hex[:8]}", owner_id=user.id)
    await add_member(db, project.id, user.id, MemberRole.owner)
    task = Task(project_id=project.id, title="Keep me", status="in_progress", reporter_id=user.id)
    db.add(task)
    await db.commit()
    await db.execute(text("SELECT seed_work_types_for_project(:id)"), {"id": project.id})
    # Startup insert is idempotent and does not touch this project.
    await db.execute(text("INSERT INTO project_templates (key, name, is_builtin) SELECT 'basic', 'Basic', TRUE WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'basic')"))
    await db.commit()
    patched = await client.patch(
        f"/v1/tasks/{task.id}",
        headers=auth_header(user),
        json={"status": "done"},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["status"] == "done"
    columns = await db.scalar(
        select(func.count()).select_from(ProjectBoardColumn).where(ProjectBoardColumn.project_id == project.id)
    )
    assert columns == 0
    refreshed = await db.get(Project, project.id)
    assert refreshed is not None
    assert refreshed.template_key is None


async def test_second_seed_does_not_rewrite_a_template_description(db: AsyncSession):
    row = await db.scalar(select(ProjectTemplate).where(ProjectTemplate.key == "bug-tracking"))
    assert row is not None
    row.description = "Edited by an operator"
    await db.commit()
    await db.execute(
        text(
            """
            INSERT INTO project_templates (key, name, team, description, is_builtin)
            SELECT 'bug-tracking', 'Bug tracking', 'Engineering', 'replaced', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'bug-tracking')
            """
        )
    )
    await db.commit()
    await db.refresh(row)
    assert row.description == "Edited by an operator"


async def test_superuser_can_add_a_template_and_a_member_cannot(
    db: AsyncSession, client: AsyncClient
):
    admin = await _owner(db, superuser=True)
    member = await _owner(db)
    body = {
        "team": "Facilities",
        "name": "Room booking",
        "description": "Reserve a room.",
        "columns": [
            {"label": "Requested", "is_finished": False},
            {"label": "Booked", "is_finished": True},
        ],
        "work_types": [
            {"name": "Booking", "is_default": True},
            {"name": "Setup", "is_default": False},
        ],
        "items": [
            {"title": "Book the room", "column_label": "Requested", "work_type_name": "Booking"}
        ],
    }
    denied = await client.post("/v1/project-templates", headers=auth_header(member), json=body)
    assert denied.status_code == 403, denied.text
    created = await client.post("/v1/project-templates", headers=auth_header(admin), json=body)
    assert created.status_code == 201, created.text
    key = created.json()["key"]
    project = await client.post(
        "/v1/projects",
        headers=auth_header(member),
        json={"name": "Rooms", "template_key": key},
    )
    assert project.status_code == 201, project.text
    project_id = project.json()["id"]
    columns = await client.get(
        f"/v1/projects/{project_id}/board-columns",
        headers=auth_header(member),
    )
    assert [row["label"] for row in columns.json()["items"]] == ["Requested", "Booked"]
    shipped = await db.scalar(select(ProjectTemplate).where(ProjectTemplate.key == "bug-tracking"))
    assert shipped is not None
    blocked = await client.delete(
        f"/v1/project-templates/{shipped.id}",
        headers=auth_header(admin),
    )
    assert blocked.status_code == 409, blocked.text
    removed = await client.delete(
        f"/v1/project-templates/{created.json()['id']}",
        headers=auth_header(admin),
    )
    assert removed.status_code == 204, removed.text
    still = await client.get(
        f"/v1/projects/{project_id}/board-columns",
        headers=auth_header(member),
    )
    assert len(still.json()["items"]) == 2


async def test_plan_import_rejects_a_process_project(db: AsyncSession, client: AsyncClient):
    user = await _owner(db)
    created = await client.post(
        "/v1/projects",
        headers=auth_header(user),
        json={"name": "No import", "template_key": "bug-tracking"},
    )
    project_id = created.json()["id"]
    before = await db.scalar(select(func.count()).select_from(Task).where(Task.project_id == project_id))
    resp = await client.post(
        f"/v1/projects/{project_id}/plan-import",
        headers=auth_header(user),
        json={},
    )
    assert resp.status_code == 409, resp.text
    assert "template_project" in resp.text
    after = await db.scalar(select(func.count()).select_from(Task).where(Task.project_id == project_id))
    assert after == before
