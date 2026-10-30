"""Activity feed API regression tests.

Covers the project Activity tab's create/list/pagination/attachment paths,
backward-compatible ``note`` kind handling, internal visibility, and the
client-portal activity scoping.
"""

from __future__ import annotations

import base64
import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_client_access import ProjectClientAccess
from app.services.project_access import MemberRole
from tests.factories import (
    add_member,
    auth_header,
    create_client,
    create_client_contact,
    create_project,
    create_user,
)

# 1x1 transparent PNG — valid magic bytes for the attachment sniffer.
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


async def _project(db: AsyncSession, *, role: MemberRole = MemberRole.owner):
    tag = uuid.uuid4().hex[:10]
    user = await create_user(db, email=f"activity-{tag}@example.com")
    project = await create_project(
        db,
        name=f"Activity {tag}",
        slug=f"activity-{tag}",
        owner_id=user.id,
    )
    await add_member(db, project.id, user.id, role)
    await db.commit()
    return user, project


async def _create_task(
    client: AsyncClient,
    user,
    project,
    *,
    title: str = "Activity task",
    assignee_id: uuid.UUID | None = None,
) -> dict:
    payload: dict[str, object] = {"title": title}
    if assignee_id is not None:
        payload["assignee_id"] = str(assignee_id)
    resp = await client.post(
        f"/v1/projects/{project.id}/tasks",
        headers=auth_header(user),
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _post_activity(
    client: AsyncClient,
    user,
    project,
    payload: dict,
) -> dict:
    body = {
        "subject_type": "project",
        "subject_id": str(project.id),
        "kind": "comment",
        "body": "hello",
        **payload,
    }
    resp = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=auth_header(user),
        json=body,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_note_alias_is_stored_as_comment(client: AsyncClient, db: AsyncSession) -> None:
    user, project = await _project(db)
    created = await _post_activity(
        client, user, project, {"kind": "note", "body": "legacy composer payload"}
    )
    assert created["kind"] == "comment"
    assert created["body"] == "legacy composer payload"

    # The historical filter value keeps working too.
    listed = await client.get(
        f"/v1/projects/{project.id}/activities?kind=note",
        headers=auth_header(user),
    )
    assert listed.status_code == 200, listed.text
    assert [row["id"] for row in listed.json()["items"]] == [created["id"]]


async def test_invalid_kind_and_input_errors(client: AsyncClient, db: AsyncSession) -> None:
    user, project = await _project(db)
    headers = auth_header(user)
    base = {
        "subject_type": "project",
        "subject_id": str(project.id),
        "body": "x",
    }

    bad_kind = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=headers,
        json={**base, "kind": "bogus"},
    )
    assert bad_kind.status_code == 400
    assert "Invalid kind" in bad_kind.json()["detail"]

    internal_project = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=headers,
        json={**base, "kind": "comment", "is_internal": True},
    )
    assert internal_project.status_code == 400
    assert "is_internal is only valid on task or ticket" in internal_project.json()["detail"]

    empty = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=headers,
        json={**base, "kind": "comment", "body": "   "},
    )
    assert empty.status_code == 400

    bad_parent = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=headers,
        json={**base, "kind": "comment", "parent_activity_id": str(uuid.uuid4())},
    )
    assert bad_parent.status_code == 400


async def test_pagination_and_subject_enrichment(client: AsyncClient, db: AsyncSession) -> None:
    user, project = await _project(db)
    headers = auth_header(user)
    for index in range(3):
        await _post_activity(client, user, project, {"body": f"page {index}"})

    first = await client.get(
        f"/v1/projects/{project.id}/activities?limit=2",
        headers=headers,
    )
    assert first.status_code == 200, first.text
    payload = first.json()
    assert payload["total"] == 3
    assert payload["has_more"] is True
    assert len(payload["items"]) == 2

    second = await client.get(
        f"/v1/projects/{project.id}/activities?limit=2&offset=2",
        headers=headers,
    )
    assert second.status_code == 200, second.text
    assert second.json()["has_more"] is False
    assert len(second.json()["items"]) == 1

    task = await _create_task(client, user, project, title="Enriched subject")
    task_activity = await _post_activity(
        client,
        user,
        project,
        {"subject_type": "task", "subject_id": task["id"], "body": "on a task"},
    )
    assert task_activity["subject_type"] == "task"

    by_task = await client.get(
        f"/v1/projects/{project.id}/activities?subject_type=task&subject_id={task['id']}",
        headers=headers,
    )
    assert by_task.status_code == 200, by_task.text
    rows = by_task.json()["items"]
    assert rows and all(row["subject_ref"] == task["ref"] for row in rows)
    assert all(row["subject_title"] == task["title"] for row in rows)


