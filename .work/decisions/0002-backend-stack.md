# ADR-0002: Backend stack

**Status:** Decided
**Date:** 2026-06-18
**Source:** Brownfield reverse-engineering of existing code

## Context

tools-project needs a backend runtime that supports async I/O, real-time collaboration via SSE, and a declarative schema workflow (no Alembic). The stack was chosen before this ADR was written — this document formalizes the existing decision.

## Decision

- **Runtime:** Python 3.11 (`api/Dockerfile.dev:1` — `python:3.11-slim-bookworm`)
- **Web framework:** FastAPI ≥0.115 (`api/pyproject.toml`) with async routes
- **ASGI server:** Uvicorn 0.32+ with `--reload` in dev (`api/Dockerfile.dev:14`)
- **ORM:** SQLAlchemy 2.0+ async (`sqlalchemy[asyncio]`) with asyncpg ≥0.29
- **Database:** PostgreSQL 16 (`docker-compose.yml:23` — `postgres:16-alpine`)
- **Schema management:** Declarative SQL files in `sql/` (`schema_changes.sql` → `schema_indexes.sql` → `schema_backfill.sql` → `schema_inserts.sql`) — no Alembic. DDL runs on API startup via `app/schema_sql.py`.
- **Auth (local):** bcrypt directly (`api/app/services/auth_local.py`), JWT via `python-jose[cryptography]`
- **Auth (OAuth):** Tools-dashboard OAuth 2.0 + PKCE with `state` embedded in signed cookie (no Redis)
- **File attachments:** Local filesystem at `ATTACHMENTS_DIR`, 25 MiB per-file cap, per-project count/byte quotas

## Consequences

- Async throughout requires async SQLAlchemy sessions, async HTTP clients (httpx) for GitHub integration.
- Declarative SQL means all model changes must produce idempotent DDL statements.
- Python 3.11 vs 3.12/3.13 means no 3.12+ specific syntax — acceptable for stability in a brownfield project.
- PostgreSQL 16 provides `pg_isready` health checks and features compatible with the SQLAlchemy async driver.

## Alternatives rejected

- **Alembic / explicit migrations:** Rejected for simplicity — the project prefers idempotent SQL scripts that always match the current model.
- **Django:** Rejected — FastAPI's async-native design better suits SSE and GitHub polling.
- **Node.js backend:** Rejected — Python ecosystem preferred for SQLAlchemy strengths and team familiarity.
