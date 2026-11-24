"""CRM org/contact profile fields on prospects and clients."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.prospect import Prospect
from app.services.crm_profile import (
    CLIENT_PROFILE_KEYS,
    PROSPECT_PROFILE_KEYS,
    apply_profile_update,
    blank_to_none,
    email_or_none,
    profile_kwargs,
)
from tests.factories import auth_header, create_user


class _Body:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.model_fields_set = set(kwargs)


async def test_crm_profile_helpers_normalize() -> None:
    assert blank_to_none("  ") is None
    assert blank_to_none("  hi ") == "hi"
    assert email_or_none("  Alice@Acme.COM ") == "alice@acme.com"
    assert email_or_none("   ") is None

    body = _Body(
        contact_name="  Jane  ",
        contact_email="Jane@Acme.com",
        org_email="",
        latitude=9.93,
        longitude=None,
    )
    out = profile_kwargs(body, PROSPECT_PROFILE_KEYS)
    assert out["contact_name"] == "Jane"
    assert out["contact_email"] == "jane@acme.com"
    assert out["org_email"] is None
    assert out["latitude"] == 9.93
    assert out["longitude"] is None


async def test_apply_profile_update_respects_fields_set() -> None:
    row = type("Row", (), {"email": "keep@x.com", "service": "old"})()
    apply_profile_update(row, _Body(service="  new  "), CLIENT_PROFILE_KEYS)
    assert row.service == "new"
    assert row.email == "keep@x.com"
    apply_profile_update(row, _Body(service=""), CLIENT_PROFILE_KEYS)
    assert row.service is None
    assert row.email == "keep@x.com"


async def test_prospect_create_and_patch_profile(client: AsyncClient, db: AsyncSession) -> None:
    admin = await create_user(
        db, email=f"crm-admin-{uuid.uuid4().hex[:8]}@example.com", is_superuser=True
    )
    await db.commit()
    headers = auth_header(admin)
    tag = uuid.uuid4().hex[:8]

    create = await client.post(
        "/v1/prospects",
        headers=headers,
        json={
            "company_name": f"Org {tag}",
            "pipeline_stage": "engaged",
            "contact_name": "Pat Contact",
            "contact_email": "Pat@Org.example",
            "contact_phone": "+1 555 0100",
            "org_email": "Hello@Org.example",
            "org_phone": "+1 555 0101",
            "working_schedule": "Mon–Fri 9–17",
            "message": "Need a demo",
            "service": "Implementation",
            "address": "1 Main St",
            "latitude": 9.9281,
            "longitude": -84.0907,
        },
    )
    assert create.status_code == 201, create.text
    data = create.json()
    assert data["company_name"] == f"Org {tag}"
    assert data["contact_name"] == "Pat Contact"
    assert data["contact_email"] == "pat@org.example"
    assert data["org_email"] == "hello@org.example"
    assert data["service"] == "Implementation"
    assert float(data["latitude"]) == pytest.approx(9.9281)
    prospect_id = data["id"]

    patch = await client.patch(
        f"/v1/prospects/{prospect_id}",
        headers=headers,
        json={"service": "Support", "message": "", "latitude": None},
    )
    assert patch.status_code == 200, patch.text
    updated = patch.json()
    assert updated["service"] == "Support"
    assert updated["message"] is None
    assert updated["latitude"] is None
    assert updated["contact_name"] == "Pat Contact"

    row = await db.get(Prospect, uuid.UUID(prospect_id))
    assert row is not None
    assert row.service == "Support"
    assert row.message is None
    assert row.org_phone == "+1 555 0101"


async def test_client_create_and_patch_profile(client: AsyncClient, db: AsyncSession) -> None:
    admin = await create_user(
        db, email=f"crm-client-{uuid.uuid4().hex[:8]}@example.com", is_superuser=True
    )
    await db.commit()
    headers = auth_header(admin)
    tag = uuid.uuid4().hex[:8]

    create = await client.post(
        "/v1/clients",
        headers=headers,
        json={
            "name": f"Client Org {tag}",
            "email": "Ops@Client.example",
            "phone": "+1 555 0200",
            "working_schedule": "24/7",
            "message": "Intake note",
            "service": "Managed",
            "address": "2 Oak Ave",
            "latitude": 40.7128,
            "longitude": -74.006,
        },
    )
    assert create.status_code == 201, create.text
    data = create.json()
    assert data["email"] == "ops@client.example"
    assert data["working_schedule"] == "24/7"
    assert float(data["longitude"]) == pytest.approx(-74.006)
    client_id = data["id"]

    patch = await client.patch(
        f"/v1/clients/{client_id}",
        headers=headers,
        json={"phone": "", "address": "3 Pine Rd"},
    )
    assert patch.status_code == 200, patch.text
    updated = patch.json()
    assert updated["phone"] is None
    assert updated["address"] == "3 Pine Rd"
    assert updated["email"] == "ops@client.example"


async def test_promote_copies_profile_and_primary_contact(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin = await create_user(
        db, email=f"crm-promote-{uuid.uuid4().hex[:8]}@example.com", is_superuser=True
    )
    await db.commit()
    headers = auth_header(admin)
    tag = uuid.uuid4().hex[:8]

    create = await client.post(
        "/v1/prospects",
        headers=headers,
        json={
            "company_name": f"Win Co {tag}",
            "pipeline_stage": "negotiating",
            "contact_name": "Lead Name",
            "contact_email": f"lead-{tag}@win.example",
            "contact_phone": "+1 555 0300",
            "org_email": f"hello-{tag}@win.example",
            "org_phone": "+1 555 0301",
            "working_schedule": "Weekdays",
            "message": "Signed",
            "service": "Retainer",
            "address": "9 Victory Ln",
            "latitude": 1.23,
            "longitude": 4.56,
        },
    )
    assert create.status_code == 201, create.text
    prospect_id = create.json()["id"]

    won = await client.patch(
        f"/v1/prospects/{prospect_id}/stage",
        headers=headers,
        json={"stage": "won"},
    )
    assert won.status_code == 200, won.text
    body = won.json()
    assert body.get("promoted_client") is not None
    client_out = body["promoted_client"]
    assert client_out["email"] == f"hello-{tag}@win.example"
    assert client_out["phone"] == "+1 555 0301"
    assert client_out["service"] == "Retainer"
    assert client_out["address"] == "9 Victory Ln"
    assert float(client_out["latitude"]) == pytest.approx(1.23)

    client_row = await db.get(Client, uuid.UUID(client_out["id"]))
    assert client_row is not None
    assert client_row.working_schedule == "Weekdays"
    assert client_row.message == "Signed"

    contacts = list(
        (
            await db.scalars(
                select(ClientContact).where(ClientContact.client_id == client_row.id)
            )
        ).all()
    )
    assert len(contacts) == 1
    assert contacts[0].is_primary is True
    assert contacts[0].name == "Lead Name"
    assert contacts[0].email == f"lead-{tag}@win.example"
    assert contacts[0].phone == "+1 555 0300"
