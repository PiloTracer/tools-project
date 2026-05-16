# Session handoff — tools-project

**Date:** 2026-05-15 (updated)

## Start here (new session)

1. Read **`.ai/context/CONTEXT.md`** — ports, auth modes, repo map.  
2. Read **`.ai/context/NEXT.md`** — **prioritized next batches** (schema SQL discipline → **`ProjectMember` / RBAC** → components → tasks → admin).  
3. Full product / MVP scope: **`.ai/plans/proposal/20260515-full-project.md`**.  
4. **Docker-only** tooling for Node/Python (see **`.cursorrules`**).  
5. **No Alembic** — DDL lives under **`sql/`** and applies on API startup (`app/schema_sql.py`).

---

## Snapshot

| Area | Status |
|------|--------|
| **Auth** | **Dual mode:** `AUTH_LOCAL_ENABLED` + `AUTH_OAUTH_ENABLED`. **`GET /v1/auth/config`** drives **`/login`**. |
| **Local** | bcrypt + JWT (`token_typ: local`), **`POST /v1/auth/local/login`**, **`/v1/admin/users`** (API CRUD; **web table only**, no forms yet). |
| **OAuth** | **`/sign-in`** → PKCE → **`/oauth/complete`** → **`prj_auth`** cookie. |
| **`/v1/auth/me`** | **`get_current_user`**: local JWT **or** (if OAuth on) **Bearer → `OAUTH_USER_INFO_ENDPOINT` → upsert `users` row** — not JWKS yet. |
| **Web** | **`AppShell`** (nav + user chip + sign out); **home** dashboard; **`/projects`**, **`/projects/new`**, **`/projects/[id]`**; **`POST /api/projects`** proxy; login redirects to **`/projects`**. |
| **Domain** | **`projects`** table + **`GET/POST /v1/projects`**, **`GET /v1/projects/{id}`** — scoped to **`owner_id`** (no **`ProjectMember`** yet). |
| **DB** | PostgreSQL; **`sql/schema_*.sql`** on startup (after bootstrap: backfill + inserts). **`bootstrap`** fills first superuser when DB empty + local auth + **`BOOTSTRAP_ADMIN_*`**. **`schema_inserts.sql`** adds a demo project for the oldest superuser. |
| **`./bin/start.sh`** | **10** drop public schema (**warning**); **11** `apply-ddl` (DDL → bootstrap → seeds). |

---

## Verified recently

- **`docker compose run web`**: `npm run check` + **`npm run build`** clean.  
- **`docker compose`**: API uses **`sqlparse`** (`api/pyproject.toml`) to split startup SQL scripts; **`./sql`** is mounted **`/sql`** for the **`api`** service.

---

## Recommended next work

**Detailed tasks and acceptance criteria:** **`.ai/context/NEXT.md`**.

Summary: **`sql/` parity with models + backfills** → **`ProjectMember` + RBAC** → **components** → **tasks (table UI)** → **admin user forms**; then Phase 2 (**activity**, **tickets**, **`/today`**).

Legacy note: older items “unified Bearer via JWKS” and “first `/v1/projects`” are **superseded** by current **userinfo upsert** + existing **projects** router; JWKS remains optional hardening.

---

## Where to read more

| Doc | Role |
|-----|------|
| **`.ai/context/NEXT.md`** | **Next batches** (agent/human checklist) |
| **`.ai/context/CONTEXT.md`** | Stable technical context |
| **`.cursorrules`** | **No Alembic**; **`sql/`** workflow |
| **`.ai/plans/proposal/preliminary.md`** | Short product brief |
| **`.ai/plans/proposal/20260515-full-project.md`** | Full MVP / north-star plan |
| **`sql/`** | Declarative schema + seeds |
| **`api/README.md`**, **`http://localhost:8300/docs`** | API |

---

## Agent notes

- **Do not commit** `.env` or `credentials/`.  
- **Scratch notes:** **`.ai/plans/proposal/notas`** — not authoritative unless the user says so.
