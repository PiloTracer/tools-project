"""Shared test fixtures."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure test database is used before any app imports that read settings.
TEST_DATABASE_URL = "postgresql+asyncpg://prj:prj_dev_change_me@postgresql:5432/tools_project_test"
os.environ["DATABASE_URL"] = "postgresql://prj:prj_dev_change_me@postgresql:5432/tools_project_test"
os.environ["SQL_SCHEMA_DIR"] = "/sql"
os.environ["SQL_SCHEMA_APPLY"] = "true"
os.environ["JWT_SECRET"] = "test-jwt-secret-do-not-use-in-production"
os.environ["GITHUB_SYNC_ENABLED"] = "false"
os.environ["AUTH_OAUTH_ENABLED"] = "false"
os.environ["AUTH_LOCAL_ENABLED"] = "true"
os.environ["BOOTSTRAP_ADMIN_EMAIL"] = "admin@example.com"
os.environ["BOOTSTRAP_ADMIN_PASSWORD"] = "admin-test-password"
os.environ["RFP_WEBHOOK_SECRET"] = "test-rfp-secret"

from app.bootstrap import run_bootstrap  # noqa: E402
from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.schema_sql import run_post_bootstrap, run_pre_bootstrap  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    """Provide a single event loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


async def _create_test_database() -> None:
    sys_dsn = "postgresql://prj:prj_dev_change_me@postgresql:5432/postgres"
    conn = await asyncpg.connect(dsn=sys_dsn)
    try:
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'tools_project_test'"
        )
        if result is None:
            await conn.execute("CREATE DATABASE tools_project_test")
    finally:
        await conn.close()


async def _apply_schema_and_bootstrap() -> None:
    engine = create_async_engine(TEST_DATABASE_URL)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with engine.begin() as conn:
        await conn.exec_driver_sql("DROP SCHEMA IF EXISTS public CASCADE")
        await conn.exec_driver_sql("CREATE SCHEMA public")
        await conn.exec_driver_sql("GRANT ALL ON SCHEMA public TO CURRENT_USER")
    async with engine.begin() as conn:
        await run_pre_bootstrap(conn)
    async with factory() as session:
        await run_bootstrap(session)
        await session.commit()
    async with engine.begin() as conn:
        await run_post_bootstrap(conn)
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _test_database() -> None:
    await _create_test_database()
    await _apply_schema_and_bootstrap()
    yield


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh async session for the test and override app dependencies."""
    engine = create_async_engine(TEST_DATABASE_URL)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    # Point app globals at this test's engine so factories and app lifespan share it.
    import app.db as db_module

    db_module._engine = engine
    db_module._session_factory = factory

    session = factory()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_db] = _override_get_db

    try:
        yield session
    finally:
        await session.rollback()
        await session.close()
        await engine.dispose()
        app.dependency_overrides.clear()
        db_module._engine = None
        db_module._session_factory = None


@pytest_asyncio.fixture
async def client(_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client against the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
