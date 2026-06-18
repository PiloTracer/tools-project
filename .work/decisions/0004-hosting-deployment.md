# ADR-0004: Hosting and deployment

**Status:** Decided
**Date:** 2026-06-18
**Source:** Brownfield reverse-engineering of existing code

## Context

tools-project is a development-phase internal tool. The hosting model must support local development and a clear path to production deployment. The current setup was chosen before this ADR was written — this document formalizes the existing decision.

## Decision

- **Local development:** Docker Compose (`docker-compose.yml`) with three services: `postgresql`, `api`, `web` — all under `profiles: [dev]`.
- **API server:** Uvicorn with `--reload` for hot-reload in dev; production would use Uvicorn workers or Gunicorn.
- **Web server:** Next.js `npm run dev` in dev; `npm run build && npm start` for production.
- **Database:** PostgreSQL 16 container with named volume (`tpr_pg_data`) for persistence across restarts.
- **Port convention:** API `8300`, Web `18513` (dev), PostgreSQL `55433:5432` — all configurable via `.env`.
- **Auth:** Dual-mode — local JWT (`AUTH_LOCAL_ENABLED`) and/or OAuth 2.0 via tools-dashboard (`AUTH_OAUTH_ENABLED`). Controlled by env vars.
- **Schema management:** SQL files (`sql/schema_*.sql`) executed on API startup — no dedicated migration container.
- **Attachments:** Local filesystem bind-mounted volume — not suitable for multi-replica production without object storage.
- **GitHub integration:** PAT with Fernet-at-rest encryption (`GITHUB_TOKEN_ENCRYPTION_KEY` or derived from `JWT_SECRET`).

## Consequences

- Docker Compose is the only supported dev environment — contributors must have Docker.
- OAuth mode requires `extra_hosts` to reach the host IdP (`dev.aiepic.app:host-gateway`).
- The local filesystem attachment store is an explicit V1 limitation — V2 should migrate to S3-compatible object storage.
- Declarative SQL startup means schema changes are applied on every start — safe because all DDL is `IF NOT EXISTS`.
- Multi-profile Compose (`dev` vs `prod`) can be introduced without breaking existing workflows.

## Alternatives rejected

- **Bare metal / venv + nvm:** Rejected for reproducibility — Docker Compose ensures consistent environment.
- **Alembic / Flyway:** Rejected — the project prefers idempotent SQL files run at startup (no migration state to manage).
- **Kubernetes / Nomad:** Not applicable at this stage — overkill for a dev-phase internal tool.
- **Cloud-hosted DB (RDS, Cloud SQL):** Production path, not needed in dev. PostgreSQL 16 local is sufficient.
