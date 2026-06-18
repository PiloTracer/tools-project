# Coding conventions — tools-project

**Brownfield synthesis 2026-06-18:** Inferred from existing code patterns. Update as the team standardizes.

## Python (API)

- **Framework:** FastAPI with async endpoints
- **ORM:** SQLAlchemy 2 async (Mapped-column style, not legacy `declarative_base()`)
- **DB driver:** asyncpg
- **Models:** One file per entity under `api/app/models/`
- **Routers:** One file per bounded context under `api/app/routers/`, tagged in OpenAPI
- **Services:** Business logic in `api/app/services/`, not in routers
- **Schema files:** Idempotent DDL under `sql/schema_*.sql` — no Alembic
- **Config:** Pydantic `BaseSettings` in `api/app/config.py`
- **Dependencies:** FastAPI `Depends()` for auth and project access
- **Testing:** pytest preferred (no test suite committed yet — placeholder)
- **Format/lint:** ruff for Python; ESLint for TypeScript (no project-wide lint config committed yet — placeholder)

## TypeScript/React (Web)

- **Framework:** Next.js 16 App Router with React 19
- **Pages:** `web/src/app/<route>/page.tsx` (SSR or client)
- **Client components:** Keep interactivity in `*Client.tsx` files
- **API routes:** BFF proxy pattern under `web/src/app/api/`
- **Shared types:** `web/src/shared/types/` (mirrored from API schemas)
- **Components:** Reusable UI in `web/src/components/`
- **State:** Server components by default; client components only where interactivity required
- **Styling:** Global CSS in `web/src/app/globals.css`; component-scoped styles as needed (no CSS-modules/Tailwind config committed yet)

## Git conventions

- **Commits:** `type: short description` — types: `feat`, `fix`, `refactor`, `docs`, `chore`, `style`, `test`
- **Branch:** `main` is the primary branch
- **No force-push** without explicit user request
- **No secrets** in commits (`.env`, `credentials/`, `*.pem`, tokens)
