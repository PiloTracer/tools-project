# Session handoff — tools-project

**Date:** 2026-05-15

## Snapshot

| Area | Status |
|------|--------|
| **Auth** | **Dual mode:** `AUTH_LOCAL_ENABLED` + `AUTH_OAUTH_ENABLED` (defaults **both true** in compose for dev). **`GET /v1/auth/config`** drives **`/login`**. |
| **Local** | bcrypt (`bcrypt`), JWT (`python-jose`, `token_typ: local`), **`POST /v1/auth/local/login`**, **`GET /v1/auth/me`**, **`/v1/admin/users`** (list/create/patch, superuser). |
| **OAuth** | **`/sign-in`** → PKCE → **`/oauth/complete`** → cookies; disabled when **`AUTH_OAUTH_ENABLED=false`**. |
| **Web** | **`/api/auth/local/login`**, **`/api/auth/logout`**; **`/admin/users`** (read-only table, local superuser session). |
| **DB** | PostgreSQL + **`users`** via SQLAlchemy **`create_all`** on API startup — **no Alembic yet**. |
| **Bootstrap** | Optional **`BOOTSTRAP_ADMIN_*`** if DB is empty; dev default email **`admin@example.com`** (not `admin@localhost` — **`EmailStr`**). |

## Verified recently

- **`docker compose --profile dev up --build`**: API **`/healthz`**, **`/v1/auth/config`**, local login with bootstrap user, **`next build`** + eslint clean (see session logs).

## Recommended next work (priority)

1. **Unified Bearer auth on the API** — Accept **dashboard** OAuth JWTs (JWKS / introspection) on the same routes as **local** JWTs so hybrid users and SSO-only tokens work consistently.
2. **Alembic** — Replace **`create_all`** for production; version **`users`** and future PMS tables.
3. **Admin UX** — Forms on **`/admin/users`** for create/update user (today: OpenAPI + table + **`PATCH`**).
4. **Domain** — First real **`/v1/projects`** (or equivalent) with auth dependency and DB models.

## Where to read more

- **Stable layout & env:** **`.ai/context/CONTEXT.md`** (this file is the rolling “what’s next”).
- **Product:** **`.ai/plans/proposal/preliminary.md`**
- **Rough delivery phases:** **`.ai/plans/estimate/plan.md`**
- **API surface:** **`api/README.md`**, **`http://localhost:8300/docs`** (when stack is up)

## Agent notes

- **Docker-first:** all npm/Python via Compose (see **`.cursorrules`**).
- **Scratch / informal notes:** **`.ai/plans/proposal/notas`** — not authoritative unless the user says so.
