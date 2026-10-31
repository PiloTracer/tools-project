"""Webhook subscription monitoring fields (integration error/observability surface)."""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import auth_header, create_user


async def test_subscription_creation_and_listing_expose_monitoring_fields(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin = await create_user(
        db, email=f"admin-{uuid.uuid4().hex[:8]}@example.com", is_superuser=True
    )

    created = await client.post(
        "/v1/admin/webhook-subscriptions",
        headers=auth_header(admin),
        json={
            "url": "https://example.test/hook",
            "events": ["ticket.created"],
            "label": "ops-bot",
        },
    )

    assert created.status_code == 201
    body = created.json()
    assert body["hmac_secret"].startswith("whsec_")
    assert body["last_delivered_at"] is None

    listed = await client.get(
        "/v1/admin/webhook-subscriptions", headers=auth_header(admin)
    )

    assert listed.status_code == 200
    item = next(i for i in listed.json()["items"] if i["id"] == body["id"])
    assert item["last_delivered_at"] is None
    # The full secret is only returned once; the list exposes a masked prefix.
    assert item["hmac_secret"] != body["hmac_secret"]
    assert item["hmac_secret"].endswith("...")


async def test_subscription_endpoints_require_superuser(
    client: AsyncClient, db: AsyncSession
) -> None:
    member = await create_user(db, email=f"member-{uuid.uuid4().hex[:8]}@example.com")

    response = await client.get(
        "/v1/admin/webhook-subscriptions", headers=auth_header(member)
    )

    assert response.status_code == 403
