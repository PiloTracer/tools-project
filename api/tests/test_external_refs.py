"""Tests for cross-app external references."""

from __future__ import annotations

import uuid

from httpx import AsyncClient

from tests.factories import add_member, auth_header, create_project, create_user


async def test_create_and_list_external_refs(client: AsyncClient, db) -> None:
    user = await create_user(db, email="external@example.com")
    project = await create_project(db, name="External Project", slug="external-project", owner_id=user.id)
    await add_member(db, project.id, user.id)
    await db.commit()

    subject_id = uuid.uuid4()
    payload = {
        "source_app": "CompanyBrain",
        "external_id": "CB-12345",
        "external_url": "https://companybrain.example.com/notes/CB-12345",
        "label": "Q3 strategy note",
        "subject_type": "task",
        "subject_id": str(subject_id),
    }
    create_resp = await client.post(
        f"/v1/projects/{project.id}/external-refs",
        json=payload,
        headers=auth_header(user),
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["source_app"] == "CompanyBrain"
    assert data["external_id"] == "CB-12345"
    assert data["subject_id"] == str(subject_id)

    list_resp = await client.get(
        f"/v1/projects/{project.id}/external-refs?subject_type=task&subject_id={subject_id}",
        headers=auth_header(user),
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["external_id"] == "CB-12345"

    ref_id = items[0]["id"]
    del_resp = await client.delete(
        f"/v1/projects/{project.id}/external-refs/{ref_id}",
        headers=auth_header(user),
    )
    assert del_resp.status_code == 204

    list_resp2 = await client.get(
        f"/v1/projects/{project.id}/external-refs",
        headers=auth_header(user),
    )
    assert list_resp2.json()["items"] == []


async def test_external_ref_requires_project_access(client: AsyncClient, db) -> None:
    user = await create_user(db, email="noaccess@example.com")
    other = await create_user(db, email="owner@example.com")
    project = await create_project(db, name="Private Project", slug="private-project", owner_id=other.id)
    await db.commit()

    resp = await client.get(
        f"/v1/projects/{project.id}/external-refs",
        headers=auth_header(user),
    )
    assert resp.status_code == 404
