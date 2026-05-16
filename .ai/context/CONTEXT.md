# tools-project — context

**Last updated:** 2026-05-15

## Purpose

**Project management hub** aligned with the org toolchain: **projects**, **components**, **tasks**, **TODOs**, **support tickets**, low-friction activity (text, images, threading), and **GitHub** linkage (e.g. commits per project/component).

**Authentication is deployment-configurable:**

| Mode | Typical flags | UX |
|------|----------------|-----|
| **Standalone** | `AUTH_LOCAL_ENABLED=true`, `AUTH_OAUTH_ENABLED=false` | Email/password → **local JWT**; superusers manage users via **`/v1/admin/users`**. |
| **Integrated** | `AUTH_LOCAL_ENABLED=false`, `AUTH_OAUTH_ENABLED=true` | **tools-dashboard** OAuth 2.0 + PKCE (same family as **`/mnt/work/Projects/tools-rizervox`**). |
| **Hybrid** | both `true` | **`/login`** offers SSO and/or local sign-in per **`GET /v1/auth/config`**. |

Product / UX source of truth: **`.ai/plans/proposal/preliminary.md`**.  
**Prioritized implementation backlog:** **`.ai/context/NEXT.md`**. Full MVP spec: **`.ai/plans/proposal/20260515-full-project.md`**.  
Rolling session snapshot: **`.ai/context/HANDOFF.md`**.

## Tech stack

| Layer | Path | Notes |
|--------|------|--------|
| **Web** | `web/` | Next.js 16 App Router, TypeScript |
| **API** | `api/` | FastAPI, Uvicorn, SQLAlchemy 2 **async**, `asyncpg` |
| **DB** | Compose **`postgresql`** | PostgreSQL 16 |
| **Schema** | `sql/` | Declarative **`schema_*.sql`** on API startup (mounted **`/sql`** in Compose); **no Alembic** |
| **Identity** | Env-driven | **`JWT_SECRET`** (local); **`OAUTH_*`** when SSO on — see **`.env.example`** |

## Related repositories

| Path | Role |
|------|------|
| `/mnt/data/Projects/EPIC/tools-dashboard` | OAuth **IdP** (when SSO enabled) |
| `/mnt/work/Projects/tools-rizervox` | Reference: OAuth env, PKCE, `extra_hosts` / `host-gateway` |

Integrated/hybrid: **consume** dashboard OAuth — do not replace the IdP. Standalone: **local auth** is authoritative for this app.

## Local URLs (`docker compose --profile dev up --build`)

| Surface | Default URL |
|---------|-------------|
| **Web** | http://localhost:**18513** (`WEB_DEV_HOST_PORT`) |
| **API** | http://localhost:**8300** — `/healthz`, `/docs`, `/v1/auth/config` |
| **Postgres** | host **55433** → container `5432` (`POSTGRES_HOST_PORT`) |

Compose does **not** require a root `.env` file; defaults are in **`docker-compose.yml`**. Use **`.env`** for secrets and non-default auth (never commit).

## Repository map

### Web (`web/`)

| Path | Role |
|------|------|
| `src/app/login` | Login UI (SSO link + **`LocalLoginForm`** when enabled) |
| `src/app/sign-in/route.ts` | OAuth kickoff; no-op redirect if `AUTH_OAUTH_ENABLED=false` |
| `src/app/oauth/complete/route.ts` | OAuth callback → **`prj_auth`** / **`prj_refresh`** cookies |
| `src/app/api/auth/local/login` | Proxy → API local login; sets **`SESSION_COOKIE_NAME`** (default `prj_auth`) |
| `src/app/api/auth/logout` | Clears session cookies |
| `src/app/projects` | Projects list + **`[id]`** hub (settings, **members**, **components**, **tasks**, **activity**, **tickets**) |
| `src/app/today` | **`/today`** — assigned tasks due window + @mentions |
| `src/app/admin/users` | Local superuser user admin (forms + **`/api/admin/users`**) |
| `src/shared/server/oauth-*.ts` | OAuth config, PKCE **signed `state`** (no Redis) |
| `src/shared/server/auth-flags.ts` | `AUTH_OAUTH_ENABLED` / `AUTH_LOCAL_ENABLED` for SSR |

### API (`api/`)

