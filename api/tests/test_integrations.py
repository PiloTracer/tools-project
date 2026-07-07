"""Tests for inbound integrations (RFP award webhook)."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid

from httpx import AsyncClient

from tests.factories import create_user


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


async def test_rfp_award_webhook_creates_client_and_project(client: AsyncClient, db) -> None:
    # Ensure a bootstrap superuser exists so the pipeline has a system actor.
    await create_user(db, email="admin-integration@example.com", is_superuser=True)
    await db.commit()

    payload = {
        "company_name": "Acme Corp",
        "contact_email": "acme@example.com",
        "contact_name": "Alice Acme",
        "rfp_title": "Widget RFP",
    }
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": _sign(body, "test-rfp-secret"),
        "X-Idempotency-Key": str(uuid.uuid4()),
    }

    resp = await client.post("/v1/integrations/rfp/award", content=body, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["client_name"] == "Acme Corp"
    assert data["project_name"].startswith("Acme Corp")
    assert "client_id" in data
    assert "project_id" in data


async def test_rfp_award_rejects_bad_signature(client: AsyncClient) -> None:
    payload = {"company_name": "Acme Corp", "contact_email": "acme@example.com"}
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": _sign(body, "wrong-secret"),
    }

    resp = await client.post("/v1/integrations/rfp/award", content=body, headers=headers)
    assert resp.status_code == 401


async def test_rfp_award_idempotency_returns_same_result(client: AsyncClient, db) -> None:
    await create_user(db, email="admin-idem@example.com", is_superuser=True)
    await db.commit()

    idem_key = str(uuid.uuid4())
    payload = {"company_name": "Stable Corp", "contact_email": "stable@example.com"}
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": _sign(body, "test-rfp-secret"),
        "X-Idempotency-Key": idem_key,
    }

    resp1 = await client.post("/v1/integrations/rfp/award", content=body, headers=headers)
    assert resp1.status_code == 201

    resp2 = await client.post("/v1/integrations/rfp/award", content=body, headers=headers)
    assert resp2.status_code == 201
    assert resp2.json() == resp1.json()


async def test_rfp_award_idempotency_conflict_on_payload_change(client: AsyncClient, db) -> None:
    await create_user(db, email="admin-conflict@example.com", is_superuser=True)
    await db.commit()

    idem_key = str(uuid.uuid4())
    body1 = json.dumps({"company_name": "A Corp", "contact_email": "a@example.com"}).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": _sign(body1, "test-rfp-secret"),
        "X-Idempotency-Key": idem_key,
    }
    resp1 = await client.post("/v1/integrations/rfp/award", content=body1, headers=headers)
    assert resp1.status_code == 201

    body2 = json.dumps({"company_name": "B Corp", "contact_email": "b@example.com"}).encode()
    headers2 = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": _sign(body2, "test-rfp-secret"),
        "X-Idempotency-Key": idem_key,
    }
    resp2 = await client.post("/v1/integrations/rfp/award", content=body2, headers=headers2)
    assert resp2.status_code == 409