async def test_note_with_attachment_can_target_task(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, project = await _project(db)
    headers = auth_header(user)
    task = await _create_task(client, user, project, title="Attach here")

    # Composer selects the generic project upload before it knows the subject;
    # the API must accept that unbound attachment once it is linked to a task.
    upload = await client.post(
        f"/v1/projects/{project.id}/attachments",
        headers=headers,
        files={"file": ("pixel.png", PNG_BYTES, "image/png")},
    )
    assert upload.status_code == 201, upload.text
    attachment_id = upload.json()["id"]

    created = await _post_activity(
        client,
        user,
        project,
        {
            "subject_type": "task",
            "subject_id": task["id"],
            "body": "with an image",
            "meta_json": {"attachment_ids": [attachment_id]},
        },
    )
    assert created["meta_json"]["attachment_ids"] == [attachment_id]

    meta = await client.get(
        f"/v1/attachments?ids={attachment_id}",
        headers=headers,
    )
    assert meta.status_code == 200, meta.text
    rows = meta.json()
    assert len(rows) == 1
    assert rows[0]["id"] == attachment_id
    assert rows[0]["filename"] == "pixel.png"
    assert rows[0]["mime"] == "image/png"
    assert rows[0]["size_bytes"] == len(PNG_BYTES)
    assert "storage_key" not in rows[0]


async def test_attachment_cannot_cross_subjects_or_projects(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, project = await _project(db)
    other_user, other_project = await _project(db)
    headers = auth_header(user)
    task_a = await _create_task(client, user, project, title="Task A")
    task_b = await _create_task(client, user, project, title="Task B")

    task_upload = await client.post(
        f"/v1/projects/{project.id}/tasks/{task_a['id']}/attachments",
        headers=headers,
        files={"file": ("pixel.png", PNG_BYTES, "image/png")},
    )
    assert task_upload.status_code == 201, task_upload.text
    bound_id = task_upload.json()["id"]

    cross_subject = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=headers,
        json={
            "subject_type": "task",
            "subject_id": task_b["id"],
            "kind": "comment",
            "body": "must reject",
            "meta_json": {"attachment_ids": [bound_id]},
        },
    )
    assert cross_subject.status_code == 400
    assert "does not belong to this task" in cross_subject.json()["detail"]

    foreign_upload = await client.post(
        f"/v1/projects/{other_project.id}/attachments",
        headers=auth_header(other_user),
        files={"file": ("pixel.png", PNG_BYTES, "image/png")},
    )
    assert foreign_upload.status_code == 201, foreign_upload.text
    foreign_id = foreign_upload.json()["id"]

    cross_project = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=headers,
        json={
            "subject_type": "task",
            "subject_id": task_b["id"],
            "kind": "comment",
            "body": "must reject",
            "meta_json": {"attachment_ids": [foreign_id]},
        },
    )
    assert cross_project.status_code == 400
    assert "does not belong to this project" in cross_project.json()["detail"]


