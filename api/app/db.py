"""Async SQLAlchemy engine and sessions."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.schema_sql import run_pre_bootstrap

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine():
    global _engine, _session_factory
    if _engine is None:
        url = get_settings().database_url
        if url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url.removeprefix("postgresql://")
        _engine = create_async_engine(url, echo=False)
        _session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _engine


def session_factory() -> async_sessionmaker[AsyncSession]:
    get_engine()
    if _session_factory is None:
        raise RuntimeError("session_factory called before get_engine() completed initialization")
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    fac = session_factory()
    async with fac() as session:
        yield session


async def init_db() -> None:
    import app.models  # noqa: F401 — register ORM models  # pyright: ignore[reportUnusedImport]

    engine = get_engine()
    async with engine.begin() as conn:
        await run_pre_bootstrap(conn)