| Path | Role |
|------|------|
| `app/main.py` | FastAPI app, lifespan: **`sql/` DDL** → **`run_bootstrap`** → **`sql/` backfill & inserts** |
| `app/db.py` | Async engine, sessions; **`init_db`** runs **`schema_changes` + indexes** from **`sql/`** |
| `app/schema_sql.py` | **`schema_*.sql`** runner; **`python -m app.cli_schema`** (e.g. `apply-ddl`) |
| `app/config.py` | **`Settings`** (`AUTH_*`, `JWT_*`, `BOOTSTRAP_ADMIN_*`, `DATABASE_URL`, **`SQL_SCHEMA_*`**) |
| `app/models/user.py` | **`users`** table |
| `app/bootstrap.py` | First superuser if DB empty + **`BOOTSTRAP_ADMIN_*`** set |
| `app/routers/auth.py` | **`/v1/auth/config`**, **`/local/login`**, **`/me`** |
| `app/routers/admin_users.py` | **`GET/POST/PATCH /v1/admin/users`** (superuser) |
| `app/deps.py` | **`get_current_user_local`**, **`require_superuser`** (local JWT only) |
| `app/services/auth_local.py` | bcrypt, JWT encode/decode (`token_typ: local`) |

**`sql/`** (repo root, mounted **`/sql`** in Compose **`api`**): **`schema_changes.sql`** + **`schema_indexes.sql`** each startup (**before bootstrap**); **`schema_backfill.sql`** + **`schema_inserts.sql`** after bootstrap. Idempotent DDL/DML only — **no Alembic** (see **`.cursorrules`**).

Root **`docker-compose.yml`**: services **`postgresql`**, **`api`**, **`web`** (all `profiles: [dev]`).

## Auth env (quick reference)

| Variable | Role |
|----------|------|
| `AUTH_LOCAL_ENABLED` | Local email/password + JWT + admin user API |
| `AUTH_OAUTH_ENABLED` | Enable Next SSO routes + IdP round-trip |
| `JWT_SECRET` | HMAC signing for **local** access tokens |
| `BOOTSTRAP_ADMIN_EMAIL` / `PASSWORD` | Optional; only when DB has **zero** users. **`EmailStr`** needs a valid domain (e.g. `admin@example.com`, not `admin@localhost`). |
| `OAUTH_*`, `PUBLIC_ORIGIN`, `SESSION_COOKIE_NAME`, `REFRESH_COOKIE_NAME` | SSO + cookies |
| `SQL_SCHEMA_DIR` | Where `schema_*.sql` live (Compose default **`/sql`**) |
| `SQL_SCHEMA_APPLY` | When false, skips SQL runner (advanced; tables must exist) |

**`GET /v1/auth/config`** returns `{ local_enabled, oauth_enabled }` for the web UI.

## OAuth (when enabled)

1. Register client in **tools-dashboard**; align **`OAUTH_REDIRECT_URI`** with **`PUBLIC_ORIGIN`** (e.g. `{PUBLIC_ORIGIN}/oauth/complete`).
2. PKCE **`state`** is **signed** (embedded verifier); no Redis in this repo.
3. Containers: **`extra_hosts`** for **`dev.aiepic.app:host-gateway`** (and **`host.docker.internal`**) so server-side token exchange reaches the host IdP.

## Docker (mandatory for Node and Python)

```bash
docker compose --profile dev up --build
docker compose run --rm --no-deps web sh -lc "npm ci --no-audit --no-fund && npm run check && npm run build"
```

## Domain model (north star — persistence is partial)

- Persisted: **`users`**, **`projects`**, **`project_members`**, **`components`**, **`tasks`**, **`activities`**, **`mentions`**, **`tickets`**, **`attachments`** (ticket and/or **task** / project-scoped rows), **`inbox_items`**, **`watchers`**. Schema in **`sql/schema_*.sql`** aligned with **`api/app/models`**.
- Web UX: Kanban + task detail, command palette (**⌘K**), project health pills, **Inbox**, **watch** actions — see **`NEXT.md`** implementation status.
- Optional polish: GitHub linkage, richer notifications, markdown editor wiring — see **`NEXT.md`** follow-ups.

## Security

- No secrets in git; use **`.env`** / platform secrets in deployment.
- **Production:** strong **`JWT_SECRET`**, rotate bootstrap passwords, tighten CORS and cookie **`secure`** flags behind HTTPS.
- **`/v1/admin/users`** expects a **local** superuser JWT (`get_current_user_local`). **`/v1/auth/me`** and **project** routes use **`get_current_user`**: local JWT **or** OAuth access token resolved via **`OAUTH_USER_INFO_ENDPOINT`** (upserts **`users`**). JWKS-based validation is optional future hardening.