async def test_internal_visibility_and_client_portal_scoping(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _project(db)
    headers = auth_header(owner)

    client_user = await create_user(db, email=f"client-{uuid.uuid4().hex[:8]}@example.com")
    company = await create_client(
        db, slug=f"client-{uuid.uuid4().hex[:8]}", created_by=owner.id
    )
    contact = await create_client_contact(
        db,
        client_id=company.id,
        user_id=client_user.id,
        email=client_user.email,
    )
    db.add(
        ProjectClientAccess(
            project_id=project.id,
            client_contact_id=contact.id,
            role="contribute",
            can_view_tasks=True,
            can_view_tickets=False,
            created_by=owner.id,
        )
    )
    await db.commit()

    assigned_task = await _create_task(
        client, owner, project, title="Client visible", assignee_id=client_user.id
    )
    hidden_task = await _create_task(client, owner, project, title="Not assigned")

    public_note = await _post_activity(client, owner, project, {"body": "project public"})
    assigned_note = await _post_activity(
        client,
        owner,
        project,
        {
            "subject_type": "task",
            "subject_id": assigned_task["id"],
            "body": "assigned task comment",
        },
    )
    hidden_note = await _post_activity(
        client,
        owner,
        project,
        {
            "subject_type": "task",
            "subject_id": hidden_task["id"],
            "body": "other task comment",
        },
    )
    secret_upload = await client.post(
        f"/v1/projects/{project.id}/attachments",
        headers=headers,
        files={"file": ("secret.png", PNG_BYTES, "image/png")},
    )
    assert secret_upload.status_code == 201, secret_upload.text
    secret_attachment = secret_upload.json()["id"]
    secret_note = await _post_activity(
        client,
        owner,
        project,
        {
            "subject_type": "task",
            "subject_id": assigned_task["id"],
            "body": "internal secret",
            "is_internal": True,
            "meta_json": {"attachment_ids": [secret_attachment]},
        },
    )

    internal = await client.get(
        f"/v1/projects/{project.id}/activities?visibility=internal",
        headers=headers,
    )
    assert internal.status_code == 200, internal.text
    assert [row["id"] for row in internal.json()["items"]] == [secret_note["id"]]

    client_headers = auth_header(client_user)
    project_feed = await client.get(
        f"/v1/projects/{project.id}/activities?limit=200",
        headers=client_headers,
    )
    assert project_feed.status_code == 200, project_feed.text
    project_ids = {row["id"] for row in project_feed.json()["items"]}
    assert public_note["id"] in project_ids
    assert assigned_note["id"] in project_ids
    assert hidden_note["id"] not in project_ids
    assert secret_note["id"] not in project_ids

    hidden_visibility = await client.get(
        f"/v1/projects/{project.id}/activities?visibility=internal",
        headers=client_headers,
    )
    assert hidden_visibility.status_code == 403

    portal_feed = await client.get(
        f"/v1/me/client/projects/{project.id}/activities?limit=200",
        headers=client_headers,
    )
    assert portal_feed.status_code == 200, portal_feed.text
    portal_ids = {row["id"] for row in portal_feed.json()["items"]}
    assert public_note["id"] in portal_ids
    assert assigned_note["id"] in portal_ids
    assert hidden_note["id"] not in portal_ids
    assert secret_note["id"] not in portal_ids

    # Client participants cannot reply to an internal thread (not even when
    # they guess its id), and the API must not reveal that it exists.
    client_reply = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=client_headers,
        json={
            "subject_type": "task",
            "subject_id": assigned_task["id"],
            "kind": "comment",
            "body": "client reply to internal",
            "parent_activity_id": secret_note["id"],
        },
    )
    assert client_reply.status_code == 404

    # Internal-note attachments must not be downloadable by client participants,
    # even when they know the attachment UUID.
    client_meta = await client.get(
        f"/v1/attachments?ids={secret_attachment}",
        headers=client_headers,
    )
    assert client_meta.status_code == 200, client_meta.text
    assert client_meta.json() == []

    client_download = await client.get(
        f"/v1/attachments/{secret_attachment}",
        headers=client_headers,
    )
    assert client_download.status_code == 404

    owner_meta = await client.get(
        f"/v1/attachments?ids={secret_attachment}",
        headers=headers,
    )
    assert owner_meta.status_code == 200, owner_meta.text
    assert [row["id"] for row in owner_meta.json()] == [secret_attachment]

    owner_download = await client.get(
        f"/v1/attachments/{secret_attachment}",
        headers=headers,
    )
    assert owner_download.status_code == 200, owner_download.text
    assert owner_download.content == PNG_BYTES


