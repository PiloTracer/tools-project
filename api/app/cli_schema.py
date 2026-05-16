"""CLI helpers for applying SQL schema files outside full API lifespan."""

from __future__ import annotations

import asyncio
import sys

from app.schema_sql import cli_apply_phase


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv == ["apply-ddl"]:
        asyncio.run(cli_apply_phase())
        return 0
    if argv == ["apply-all"]:
        asyncio.run(cli_apply_phase())
        return 0
    sys.stderr.write(
        "usage: python -m app.cli_schema apply-ddl | apply-all\n"
        "  apply-ddl | apply-all — schema_changes → schema_indexes → run_bootstrap →\n"
        "    schema_backfill → schema_inserts (same phases as API startup).\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
