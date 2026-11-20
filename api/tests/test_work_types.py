"""Work-type catalog on tasks and tickets.

Existing rows and clients that omit the field land on the project's default
type (Programming). A second pass of the seed does not recreate a type the
project removed.
"""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.work_type import WorkType
from app.services.project_access import MemberRole
from tests.factories import add_member, auth_header, create_project, create_user


async def _project(db: AsyncSession):
    tag = uuid.uuid4().hex[:10]
    user = await create_user(db, email=f"work-type-{tag}@example.com")
    project = await create_project(
        db,
        name=f"Work types {tag}",
        slug=f"work-types-{tag}",
        owner_id=user.id,
    )
    await add_member(db, project.id, user.id, MemberRole.owner)
    await db.commit()
    return user, project


async def _types(client: AsyncClient, user, project) -> list[dict]:
    resp = await client.get(
        f"/v1/projects/{project.id}/work-types",
        headers=auth_header(user),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["items"]


def _by_key(items: list[dict], key: str) -> dict:
    return next(row for row in items if row["key"] == key)


async def test_new_project_gets_the_starter_catalog(db: AsyncSession, client: AsyncClient):
    user, project = await _project(db)
    items = await _types(client, user, project)
    assert {row["key"] for row in items} == {
        "programming",
        "administrative",
        "documentation",
    }
    assert _by_key(items, "programming")["is_default"] is True
    assert sum(1 for row in items if row["is_default"]) == 1


async def test_omitted_type_is_programming_and_a_chosen_type_is_kept(
    db: AsyncSession, client: AsyncClient
):
    user, project = await _project(db)
    items = await _types(client, user, project)
    programming = _by_key(items, "programming")
    documentation = _by_key(items, "documentation")

    omitted = await client.post(
        f"/v1/projects/{project.id}/tasks",
        headers=auth_header(user),
        json={"title": "Legacy client"},
    )
    assert omitted.status_code == 201, omitted.text
    assert omitted.json()["work_type_id"] == programming["id"]

    chosen = await client.post(
        f"/v1/projects/{project.id}/tasks",
        headers=auth_header(user),
        json={"title": "Write the guide", "work_type_id": documentation["id"]},
    )
    assert chosen.status_code == 201, chosen.text
    assert chosen.json()["work_type_id"] == documentation["id"]

    ticket = await client.post(
        f"/v1/projects/{project.id}/tickets",
        headers=auth_header(user),
        json={"title": "Ask accounting"},
    )
    assert ticket.status_code == 201, ticket.text
    assert ticket.json()["work_type_id"] == programming["id"]

    listed = await client.get(
        f"/v1/projects/{project.id}/tasks",
        headers=auth_header(user),
        params={"work_type_id": documentation["id"]},
    )
    assert listed.status_code == 200, listed.text
    assert [row["id"] for row in listed.json()["items"]] == [chosen.json()["id"]]


async def test_orm_insert_without_a_type_uses_the_default(db: AsyncSession, client: AsyncClient):
    user, project = await _project(db)
    programming = _by_key(await _types(client, user, project), "programming")
    row = Task(project_id=project.id, title="Direct insert", reporter_id=user.id)
    db.add(row)
    await db.flush()
    await db.refresh(row)
    assert str(row.work_type_id) == programming["id"]


async def test_a_type_from_another_project_is_rejected(db: AsyncSession, client: AsyncClient):
    user, project = await _project(db)
    other_user, other = await _project(db)
    foreign = _by_key(await _types(client, other_user, other), "documentation")
    resp = await client.post(
        f"/v1/projects/{project.id}/tasks",
        headers=auth_header(user),
        json={"title": "Wrong project", "work_type_id": foreign["id"]},
    )
    assert resp.status_code == 400, resp.text
    assert "work_type_id" in resp.text


async def test_custom_type_can_be_added_and_the_default_cannot_be_deleted(
    db: AsyncSession, client: AsyncClient
):
    user, project = await _project(db)
    headers = auth_header(user)
    created = await client.post(
        f"/v1/projects/{project.id}/work-types",
        headers=headers,
        json={"name": "Research", "description": "Investigation before a change"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["key"] == "research"
    assert created.json()["is_default"] is False

    programming = _by_key(await _types(client, user, project), "programming")
    denied = await client.delete(
        f"/v1/work-types/{programming['id']}",
        headers=headers,
    )
    assert denied.status_code == 409, denied.text

    documentation = _by_key(await _types(client, user, project), "documentation")
    task = await client.post(
        f"/v1/projects/{project.id}/tasks",
        headers=headers,
        json={"title": "Docs", "work_type_id": documentation["id"]},
    )
    assert task.status_code == 201, task.text
    in_use = await client.delete(f"/v1/work-types/{documentation['id']}", headers=headers)
    assert in_use.status_code == 409, in_use.text

    removed = await client.delete(f"/v1/work-types/{created.json()['id']}", headers=headers)
    assert removed.status_code == 204, removed.text


async def test_seed_does_not_restore_a_deleted_starter_type(
    db: AsyncSession, client: AsyncClient
):
    user, project = await _project(db)
    headers = auth_header(user)
    administrative = _by_key(await _types(client, user, project), "administrative")
    deleted = await client.delete(f"/v1/work-types/{administrative['id']}", headers=headers)
    assert deleted.status_code == 204, deleted.text

    await db.execute(text("SELECT seed_work_types_for_project(:id)"), {"id": project.id})
    await db.execute(text("SELECT seed_work_types_for_project(:id)"), {"id": project.id})
    keys = {
        row.key
        for row in (
            await db.scalars(select(WorkType).where(WorkType.project_id == project.id))
        ).all()
    }
    assert keys == {"programming", "documentation"}

    await db.execute(text("ALTER TABLE tasks ALTER COLUMN work_type_id SET NOT NULL"))
    await db.execute(text("ALTER TABLE tickets ALTER COLUMN work_type_id SET NOT NULL"))


async def test_deleting_a_project_removes_its_tasks_and_work_types(db: AsyncSession):
    user, project = await _project(db)
    db.add(Task(project_id=project.id, title="Goes away", reporter_id=user.id))
    await db.flush()
    await db.delete(project)
    await db.commit()
    left = await db.scalar(
        select(WorkType.id).where(WorkType.project_id == project.id).limit(1)
    )
    assert left is None