async def test_reply_depth_and_cross_project_parent(client: AsyncClient, db: AsyncSession) -> None:
    user, project = await _project(db)
    other_user, other_project = await _project(db)
    headers = auth_header(user)

    parent = await _post_activity(client, user, project, {"body": "parent"})
    reply = await _post_activity(
        client,
        user,
        project,
        {"body": "reply", "parent_activity_id": parent["id"]},
    )
    nested = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=headers,
        json={
            "subject_type": "project",
            "subject_id": str(project.id),
            "kind": "comment",
            "body": "nested",
            "parent_activity_id": reply["id"],
        },
    )
    assert nested.status_code == 400
    assert "Nested replies" in nested.json()["detail"]

    foreign_parent = await _post_activity(client, other_user, other_project, {"body": "other"})
    cross_project = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=headers,
        json={
            "subject_type": "project",
            "subject_id": str(project.id),
            "kind": "comment",
            "body": "cross",
            "parent_activity_id": foreign_parent["id"],
        },
    )
    assert cross_project.status_code == 400
    assert "must belong to this project" in cross_project.json()["detail"]


async def test_github_ref_creates_one_commit_subject_ref(
    client: AsyncClient, db: AsyncSession
) -> None:
    from datetime import UTC, datetime

    from sqlalchemy import select

    from app.models.commit_subject_ref import CommitSubjectRef
    from app.models.github_commit import GithubCommit
    from app.models.github_link import GithubLink

    user, project = await _project(db)
    task = await _create_task(client, user, project, title="Commit-linked task")
    link = GithubLink(
        project_id=project.id,
        owner="acme",
        repo="widget",
        token_cipher="test-cipher",
        created_by=user.id,
    )
    db.add(link)
    await db.flush()
    commit = GithubCommit(
        github_link_id=link.id,
        sha="a" * 40,
        message="fix: link this commit\n\nBody",
        author_name="Tester",
        committed_at=datetime.now(UTC),
        html_url="https://github.com/acme/widget/commit/" + "a" * 40,
    )
    db.add(commit)
    await db.commit()

    github_ref = {
        "commit_id": str(commit.id),
        "sha": commit.sha,
        "owner": "acme",
        "repo": "widget",
        "html_url": commit.html_url,
    }
    body = {
        "subject_type": "task",
        "subject_id": task["id"],
        "kind": "comment",
        "body": "see commit",
        "meta_json": {"github_ref": github_ref},
    }
    first = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=auth_header(user),
        json=body,
    )
    assert first.status_code == 201, first.text
    assert first.json()["meta_json"]["github_ref"]["commit_id"] == str(commit.id)

    ref = await db.scalar(
        select(CommitSubjectRef).where(
            CommitSubjectRef.github_commit_id == commit.id,
            CommitSubjectRef.subject_type == "task",
            CommitSubjectRef.subject_id == task["id"],
        )
    )
    assert ref is not None
    assert ref.sha == commit.sha
    assert ref.created_by == user.id

    # Re-posting the same citation must not violate the unique ref constraint.
    second = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=auth_header(user),
        json={**body, "body": "see commit again"},
    )
    assert second.status_code == 201, second.text
    refs = (
        await db.scalars(
            select(CommitSubjectRef).where(CommitSubjectRef.github_commit_id == commit.id)
        )
    ).all()
    assert len(refs) == 1

    bad = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=auth_header(user),
        json={
            **body,
            "body": "bad commit",
            "meta_json": {"github_ref": {**github_ref, "commit_id": str(uuid.uuid4())}},
        },
    )
    assert bad.status_code == 400
    assert "Referenced commit not found" in bad.json()["detail"]


async def test_replies_to_internal_notes_stay_internal(
    client: AsyncClient, db: AsyncSession
) -> None:
    user, project = await _project(db)
    headers = auth_header(user)
    task = await _create_task(client, user, project, title="Internal thread")
    parent = await _post_activity(
        client,
        user,
        project,
        {
            "subject_type": "task",
            "subject_id": task["id"],
            "body": "internal parent",
            "is_internal": True,
        },
    )

    external_reply = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=headers,
        json={
            "subject_type": "task",
            "subject_id": task["id"],
            "kind": "comment",
            "body": "external reply",
            "parent_activity_id": parent["id"],
            "is_internal": False,
        },
    )
    assert external_reply.status_code == 400
    assert "must also be internal" in external_reply.json()["detail"]

    internal_reply = await client.post(
        f"/v1/projects/{project.id}/activities",
        headers=headers,
        json={
            "subject_type": "task",
            "subject_id": task["id"],
            "kind": "comment",
            "body": "internal reply",
            "parent_activity_id": parent["id"],
            "is_internal": True,
        },
    )
    assert internal_reply.status_code == 201, internal_reply.text
    assert internal_reply.json()["is_internal"] is True


