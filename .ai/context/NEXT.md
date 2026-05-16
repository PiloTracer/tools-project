# Next batch — tools-project (prioritized work)

**Purpose:** Concrete backlog after **projects foundation** (owner-scoped CRUD, web shell, SSO → `users` via userinfo).  
**North star:** `.ai/plans/proposal/20260515-full-project.md` (Phase 1 → 2).  
**Run dev stack:** `.cursorrules` / `docker compose --profile dev up --build` or `./bin/start.sh`.

**Schema**: **declarative `sql/` only** — no Alembic (see `.cursorrules`). On API startup: `schema_changes.sql` → `schema_indexes.sql` → **bootstrap** → `schema_backfill.sql` → `schema_inserts.sql`.

**Latest:** Batches **A–F** are implemented in-repo (A remains ongoing discipline when models change). Phase 2 can extend activity parsing, Kanban, human task refs, etc.

---

## Batch A — Schema discipline (maintain continually)

Ongoing process: whenever **`api/app/models`** gain persisted fields, update **`sql/schema_*.sql`** in the same change. **Current tree:** `users`, `projects` (+ `status`, `project_key`), `project_members`, `components`, `tasks`, **`activities`**, **`mentions`**, **`tickets`** — see **`sql/schema_changes.sql`** and indexes.

| # | Item | Why | Hints |
|---|------|-----|--------|
| A1 | Keep **`sql/schema_changes.sql`** in sync when **`api/app/models`** change | Primary DDL source; **`create_all`** is not used | Use `CREATE TABLE IF NOT EXISTS` / `ALTER TABLE … ADD COLUMN IF NOT EXISTS`; document new columns inline. |
| A2 | Keep **`sql/schema_indexes.sql`** in sync when adding indexes or constraints | Separation from table DDL | Prefer `CREATE … IF NOT EXISTS` / idempotent guards. |
| A3 | **Backfill stays current** — extend **`sql/schema_backfill.sql`** whenever a DDL change implies row fixes | One-time data migrations for existing deploys | Idempotent statements only (`WHERE` guards, `WHERE NOT EXISTS`, etc.). |
| A4 | **Seeds/config** — optional rows in **`sql/schema_inserts.sql`** (`ON CONFLICT` / subqueries); demo project targets oldest superuser | Dev UX | After bootstrap — avoid hard-coded UUIDs unless truly static fixtures. |

**Done when:** A change to persisted fields always touches the matching SQL files **in the same PR**; `./bin/start.sh` options **10/11** and `python -m app.cli_schema apply-ddl` behave as documented in `.cursorrules`.

---

## Batch B — Projects: membership & RBAC (plan §4 / §6)

| # | Item | Why | Hints |
|---|------|-----|--------|
| B1 | **`ProjectMember`** model (`project_id`, `user_id`, `role`: owner / maintainer / contributor / viewer) | Plan assumes RBAC | **Done:** `sql/` + `api/app/models/project_member.py`; backfill inserts owner rows for legacy `projects.owner_id`. |
| B2 | **API:** `GET/POST/PATCH/DELETE` `/v1/projects/{id}/members` | Multi-user projects | **Done:** `api/app/routers/projects.py` + membership checks; superusers treated as owner-level for admin. |
| B3 | **PATCH** `/v1/projects/{id}` — `name`, `description`, **`status`** `active|archived`, optional **`project_key`** | Align with plan | **Done:** API + **`ProjectSettingsForm`** on **`/projects/[id]`** (owners/maintainers). |
| B4 | **Web:** project **settings** or **members** sub-page | RBAC in UI | **Done:** **`/projects/[id]/members`** + settings card on overview. |

**Done when:** Non-owner collaborator can see project; viewer cannot mutate tasks (once tasks exist); owner can archive.

---

## Batch C — Components (plan Phase 1)

| # | Item | Why | Hints |
|---|------|-----|--------|
| C1 | **`Component`** model + **`sql/`** updates | Group work inside a project | **Done:** `components` table + ORM. |
| C2 | **API:** `/v1/projects/{id}/components` CRUD + `/v1/components/{id}` PATCH/DELETE | OpenAPI-style | **Done:** `api/app/routers/components.py`. |
| C3 | **Web:** under `/projects/[id]/components` (list + create) | User-visible structure | **Done:** + nav from overview. |

**Done when:** API + UI list/create components for a project the user can access.

---

## Batch D — Tasks & TODOs (MVP slice, plan Phase 1)

| # | Item | Why | Hints |
|---|------|-----|--------|
| D1 | **`Task`** model … | Core PM | **Done:** UUID-first `tasks` row (no human **`ref`** / counters yet — follow-up). |
| D2 | **API:** list/create/patch/delete + `POST .../transition` | Matches plan | **Done:** filters `status`, `assignee_id`, `component_id`. |
| D3 | **Web:** **table view** first (sortable); **Kanban** second PR | Table first | **Done:** **`/projects/[id]/tasks`** with **sortable** columns + assignee/due; Kanban explicitly later. |

**Done when:** Authenticated member can CRUD tasks scoped to project; list shows assigned/due basics.

---

## Batch E — Admin & auth clarity (parallelizable)

| # | Item | Why | Hints |
|---|------|-----|--------|
| E1 | **`/admin/users` forms** — create / patch / deactivate / reset password (local) | Plan §5.1 | **Done:** `AdminUsersPanel` + `/api/admin/users`. |
| E2 | **Document or implement admin for SSO** | `/v1/admin/*` local JWT only | **Done:** documented in **`/admin/users`** + **HANDOFF** (IdP claims = future). |
| E3 | **`GET /v1/auth/me` auth path** | JWKS vs userinfo | **Done:** OpenAPI description on route (`auth.py`). |

---

## Batch F — Phase 2 starter (**implemented — MVP slice**)

| Deliverable | Status |
|-------------|--------|
| **Activity** model + `GET`/`POST` per project + optional **SSE** stream (`/activities/stream`) | **Done** — `activities` table; `@email` in body creates **`mentions`** rows for existing users. |
| **Ticket** model + queue UI (separate from tasks) | **Done** — `tickets` + **`queue_slug`**; **`/projects/[id]/tickets`** + API **`/v1/projects/{id}/tickets`**, **`/v1/tickets/{id}`**. |
| **`/today`** + mentions | **Done** — **`GET /v1/me/today`** (assigned tasks with `due_at` in rolling window), **`GET /v1/me/mentions`**; web **`/today`** + nav link. |

Further hardening (not required to “close” F): richer SSE payloads, IdP-driven admin, human **`PRJ-123`** task refs, Kanban, mention notifications.

---

## Quick verification commands (Docker)

```bash
docker compose --profile dev up --build
docker compose --profile dev run --rm api python -m app.cli_schema apply-ddl   # DDL → bootstrap → backfill/inserts
curl -s "http://localhost:8300/docs"
docker compose run --rm --no-deps web sh -lc "npm ci --no-audit --no-fund && npm run check && npm run build"
```

---

*Update this file when a batch completes; keep **HANDOFF** snapshot in sync.*
