"""Run versioned SQL scripts from the repo `sql/` directory (no ORM migrations)."""

from __future__ import annotations

import logging
from pathlib import Path

import sqlparse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

PRE_BOOTSTRAP_FILES = (
    "schema_changes.sql",
    "schema_indexes.sql",
)
POST_BOOTSTRAP_FILES = (
    "schema_backfill.sql",
    "schema_inserts.sql",
)


def default_sql_schema_dir() -> Path:
    """Host layout: api/app/config.py → parents[2] is repo root."""
    return Path(__file__).resolve().parents[2] / "sql"


def resolve_sql_schema_dir(settings: Settings) -> Path | None:
    raw = (settings.sql_schema_dir or "").strip()
    if raw:
        p = Path(raw)
    else:
        p = default_sql_schema_dir()
        if not p.is_dir():
            p = Path("/sql")
    return p if p.is_dir() else None


def split_sql_statements(script: str) -> list[str]:
    parts = sqlparse.split(script)
    out: list[str] = []
    for p in parts:
        s = (p or "").strip()
        if not s:
            continue
        out.append(s)
    return out


async def run_sql_file(connection: AsyncConnection, path: Path) -> None:
    if not path.is_file():
        logger.warning("SQL file missing, skipping: %s", path)
        return
    script = path.read_text(encoding="utf-8")
    statements = split_sql_statements(script)
    if not statements:
        logger.warning("SQL file empty or unparsed, skipping: %s", path)
        return
    logger.info("Executing SQL file (%d statements): %s", len(statements), path)
    for stmt in statements:
        await connection.execute(text(stmt))


async def run_schema_files(
    connection: AsyncConnection,
    *,
    filenames: tuple[str, ...],
    sql_dir: Path,
) -> None:
    for name in filenames:
        await run_sql_file(connection, sql_dir / name)


async def run_pre_bootstrap(connection: AsyncConnection) -> None:
    settings = get_settings()
    if not settings.sql_schema_apply:
        logger.info("sql_schema_apply is false — skipping DDL SQL.")
        return
    sql_dir = resolve_sql_schema_dir(settings)
    if sql_dir is None:
        logger.error(
            "SQL schema directory not found (set SQL_SCHEMA_DIR or mount ./sql)."
        )
        raise FileNotFoundError("sql schema directory missing")
    await run_schema_files(connection, filenames=PRE_BOOTSTRAP_FILES, sql_dir=sql_dir)


async def run_post_bootstrap(connection: AsyncConnection) -> None:
    settings = get_settings()
    if not settings.sql_schema_apply:
        return
    sql_dir = resolve_sql_schema_dir(settings)
    if sql_dir is None:
        raise FileNotFoundError("sql schema directory missing")
    await run_schema_files(
        connection,
        filenames=POST_BOOTSTRAP_FILES,
        sql_dir=sql_dir,
    )


async def cli_apply_phase(*, ddl_only: bool) -> None:
    """Called from python -m app.cli_schema."""
    settings = get_settings()
    sql_dir = resolve_sql_schema_dir(settings)
    if sql_dir is None:
        raise FileNotFoundError(
            "sql schema directory not found — mount ./sql and set SQL_SCHEMA_DIR=/sql in Docker,"
            " or run from repo with sql/ beside api/"
        )
    from app.db import get_engine

    engine = get_engine()
    async with engine.begin() as conn:
        names = PRE_BOOTSTRAP_FILES if ddl_only else PRE_BOOTSTRAP_FILES + POST_BOOTSTRAP_FILES
        await run_schema_files(conn, filenames=names, sql_dir=sql_dir)