async def test_client_only_sees_visible_commit_refs(
    client: AsyncClient, db: AsyncSession
) -> None:
    from datetime import UTC, datetime

    from app.models.github_commit import GithubCommit
    from app.models.github_link import GithubLink

    owner, project = await _project(db)
    owner_headers = auth_header(owner)

    client_user = await create_user(db, email=f"commit-client-{uuid.uuid4().hex[:8]}@example.com")
    company = await create_client(
        db, slug=f"client-{uuid.uuid4().hex[:8]}", created_by=owner.id
    )
    contact = await create_client_contact(
        db,
        client_id=company.id,
        user_id=client_user.id,
        email=client_user.email,
    )
    db.add(
        ProjectClientAccess(
            project_id=project.id,
            client_contact_id=contact.id,
            role="view",
            can_view_tasks=True,
            can_view_tickets=False,
            created_by=owner.id,
        )
    )
    await db.commit()

    assigned_task = await _create_task(
        client, owner, project, title="Visible task", assignee_id=client_user.id
    )
    hidden_task = await _create_task(client, owner, project, title="Hidden task")

    link = GithubLink(
        project_id=project.id,
        owner="acme",
        repo="widget",
        token_cipher="test-cipher",
        created_by=owner.id,
    )
    db.add(link)
    await db.flush()
    commit = GithubCommit(
        github_link_id=link.id,
        sha="b" * 40,
        message="fix: visible or not",
        author_name="Tester",
        committed_at=datetime.now(UTC),
        html_url="https://github.com/acme/widget/commit/" + "b" * 40,
    )
    db.add(commit)
    await db.commit()

    for task in (assigned_task, hidden_task):
        resp = await client.post(
            f"/v1/projects/{project.id}/github/refs",
            headers=owner_headers,
            json={
                "github_commit_id": str(commit.id),
                "subject_type": "task",
                "subject_id": task["id"],
            },
        )
        assert resp.status_code == 201, resp.text

    owner_refs = await client.get(
        f"/v1/projects/{project.id}/github/refs?github_commit_id={commit.id}",
        headers=owner_headers,
    )
    assert owner_refs.status_code == 200, owner_refs.text
    assert {row["subject_id"] for row in owner_refs.json()["items"]} == {
        assigned_task["id"],
        hidden_task["id"],
    }

    client_refs = await client.get(
        f"/v1/projects/{project.id}/github/refs?github_commit_id={commit.id}",
        headers=auth_header(client_user),
    )
    assert client_refs.status_code == 200, client_refs.text
    assert [row["subject_id"] for row in client_refs.json()["items"]] == [
        assigned_task["id"]
    ]

    hidden_filter = await client.get(
        f"/v1/projects/{project.id}/github/refs?subject_id={hidden_task['id']}",
        headers=auth_header(client_user),
    )
    assert hidden_filter.status_code == 200, hidden_filter.text
    assert hidden_filter.json()["items"] == []


async def test_mention_creates_inbox_entry(client: AsyncClient, db: AsyncSession) -> None:
    owner, project = await _project(db)
    target = await create_user(
        db, email=f"mentioned-{uuid.uuid4().hex[:8]}@example.com", display_name="Mentioned"
    )
    await db.commit()

    note = await _post_activity(
        client,
        owner,
        project,
        {"body": f"@{target.email} please review this"},
    )
    assert note["body"].startswith(f"@{target.email}")

    mentions = await client.get("/v1/me/mentions", headers=auth_header(target))
    assert mentions.status_code == 200, mentions.text
    items = mentions.json()["items"]
    assert len(items) == 1
    assert items[0]["project_id"] == str(project.id)
    assert "please review this" in items[0]["excerpt"]
