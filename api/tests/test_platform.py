"""Tests for the platform identity endpoint."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.factories import create_client, create_client_contact, create_user


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_whoami_with_bearer_returns_user_and_companies(client: AsyncClient, db) -> None:
    user = await create_user(db, email="whoami@example.com")
    client_obj = await create_client(db, name="Whoami Client", slug="whoami-client", created_by=user.id)
    await create_client_contact(
        db,
        client_id=client_obj.id,
        user_id=user.id,
        email=user.email,
        name=user.display_name,
        role="contact_admin",
    )
    await db.commit()

    from tests.factories import auth_header

    response = await client.get("/v1/platform/whoami", headers=auth_header(user))
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == str(user.id)
    assert data["user"]["email"] == user.email
    assert len(data["companies"]) == 1
    assert data["companies"][0]["client_id"] == str(client_obj.id)
    assert data["companies"][0]["role"] == "contact_admin"


async def test_whoami_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.get("/v1/platform/whoami")
    assert response.status_code == 401


async def test_whoami_without_companies_returns_empty_list(client: AsyncClient, db) -> None:
    user = await create_user(db, email="nocontact@example.com")
    await db.commit()

    from tests.factories import auth_header

    response = await client.get("/v1/platform/whoami", headers=auth_header(user))
    assert response.status_code == 200
    data = response.json()
    assert data["companies"] == []
