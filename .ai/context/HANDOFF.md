# Session handoff — tools-project

**Date:** 2026-05-15 (updated)

## Start here (new session)

1. Read **`.ai/context/CONTEXT.md`** — ports, auth modes, repo map.  
2. Read **`.ai/context/NEXT.md`** — batches **A–F** (schema discipline through activity / tickets / **`/today`**).  
3. Full product / MVP scope: **`.ai/plans/proposal/20260515-full-project.md`**.  
4. **Docker-only** tooling for Node/Python (see **`.cursorrules`**).  
5. **No Alembic** — DDL lives under **`sql/`** and applies on API startup (`app/schema_sql.py`).

---

## Snapshot

| Area | Status |
|------|--------|
| **Auth** | **Dual mode:** `AUTH_LOCAL_ENABLED` + `AUTH_OAUTH_ENABLED`. **`GET /v1/auth/config`** drives **`/login`**. |
| **Local** | bcrypt + JWT; **`POST /v1/auth/local/login`**; **`/v1/admin/users`** API + **`/admin/users`** forms (**local JWT only** — SSO documented below). |
| **OAuth** | **`/sign-in`** → PKCE → **`/oauth/complete`** → **`prj_auth`** cookie. |
| **`/v1/auth/me`** | **`get_current_user`**: local JWT **or** (OAuth on) **userinfo upsert** — route OpenAPI text describes path (**JWKS** optional future hardening). |
| **Web** | **`AppShell`** (**`/today`**); **`/projects/*`** (members, components, tasks, **activity**, **tickets**); **`/api/*`** BFF + **activity SSE** proxy. |
| **Domain** | **`projects`**, **`project_members`**, **`components`**, **`tasks`**, **`activities`**, **`mentions`**, **`tickets`** — RBAC; **`/v1/me/today`** & **`/v1/me/mentions`**. |
| **DB** | PostgreSQL; **`sql/schema_*.sql`** on startup (after bootstrap: backfill + inserts). **`bootstrap`** fills first superuser when DB empty + local auth + **`BOOTSTRAP_ADMIN_*`**. **`schema_inserts.sql`** adds a demo project for the oldest superuser. |
| **`./bin/start.sh`** | **10** drop public schema (**warning**); **11** `apply-ddl` (DDL → bootstrap → seeds). |

---

## Verified recently

- **`docker compose run web`**: `npm run check` + **`npm run build`** clean.  
- **`docker compose`**: API uses **`sqlparse`** (`api/pyproject.toml`) to split startup SQL scripts; **`./sql`** is mounted **`/sql`** for the **`api`** service.

---

## Recommended next work

**Detailed tasks and acceptance criteria:** **`.ai/context/NEXT.md`**.

Summary: **NEXT batches A–F shipped** (Batch **A** = ongoing SQL discipline). Optional next: Kanban, human task refs, richer SSE payloads, notification delivery.

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
