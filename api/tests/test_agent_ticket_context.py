"""Agent attachment read + visibility tests (SPEC amendment 01 §R7).

Covers the P0 attachment surface. The agent routes are superuser-gated today
(SPEC Q1), so client-participant visibility is exercised through the shared
resolver and the web route that reuse it — the agent route itself will enforce
the same rule unchanged once the gate relaxes.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.attachment import Attachment
from app.models.commit_subject_ref import CommitSubjectRef
from app.models.github_commit import GithubCommit
from app.models.github_link import GithubLink
from app.models.project import Project
from app.models.project_client_access import ProjectClientAccess
from app.models.tenant import Tenant
from app.models.ticket import Ticket
from app.models.user import User
from app.models.user_api_key import UserApiKey
from app.models.watcher import Watcher
from app.routers.agent_query import _require_ticket_visible
from app.services.attachment_serve import is_attachment_visible
from app.services.attachment_storage import path_for_key
from app.services.project_access import MemberRole, resolve_project_access
from app.services.tenancy import ensure_default_tenant
from tests.factories import (
    add_member,
    auth_header,
    create_client,
    create_client_contact,
    create_project,
    create_user,
)

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 64
AGENT_KEY = "tools_project_agent_test_key"


@pytest.fixture(autouse=True)
def attachments_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    target = tmp_path / "attachments"
    monkeypatch.setenv("ATTACHMENTS_DIR", str(target))
    return target


async def _owner_and_project(db: AsyncSession) -> tuple[User, Project]:
    owner = await create_user(
        db,
        email=f"owner-{uuid.uuid4().hex[:8]}@example.com",
        is_superuser=True,
    )
    project = await create_project(
        db,
        slug=f"proj-{uuid.uuid4().hex[:8]}",
        owner_id=owner.id,
    )
    await add_member(db, project.id, owner.id, MemberRole.owner)
    return owner, project


async def _ticket(
    db: AsyncSession,
    project: Project,
    owner: User,
    assignee_id: uuid.UUID | None = None,
    *,
    description: str = "see screenshot",
    ref: str | None = None,
) -> Ticket:
    ticket = Ticket(
        project_id=project.id,
        ref=ref,
        title="Ticket with evidence",
        description=description,
        reporter_id=owner.id,
        assignee_id=assignee_id,
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)
    return ticket


async def _attachment(
    db: AsyncSession,
    *,
    project: Project,
    created_by: User,
    ticket_id: uuid.UUID | None = None,
    activity_id: uuid.UUID | None = None,
    mime: str = "image/png",
    data: bytes = PNG_BYTES,
    filename: str = "Screenshot 2026-10-19.png",
    storage_key: str | None = None,
) -> Attachment:
    key = storage_key or f"{uuid.uuid4().hex}.png"
    if storage_key is None:
        path_for_key(key).write_bytes(data)
    row = Attachment(
        project_id=project.id,
        ticket_id=ticket_id,
        activity_id=activity_id,
        filename=filename,
        mime=mime,
        size_bytes=len(data),
        storage_key=key,
        created_by=created_by.id,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def _personal_key(db: AsyncSession, user: User) -> str:
    db.add(
        UserApiKey(
            user_id=user.id,
            key_hash=hashlib.sha256(AGENT_KEY.encode()).hexdigest(),
            key_prefix=AGENT_KEY[:8],
            label="test",
            tenant_id=(await ensure_default_tenant(db)).id,
        )
    )
    await db.flush()
    return AGENT_KEY


async def _client_participant(
    db: AsyncSession,
    project: Project,
    owner: User,
    *,
    can_view_tickets: bool = True,
) -> User:
    client_user = await create_user(
        db, email=f"client-{uuid.uuid4().hex[:8]}@example.com"
    )
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
            can_view_tickets=can_view_tickets,
            created_by=owner.id,
        )
    )
    await db.commit()
    return client_user


async def test_attachment_download_streams_bytes(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)
    row = await _attachment(db, project=project, created_by=owner, ticket_id=ticket.id)

    response = await client.get(
        f"/v1/agent/attachments/{row.id}", headers=auth_header(owner)
    )

    assert response.status_code == 200
    assert response.content == PNG_BYTES
    assert response.headers["content-type"] == "image/png"
    assert response.headers["content-length"] == str(len(PNG_BYTES))
    assert "inline" in response.headers["content-disposition"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-security-policy"] == "sandbox"
    assert response.headers["cache-control"] == "private, max-age=0, no-store"
    assert "etag" not in response.headers


async def test_attachment_download_with_personal_key(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)
    row = await _attachment(db, project=project, created_by=owner, ticket_id=ticket.id)
    key = await _personal_key(db, owner)

    response = await client.get(
        f"/v1/agent/attachments/{row.id}", headers={"X-Api-Key": key}
    )

    assert response.status_code == 200
    assert response.content == PNG_BYTES


async def test_attachment_download_requires_auth(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)
    row = await _attachment(db, project=project, created_by=owner, ticket_id=ticket.id)

    response = await client.get(f"/v1/agent/attachments/{row.id}")

    assert response.status_code == 401


async def test_attachment_download_non_superuser_is_403(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)
    row = await _attachment(db, project=project, created_by=owner, ticket_id=ticket.id)
    member = await create_user(db, email=f"member-{uuid.uuid4().hex[:8]}@example.com")
    await add_member(db, project.id, member.id, MemberRole.contributor)

    response = await client.get(
        f"/v1/agent/attachments/{row.id}", headers=auth_header(member)
    )

    assert response.status_code == 403


async def test_attachment_download_unknown_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, _project = await _owner_and_project(db)

    response = await client.get(
        f"/v1/agent/attachments/{uuid.uuid4()}", headers=auth_header(owner)
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "attachment_not_found"


async def test_attachment_download_bad_storage_key_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    row = await _attachment(
        db,
        project=project,
        created_by=owner,
        storage_key="../etc/passwd",
    )

    response = await client.get(
        f"/v1/agent/attachments/{row.id}", headers=auth_header(owner)
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "attachment_not_found"


async def test_attachment_download_disallowed_mime_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    row = await _attachment(
        db, project=project, created_by=owner, mime="image/svg+xml"
    )

    response = await client.get(
        f"/v1/agent/attachments/{row.id}", headers=auth_header(owner)
    )

    assert response.status_code == 404


async def test_attachment_download_disposition(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    row = await _attachment(db, project=project, created_by=owner)

    inline = await client.get(
        f"/v1/agent/attachments/{row.id}", headers=auth_header(owner)
    )
    download = await client.get(
        f"/v1/agent/attachments/{row.id}?download=1", headers=auth_header(owner)
    )

    assert inline.headers["content-disposition"].startswith("inline")
    assert download.headers["content-disposition"].startswith("attachment")


async def test_internal_note_attachment_hidden_from_client(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    client_user = await _client_participant(db, project, owner)
    ticket = await _ticket(db, project, owner, assignee_id=client_user.id)

    note = Activity(
        project_id=project.id,
        subject_type="ticket",
        subject_id=ticket.id,
        kind="comment",
        actor_id=owner.id,
        body="internal note",
        is_internal=True,
    )
    db.add(note)
    await db.flush()
    row = await _attachment(
        db, project=project, created_by=owner, ticket_id=ticket.id, activity_id=note.id
    )

    hidden = await client.get(f"/v1/attachments/{row.id}", headers=auth_header(client_user))
    staff = await client.get(f"/v1/attachments/{row.id}", headers=auth_header(owner))

    assert hidden.status_code == 404
    assert staff.status_code == 200


async def test_subject_visibility_for_client_participant(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    client_user = await _client_participant(db, project, owner)
    assigned = await _ticket(db, project, owner, assignee_id=client_user.id)
    other_company = await _ticket(db, project, owner)

    visible = await _attachment(db, project=project, created_by=owner, ticket_id=assigned.id)
    hidden = await _attachment(
        db, project=project, created_by=owner, ticket_id=other_company.id
    )

    ok = await client.get(f"/v1/attachments/{visible.id}", headers=auth_header(client_user))
    denied = await client.get(f"/v1/attachments/{hidden.id}", headers=auth_header(client_user))

    assert ok.status_code == 200
    assert denied.status_code == 404

    # The same shared predicate the agent route calls (superuser gate today).
    acc = await resolve_project_access(db, client_user, project.id)
    assert acc is not None
    assert await is_attachment_visible(db, acc, visible) is True
    assert await is_attachment_visible(db, acc, hidden) is False


async def test_client_without_ticket_permission_cannot_read_ticket_attachment(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    client_user = await _client_participant(
        db, project, owner, can_view_tickets=False
    )
    ticket = await _ticket(db, project, owner, assignee_id=client_user.id)
    row = await _attachment(db, project=project, created_by=owner, ticket_id=ticket.id)

    response = await client.get(f"/v1/attachments/{row.id}", headers=auth_header(client_user))

    assert response.status_code == 404


# ── Ticket detail (T4/T6: amendment tests #1–#8) ──────────────────────


async def test_detail_by_uuid_and_ref(client: AsyncClient, db: AsyncSession) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner, ref=f"TST-T-{uuid.uuid4().hex[:8]}")

    by_uuid = await client.get(f"/v1/agent/tickets/{ticket.id}", headers=auth_header(owner))
    by_ref = await client.get(
        f"/v1/agent/tickets/{ticket.ref.lower()}", headers=auth_header(owner)
    )

    assert by_uuid.status_code == 200
    assert by_ref.status_code == 200
    a = by_uuid.json()["data"]["ticket"]
    b = by_ref.json()["data"]["ticket"]
    assert a["id"] == b["id"] == str(ticket.id)
    assert a["ref"] == b["ref"] == ticket.ref
    assert by_uuid.json()["data"]["agent_api_version"] == "1.1.0"


async def test_detail_unknown_ticket_is_404(client: AsyncClient, db: AsyncSession) -> None:
    owner, _project = await _owner_and_project(db)

    response = await client.get(
        f"/v1/agent/tickets/{uuid.uuid4()}", headers=auth_header(owner)
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "ticket_not_found"


@pytest.mark.usefixtures("multi_tenant_on")
async def test_detail_other_tenant_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, _project_a = await _owner_and_project(db)
    tenant_b = Tenant(slug=f"b-{uuid.uuid4().hex[:8]}", name="Tenant B")
    db.add(tenant_b)
    await db.flush()
    project_b = await create_project(
        db, slug=f"proj-b-{uuid.uuid4().hex[:8]}", owner_id=owner.id, tenant_id=tenant_b.id
    )
    ticket_b = await _ticket(db, project_b, owner)

    response = await client.get(
        f"/v1/agent/tickets/{ticket_b.id}", headers=auth_header(owner)
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "ticket_not_found"


async def test_detail_requires_superuser(client: AsyncClient, db: AsyncSession) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)
    member = await create_user(db, email=f"member-{uuid.uuid4().hex[:8]}@example.com")
    await add_member(db, project.id, member.id, MemberRole.contributor)

    anonymous = await client.get(f"/v1/agent/tickets/{ticket.id}")
    non_superuser = await client.get(
        f"/v1/agent/tickets/{ticket.id}", headers=auth_header(member)
    )

    assert anonymous.status_code == 401
    assert non_superuser.status_code == 403


async def test_detail_resolves_description_and_attachments(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)
    att = await _attachment(db, project=project, created_by=owner, ticket_id=ticket.id)
    description = f"Evidence ![shot.png](/api/attachments/{att.id})"
    ticket.description = description
    await db.flush()

    response = await client.get(
        f"/v1/agent/tickets/{ticket.id}", headers=auth_header(owner)
    )

    assert response.status_code == 200
    payload = response.json()["data"]["ticket"]
    assert payload["description"] == description
    assert f"/v1/agent/attachments/{att.id}" in payload["description_resolved"]
    assert payload["description_resolved"].startswith("Evidence ![shot.png](http")
    assert payload["attachments"][0]["markdown_ref"] == f"/api/attachments/{att.id}"
    assert payload["attachments"][0]["download_url"].endswith(
        f"/v1/agent/attachments/{att.id}"
    )
    assert payload["counts"]["attachments"] == 1
    assert payload["attachments_truncated"] is False
    assert "storage_key" not in response.text


async def test_detail_unknown_attachment_ref_left_untouched(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    missing = uuid.uuid4()
    description = f"Broken ![shot.png](/api/attachments/{missing})"
    ticket = await _ticket(db, project, owner, description=description)

    response = await client.get(
        f"/v1/agent/tickets/{ticket.id}", headers=auth_header(owner)
    )

    assert response.status_code == 200
    payload = response.json()["data"]["ticket"]
    assert payload["description_resolved"] == description
    assert payload["attachments"] == []


async def test_detail_includes_activities_commits_and_watchers(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)

    public = Activity(
        project_id=project.id,
        subject_type="ticket",
        subject_id=ticket.id,
        kind="comment",
        actor_id=owner.id,
        body="public reply",
        is_internal=False,
    )
    internal = Activity(
        project_id=project.id,
        subject_type="ticket",
        subject_id=ticket.id,
        kind="comment",
        actor_id=owner.id,
        body="internal note",
        is_internal=True,
    )
    db.add_all([public, internal])
    await db.flush()
    comment_file = await _attachment(
        db, project=project, created_by=owner, ticket_id=ticket.id, activity_id=public.id
    )

    link = GithubLink(
        project_id=project.id,
        owner="org",
        repo="repo",
        token_cipher="x",
        created_by=owner.id,
    )
    db.add(link)
    await db.flush()
    commit = GithubCommit(
        github_link_id=link.id,
        sha="a" * 40,
        message="TST-T-1: fix the thing\n\nbody",
        author_name="Dev",
        committed_at=datetime.now(UTC),
        html_url="https://github.com/org/repo/commit/abc",
    )
    db.add(commit)
    await db.flush()
    db.add(
        CommitSubjectRef(
            github_commit_id=commit.id,
            sha=commit.sha,
            project_id=project.id,
            subject_type="ticket",
            subject_id=ticket.id,
            created_by=owner.id,
        )
    )
    db.add(Watcher(user_id=owner.id, subject_type="ticket", subject_id=ticket.id))
    await db.flush()

    response = await client.get(
        f"/v1/agent/tickets/{ticket.id}", headers=auth_header(owner)
    )

    assert response.status_code == 200
    payload = response.json()["data"]["ticket"]
    assert payload["counts"]["activities"] == 2
    assert {item["body"] for item in payload["activities"]} == {"public reply", "internal note"}
    assert payload["activities_page"]["order"] == "desc"
    public_item = next(i for i in payload["activities"] if i["body"] == "public reply")
    assert public_item["attachments"][0]["id"] == str(comment_file.id)
    assert payload["linked_commits"][0]["state"] == "resolved"
    assert payload["linked_commits"][0]["html_url"].startswith("https://github.com/")
    assert payload["linked_commits"][0]["short_sha"] == "a" * 7
    assert payload["watchers"][0]["id"] == str(owner.id)
    assert payload["reporter"]["email"] == owner.email


async def test_detail_attachments_capped_with_flag(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)
    for _ in range(201):
        await _attachment(db, project=project, created_by=owner, ticket_id=ticket.id)

    response = await client.get(
        f"/v1/agent/tickets/{ticket.id}", headers=auth_header(owner)
    )

    assert response.status_code == 200
    payload = response.json()["data"]["ticket"]
    assert len(payload["attachments"]) == 200
    assert payload["attachments_truncated"] is True
    assert payload["counts"]["attachments"] == 201


async def test_client_participant_ticket_visibility_rule(db: AsyncSession) -> None:
    # The agent routes are superuser-gated today (SPEC Q1), so the rule the route
    # calls is exercised directly; it is the same helper the route invokes.
    owner, project = await _owner_and_project(db)
    client_user = await _client_participant(db, project, owner)
    assigned = await _ticket(db, project, owner, assignee_id=client_user.id)
    other = await _ticket(db, project, owner)

    acc = await resolve_project_access(db, client_user, project.id)
    assert acc is not None

    await _require_ticket_visible(db, acc, assigned)
    with pytest.raises(HTTPException) as exc:
        await _require_ticket_visible(db, acc, other)
    assert exc.value.status_code == 404


async def test_detail_can_omit_activities(client: AsyncClient, db: AsyncSession) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)

    response = await client.get(
        f"/v1/agent/tickets/{ticket.id}?include_activities=false",
        headers=auth_header(owner),
    )

    assert response.status_code == 200
    payload = response.json()["data"]["ticket"]
    assert "activities" not in payload
    assert "activities_page" not in payload
    assert payload["counts"]["activities"] == 0


# ── Web-URL resolution + activity pagination (integration completeness) ──


async def test_detail_resolves_from_web_url(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)

    url = f"https://project.cloudsys.win/projects/{project.id}/tickets/{ticket.id}"
    from_url = await client.get(
        "/v1/agent/tickets/resolve",
        params={"url": url},
        headers=auth_header(owner),
    )

    by_id = await client.get(f"/v1/agent/tickets/{ticket.id}", headers=auth_header(owner))

    assert from_url.status_code == 200
    assert from_url.json()["data"]["ticket"]["id"] == by_id.json()["data"]["ticket"]["id"]


async def test_detail_resolves_from_relative_url_with_trailing_slash(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)

    response = await client.get(
        "/v1/agent/tickets/resolve",
        params={"url": f"/projects/{project.id}/tickets/{ticket.id}/"},
        headers=auth_header(owner),
    )

    assert response.status_code == 200
    assert response.json()["data"]["ticket"]["ref"] == ticket.ref


async def test_resolve_url_without_ticket_segment_is_400(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, _project = await _owner_and_project(db)

    response = await client.get(
        "/v1/agent/tickets/resolve",
        params={"url": "https://project.cloudsys.win/"},
        headers=auth_header(owner),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid_ticket_url"


async def test_resolve_unknown_ticket_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    missing = uuid.uuid4()

    response = await client.get(
        "/v1/agent/tickets/resolve",
        params={"url": f"https://host/projects/{project.id}/tickets/{missing}"},
        headers=auth_header(owner),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "ticket_not_found"


async def _comment(
    db: AsyncSession,
    project: Project,
    ticket: Ticket,
    owner: User,
    *,
    body: str,
    created_at: datetime,
    is_internal: bool = False,
) -> Activity:
    row = Activity(
        project_id=project.id,
        subject_type="ticket",
        subject_id=ticket.id,
        kind="comment",
        actor_id=owner.id,
        body=body,
        is_internal=is_internal,
        created_at=created_at,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def test_detail_activity_page_is_the_most_recent(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)
    for index in range(3):
        await _comment(
            db,
            project,
            ticket,
            owner,
            body=f"comment-{index}",
            created_at=datetime(2026, 10, 19, 12, index, tzinfo=UTC),
        )

    response = await client.get(
        f"/v1/agent/tickets/{ticket.id}?activity_limit=2", headers=auth_header(owner)
    )

    assert response.status_code == 200
    payload = response.json()["data"]["ticket"]
    assert [item["body"] for item in payload["activities"]] == ["comment-2", "comment-1"]
    assert payload["activities_page"] == {
        "total": 3,
        "has_more": True,
        "next_offset": 2,
        "order": "desc",
    }


async def test_activities_pagination_and_order(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)
    for index in range(3):
        await _comment(
            db,
            project,
            ticket,
            owner,
            body=f"comment-{index}",
            created_at=datetime(2026, 10, 19, 12, index, tzinfo=UTC),
        )

    first = await client.get(
        f"/v1/agent/tickets/{ticket.id}/activities?limit=2&order=desc",
        headers=auth_header(owner),
    )
    older = await client.get(
        f"/v1/agent/tickets/{ticket.id}/activities?limit=2&offset=2&order=desc",
        headers=auth_header(owner),
    )
    ascending = await client.get(
        f"/v1/agent/tickets/{ticket.id}/activities?limit=2&order=asc",
        headers=auth_header(owner),
    )

    assert first.status_code == 200
    page = first.json()["data"]
    assert [item["body"] for item in page["items"]] == ["comment-2", "comment-1"]
    assert page["total"] == 3
    assert page["has_more"] is True
    assert page["next_offset"] == 2
    assert page["order"] == "desc"

    assert [item["body"] for item in older.json()["data"]["items"]] == ["comment-0"]
    assert older.json()["data"]["has_more"] is False
    assert older.json()["data"]["next_offset"] is None

    assert [item["body"] for item in ascending.json()["data"]["items"]] == [
        "comment-0",
        "comment-1",
    ]


async def test_activities_internal_filter_and_kind(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)
    public = await _comment(
        db,
        project,
        ticket,
        owner,
        body="public",
        created_at=datetime(2026, 10, 19, 12, 0, tzinfo=UTC),
    )
    await _comment(
        db,
        project,
        ticket,
        owner,
        body="internal",
        created_at=datetime(2026, 10, 19, 12, 1, tzinfo=UTC),
        is_internal=True,
    )
    transition = Activity(
        project_id=project.id,
        subject_type="ticket",
        subject_id=ticket.id,
        kind="status_change",
        actor_id=owner.id,
        body="open → in_progress",
        meta_json={"from": "open", "to": "in_progress"},
        created_at=datetime(2026, 10, 19, 12, 2, tzinfo=UTC),
    )
    db.add(transition)
    await db.flush()

    everything = await client.get(
        f"/v1/agent/tickets/{ticket.id}/activities", headers=auth_header(owner)
    )
    external = await client.get(
        f"/v1/agent/tickets/{ticket.id}/activities?include_internal=false",
        headers=auth_header(owner),
    )
    internal_only = await client.get(
        f"/v1/agent/tickets/{ticket.id}/activities?visibility=internal",
        headers=auth_header(owner),
    )
    status_only = await client.get(
        f"/v1/agent/tickets/{ticket.id}/activities?kind=status_change",
        headers=auth_header(owner),
    )

    assert everything.json()["data"]["total"] == 3
    assert {item["body"] for item in external.json()["data"]["items"]} == {
        "public",
        "open → in_progress",
    }
    assert [item["body"] for item in internal_only.json()["data"]["items"]] == ["internal"]
    assert [item["body"] for item in status_only.json()["data"]["items"]] == [
        "open → in_progress"
    ]
    assert public.id is not None


async def test_activities_include_comment_attachments(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project = await _owner_and_project(db)
    ticket = await _ticket(db, project, owner)
    comment = await _comment(
        db,
        project,
        ticket,
        owner,
        body="see file",
        created_at=datetime(2026, 10, 19, 12, 0, tzinfo=UTC),
    )
    attachment = await _attachment(
        db, project=project, created_by=owner, ticket_id=ticket.id, activity_id=comment.id
    )

    response = await client.get(
        f"/v1/agent/tickets/{ticket.id}/activities", headers=auth_header(owner)
    )

    item = response.json()["data"]["items"][0]
    assert item["attachments"][0]["id"] == str(attachment.id)
    assert item["attachments"][0]["scope"] == "activity"


async def test_activities_unknown_ticket_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, _project = await _owner_and_project(db)

    response = await client.get(
        f"/v1/agent/tickets/{uuid.uuid4()}/activities", headers=auth_header(owner)
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "ticket_not_found"


# ── P2: capabilities, served client file, context counts, ticket filter ──


async def test_capabilities_handshake(client: AsyncClient, db: AsyncSession) -> None:
    owner, _project = await _owner_and_project(db)
    member = await create_user(db, email=f"member-{uuid.uuid4().hex[:8]}@example.com")

    response = await client.get("/v1/agent/capabilities", headers=auth_header(owner))
    anonymous = await client.get("/v1/agent/capabilities")
    non_superuser = await client.get(
        "/v1/agent/capabilities", headers=auth_header(member)
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["agent_api_version"] == "1.1.0"
    assert {"ticket_detail", "ticket_activities", "attachment_download"} <= set(
        data["capabilities"]
    )
    assert data["limits"]["activities_max"] == 200
    assert data["limits"]["attachment_max_bytes"] == 25 * 1024 * 1024
    assert data["recommended_mcp_server_version"] == "1.1.0"
    assert data["mcp_server_download_url"].endswith("/v1/agent/client/mcp_server.py")
    assert anonymous.status_code == 401
    assert non_superuser.status_code == 403


async def test_served_mcp_file_matches_packaged_module(
    client: AsyncClient, db: AsyncSession
) -> None:
    from app.client import mcp_server as packaged

    owner, _project = await _owner_and_project(db)

    response = await client.get(
        "/v1/agent/client/mcp_server.py", headers=auth_header(owner)
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/x-python")
    assert response.headers["content-disposition"].startswith("attachment")
    assert response.headers["x-mcp-server-version"] == packaged.SERVER_VERSION
    assert response.content == Path(packaged.__file__).read_bytes()


async def test_context_counts_are_real(client: AsyncClient, db: AsyncSession) -> None:
    owner, project = await _owner_and_project(db)
    for _ in range(2):
        member = await create_user(db, email=f"m-{uuid.uuid4().hex[:8]}@example.com")
        await add_member(db, project.id, member.id, MemberRole.contributor)

    from app.models.task import Task

    for index, status in enumerate(("todo", "in_progress", "done")):
        db.add(
            Task(
                project_id=project.id,
                title=f"task-{index}",
                status=status,
                reporter_id=owner.id,
            )
        )
    for index, status in enumerate(("open", "open", "in_progress", "resolved")):
        db.add(
            Ticket(
                project_id=project.id,
                title=f"ticket-{index}",
                description=None,
                status=status,
                reporter_id=owner.id,
            )
        )
    await db.flush()

    response = await client.get(
        f"/v1/agent/projects/{project.id}/context", headers=auth_header(owner)
    )

    assert response.status_code == 200
    project_data = response.json()["data"]["project"]
    assert project_data["member_count"] == 3
    assert project_data["open_tasks"] == 2
    assert project_data["tasks_total"] == 3
    assert project_data["open_tickets"] == 3
    assert project_data["tickets_total"] == 4
    assert project_data["tasks_truncated"] is False
    assert project_data["tickets_truncated"] is False


async def test_context_counts_report_truncation(
    client: AsyncClient, db: AsyncSession
) -> None:
    from app.models.task import Task

    owner, project = await _owner_and_project(db)
    db.add_all(
        [
            Task(project_id=project.id, title=f"bulk-{index}", reporter_id=owner.id)
            for index in range(101)
        ]
    )
    await db.flush()

    response = await client.get(
        f"/v1/agent/projects/{project.id}/context", headers=auth_header(owner)
    )

    project_data = response.json()["data"]["project"]
    assert project_data["tasks_total"] == 101
    assert project_data["tasks_truncated"] is True
    assert len(response.json()["data"]["tasks"]) == 100


async def test_ticket_list_filters_by_project(
    client: AsyncClient, db: AsyncSession
) -> None:
    owner, project_a = await _owner_and_project(db)
    project_b = await create_project(
        db, slug=f"proj-b-{uuid.uuid4().hex[:8]}", owner_id=owner.id
    )
    ticket_a = await _ticket(db, project_a, owner)
    ticket_b = await _ticket(db, project_b, owner)

    filtered = await client.get(
        f"/v1/agent/tickets?project_id={project_a.id}&limit=200",
        headers=auth_header(owner),
    )
    unknown = await client.get(
        f"/v1/agent/tickets?project_id={uuid.uuid4()}", headers=auth_header(owner)
    )

    assert filtered.status_code == 200
    ids = {item["id"] for item in filtered.json()["data"]}
    assert str(ticket_a.id) in ids
    assert str(ticket_b.id) not in ids
    assert unknown.status_code == 200
    assert unknown.json()["data"] == []
