# Next batch — tools-project (prioritized work)

**Purpose:** Concrete backlog after **projects foundation** (owner-scoped CRUD, web shell, SSO → `users` via userinfo).  
**North star:** `.ai/plans/proposal/20260515-full-project.md` (Phase 1 → 2).  
**Run dev stack:** `.cursorrules` / `docker compose --profile dev up --build` or `./bin/start.sh`.

---

## Batch A — Data & migrations (do first)

| # | Item | Why | Hints |
|---|------|-----|--------|
| A1 | **Alembic** in `api/`: env, `alembic revision --autogenerate`, wire startup to **`upgrade head`** (or document “migrate then run” for prod) | Replace ad-hoc **`create_all`**; required before serious schema churn | `api/app/db.py` today calls `Base.metadata.create_all` in `init_db`. Add first revision: `users`, `projects`. |
| A2 | **Baseline existing DBs** | Anyone with a live `projects` table from `create_all` needs a migration that matches current models or a one-time stamp | If autogenerate conflicts, hand-edit first revision to match `app/models/user.py`, `app/models/project.py`. |

**Done when:** `alembic upgrade head` on empty DB creates schema; CI or docs show the command; new columns go through revisions only.

---

## Batch B — Projects: membership & RBAC (plan §4 / §6)

| # | Item | Why | Hints |
|---|------|-----|--------|
| B1 | **`ProjectMember`** model (`project_id`, `user_id`, `role`: owner / maintainer / contributor / viewer) | Plan assumes RBAC; today access is **`owner_id` only** | Migration + backfill: set existing `projects.owner_id` as `owner` member. |
| B2 | **API:** `GET/POST/PATCH/DELETE` `/v1/projects/{id}/members` (superuser or project owner to add; enforce role rules) | Multi-user projects | Replace “owner-only” checks in `projects` router with membership + role (e.g. viewer read-only). |
| B3 | **PATCH** `/v1/projects/{id}` — `name`, `description`, **`status`** `active|archived`, optional **`key`** for future refs | Align with plan domain table | Decide: keep **`slug`** as URL id vs introduce display **`key`** (`PRJ`) + numeric refs when **tasks** land. |
| B4 | **Web:** project **settings** or **members** sub-page (minimal table + invite by email if user exists) | Makes RBAC real in UI | Start read-only member list + server actions or BFF routes. |

**Done when:** Non-owner collaborator can see project; viewer cannot mutate tasks (once tasks exist); owner can archive.

---

## Batch C — Components (plan Phase 1)

| # | Item | Why | Hints |
|---|------|-----|--------|
| C1 | **`Component`** model + Alembic | Group work inside a project | FK `project_id`, `name`, optional `description`, optional `lead_user_id`. |
| C2 | **API:** `/v1/projects/{id}/components` CRUD + `/v1/components/{id}` PATCH/DELETE | Matches proposed OpenAPI | Scope by project membership. |
| C3 | **Web:** under `/projects/[id]/components` (list + create) | User-visible structure | Link from project overview. |

**Done when:** API + UI list/create components for a project the user can access.

---

## Batch D — Tasks & TODOs (MVP slice, plan Phase 1)

| # | Item | Why | Hints |
|---|------|-----|--------|
| D1 | **`Task`** model: `project_id`, optional `component_id`, `title`, `body`/`description`, **`status`** enum, **`priority`**, `assignee_id`, `reporter_id`, `due_at`, optional `parent_task_id`, **`is_todo`** bool | Core PM | Add `project_counters` + human **`ref`** (`PRJ-123`) when ready; can ship UUID-first + ref in follow-up. |
| D2 | **API:** list/create/patch/delete + optional `POST .../transition` | Matches plan | Filters: `status`, `assignee_id`, `component_id`. |
| D3 | **Web:** **table view** first (sortable); **Kanban** second PR | Table is faster to ship | `/projects/[id]/tasks` — reuse dashboard styling. |

**Done when:** Authenticated member can CRUD tasks scoped to project; list shows assigned/due basics.

---

## Batch E — Admin & auth clarity (parallelizable)

| # | Item | Why | Hints |
|---|------|-----|--------|
| E1 | **`/admin/users` forms** — create / patch / deactivate / reset password (local) | Plan §5.1; today mostly table | Use existing OpenAPI contracts. |
| E2 | **Document or implement admin for SSO** | `/v1/admin/*` still **`get_current_user_local`** — intentional for now | Either keep “local superuser only” and document, or map IdP admin claims later (see **HANDOFF**). |
| E3 | **`GET /v1/auth/me` auth path** | Plan §8.1 mentions JWKS; **current** code uses **userinfo + upsert** for OAuth | Update plan text or add JWKS as Phase-4 hardening so docs match code. |

---

## Batch F — Phase 2 starter (after Batch D)

Defer until tasks exist; order within Phase 2:

- **Activity** model + `POST`/`GET` activity per subject; **SSE** optional second step.
- **Ticket** model + queue UI (separate from tasks).
- **`/today`** (My focus): assigned tasks due, mentions (needs Mention model or placeholder).

---

## Quick verification commands (Docker)

```bash
docker compose --profile dev up --build
# API
docker compose run --rm --no-deps api sh -lc "pip install -e . && alembic upgrade head"  # once Alembic exists
curl -s "http://localhost:8300/docs"
# Web
docker compose run --rm --no-deps web sh -lc "npm ci --no-audit --no-fund && npm run check && npm run build"
```

---

*Update this file when a batch completes; keep **HANDOFF** snapshot in sync.*
