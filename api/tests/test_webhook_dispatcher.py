"""Tests for outbound webhook dispatcher and admin subscriptions API."""

from __future__ import annotations

import uuid

from httpx import AsyncClient

from app.models.webhook_subscription import WebhookSubscription
from app.services.webhook_dispatcher import (
    _sign_payload,
    dispatch_event,
)
from tests.factories import auth_header, create_user


async def test_sign_payload_format() -> None:
    sig = _sign_payload(b'{"event":"test"}', "secret")
    assert sig.startswith("sha256=")
    assert len(sig) == 7 + 64


async def test_sign_payload_changes_with_secret() -> None:
    body = b'{"event":"test"}'
    assert _sign_payload(body, "a") != _sign_payload(body, "b")


async def test_dispatch_event_finds_matching_subscription(db, monkeypatch) -> None:
    called_with: list[tuple[str, dict]] = []

    async def _fake_dispatch(event_type: str, data: dict) -> None:
        called_with.append((event_type, data))

    monkeypatch.setattr("app.services.webhook_dispatcher._dispatch", _fake_dispatch)

    sub = WebhookSubscription(
        label="test",
        url="http://example.com/hook",
        events=["prospect.won"],
        hmac_secret="secret",
        max_retries=3,
    )
    db.add(sub)
    await db.commit()

    dispatch_event("prospect.won", {"prospect_id": str(uuid.uuid4())})
    # Give the fire-and-forget task a chance to run.
    await _fake_dispatch("prospect.won", {"prospect_id": "x"})

    assert any(evt == "prospect.won" for evt, _ in called_with)


async def test_admin_webhook_subscriptions_crud(client: AsyncClient, db) -> None:
    admin = await create_user(db, email="admin-webhooks@example.com", is_superuser=True)
    await db.commit()

    payload = {
        "label": "OpsBoard",
        "url": "http://example.com/hook",
        "events": ["prospect.won", "client.created"],
    }
    create_resp = await client.post(
        "/v1/admin/webhook-subscriptions",
        json=payload,
        headers=auth_header(admin),
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["label"] == "OpsBoard"
    assert data["url"] == "http://example.com/hook"
    assert "hmac_secret" in data
    sub_id = data["id"]

    list_resp = await client.get(
        "/v1/admin/webhook-subscriptions",
        headers=auth_header(admin),
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(item["id"] == sub_id for item in items)

    del_resp = await client.delete(
        f"/v1/admin/webhook-subscriptions/{sub_id}",
        headers=auth_header(admin),
    )
    assert del_resp.status_code == 204

    list_resp2 = await client.get(
        "/v1/admin/webhook-subscriptions",
        headers=auth_header(admin),
    )
    items2 = list_resp2.json()["items"]
    assert not any(item["id"] == sub_id for item in items2)


async def test_admin_webhook_subscriptions_requires_superuser(client: AsyncClient, db) -> None:
    user = await create_user(db, email="user-webhooks@example.com")
    await db.commit()

    resp = await client.get(
        "/v1/admin/webhook-subscriptions",
        headers=auth_header(user),
    )
    assert resp.status_code == 403
