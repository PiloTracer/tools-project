# Session handoff — tools-project

**Date:** 2026-05-15 (updated)

## Start here (new session)

1. Read **`.ai/context/CONTEXT.md`** — ports, auth modes, repo map.  
2. Read **`.ai/context/NEXT.md`** — **carryover priorities** (**P1 & P3 closed 2026-05-15**, **P2 / P4 / P5 open**) then **Batch G** (Phase 1 parity: Kanban, task detail, ⌘K, health) and **Batch H** (inbox, watchers, activity depth). Batches **B–F** are complete; **A** = ongoing SQL discipline.  
3. Full product / MVP scope: **`.ai/plans/proposal/20260515-full-project.md`** (incl. **§16** repo alignment — `Activity.is_internal` row is now **done**).  
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
| **Web** | **`AppShell`** (**`/today`**); **`/projects/*`** (members, components, **tasks** table, **activity**, **tickets** queue + **ticket case** `.../tickets/[ticketId]`); **`/api/*`** BFF + **activity SSE** proxy; **`/api/attachments/[id]`** for authenticated image fetch. |
| **Domain** | **`projects`**, **`project_members`**, **`components`**, **`tasks`** (with **`ref`**), **`activities`**, **`mentions`**, **`tickets`**, **`attachments`** (ticket images, **`meta_json.attachment_ids`** on activity) — RBAC; **`/v1/me/today`** & **`/v1/me/mentions`**. |
| **DB** | PostgreSQL; **`sql/schema_*.sql`** on startup (after bootstrap: backfill + inserts). **`bootstrap`** fills first superuser when DB empty + local auth + **`BOOTSTRAP_ADMIN_*`**. **`schema_inserts.sql`** adds a demo project for the oldest superuser. |
| **Storage** | **`ATTACHMENTS_DIR`** (default `/data/attachments`); Compose named volume **`tpr_attachments`** on **`api`**. |
| **`./bin/start.sh`** | **10** drop public schema (**warning**); **11** `apply-ddl` (DDL → bootstrap → seeds). |

---

## Verified recently

- **2026-05-15:** `docker compose run --rm --no-deps web sh -lc "npm run check && npm run build"` → clean (16/16 static, all 38 routes).  
- **2026-05-15:** `docker compose run --rm --no-deps api python -m compileall -q app` clean; smoke-imported `Activity` + `ActivityCreate` + `ActivityOut` to confirm `is_internal` is present on all three.  
- **API image**: `python-multipart` for uploads; uses **`sqlparse`** (`api/pyproject.toml`) to split startup SQL scripts; **`./sql`** is mounted **`/sql`** for the **`api`** service.

---

## Recommended next work

**Checklist and acceptance-style tasks:** **`.ai/context/NEXT.md`**.

**Order of attack:** (1) **P2** (threaded reply UI — DB column `parent_activity_id` already in place) → **P4** (task attachments, mirroring ticket pattern) → **P5** (non-image uploads + retention hook). (2) **Batch G** — Kanban + task detail + ⌘K + health badges toward Phase 1 “done”. (3) **Batch H** — inbox + watchers + richer activity/SSE.

Legacy note: older items “unified Bearer via JWKS” and “first `/v1/projects`” are **superseded** by current **userinfo upsert** + **projects** router; JWKS remains optional hardening.

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
