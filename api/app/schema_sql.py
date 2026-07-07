"""Run versioned SQL scripts from the repo `sql/` directory (no ORM migrations)."""

from __future__ import annotations

import logging
from pathlib import Path

import sqlparse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

# Single execution order for every `schema_*.sql` file (DDL → indexes → backfill → seeds).
# Pre-bootstrap phases run from init_db(); post-bootstrap run after run_bootstrap() in lifespan.
SCHEMA_SQL_FILE_ORDER = (
    "schema_changes.sql",
    "schema_indexes.sql",
    "schema_backfill.sql",
    "schema_inserts.sql",
)
PRE_BOOTSTRAP_FILES = SCHEMA_SQL_FILE_ORDER[:2]
POST_BOOTSTRAP_FILES = SCHEMA_SQL_FILE_ORDER[2:]


def default_sql_schema_dir() -> Path:
    """Host layout: api/app/config.py → parents[2] is repo root."""
    return Path(__file__).resolve().parents[2] / "sql"


def schema_sql_inventory(sql_dir: Path) -> tuple[frozenset[str], frozenset[str]]:
    """Declared filenames vs `schema_*.sql` present on disk."""
    declared = frozenset(SCHEMA_SQL_FILE_ORDER)
    on_disk = frozenset(p.name for p in sql_dir.glob("schema_*.sql"))
    return declared, on_disk


def assert_complete_schema_sql_inventory(sql_dir: Path) -> None:
    """Fail if `sql/` is missing a listed file or contains an unlisted `schema_*.sql`."""
    declared, on_disk = schema_sql_inventory(sql_dir)
    if declared == on_disk:
        return
    parts: list[str] = []
    missing = sorted(declared - on_disk)
    extra = sorted(on_disk - declared)
    if missing:
        parts.append(f"missing: {missing}")
    if extra:
        parts.append(f"unlisted schema_*.sql (extend SCHEMA_SQL_FILE_ORDER): {extra}")
    raise FileNotFoundError("sql/ schema inventory mismatch — " + "; ".join(parts))


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


async def cli_apply_phase() -> None:
    """Apply schema SQL like API startup: pre-bootstrap DDL → ``run_bootstrap`` → post-bootstrap SQL."""
    import app.models  # noqa: F401 — register ORM models before bootstrap  # pyright: ignore[reportUnusedImport]

    settings = get_settings()
    sql_dir = resolve_sql_schema_dir(settings)
    if sql_dir is None:
        raise FileNotFoundError(
            "SQL schema directory not found — mount ./sql and set SQL_SCHEMA_DIR=/sql in Docker,"
            " or run from repo with sql/ beside api/"
        )
    assert_complete_schema_sql_inventory(sql_dir)
    from app.bootstrap import run_bootstrap
    from app.db import get_engine, session_factory

    engine = get_engine()

    async with engine.begin() as conn:
        await run_schema_files(conn, filenames=PRE_BOOTSTRAP_FILES, sql_dir=sql_dir)

    fac = session_factory()
    async with fac() as session:
        await run_bootstrap(session)

    async with engine.begin() as conn:
        await run_schema_files(conn, filenames=POST_BOOTSTRAP_FILES, sql_dir=sql_dir)
