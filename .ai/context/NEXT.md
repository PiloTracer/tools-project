# Next batch — tools-project (prioritized work)

**Purpose:** Backlog derived from **`.ai/plans/proposal/20260515-full-project.md`** (phases §10–§11) and repo reality.  
**North star:** same file — Phase **1** (domain core) → **2** (activity & tickets depth) → **3** (GitHub & polish).  
**Run dev stack:** `.cursorrules` / `docker compose --profile dev up --build` or `./bin/start.sh`.

**Schema:** declarative **`sql/`** only — no Alembic. On API startup: `schema_changes.sql` → `schema_indexes.sql` → bootstrap → `schema_backfill.sql` → `schema_inserts.sql`.

**Latest (repo):** Batches **A–F** delivered (projects, members, components, tasks table + transitions, admin users, activity + mentions + tickets + **`/today`**). **Extended:** ticket **case** page (`/projects/[id]/tickets/[ticketId]`), queue triage ordering, **attachments** (`attachments` table, ticket image upload, activity `meta_json.attachment_ids`, BFF **`/api/attachments/[id]`**), Compose volume **`tpr_attachments`**. Batch **A** stays ongoing whenever models change.

---

## Carryover priorities (close gaps from the ticket / activity slice)

These items were explicitly deferred or only partially met vs plan §5.1 / §11.4 — **do first** when opening the next sprint so the slice does not rot.

| # | Item | Why |
|---|------|-----|
| **P1** | **`activities.is_internal`** (SQL + model + `ActivityCreate` / `ActivityOut`) + **UI** on ticket (and later task) comments: “Internal note” vs customer-visible | Plan §5.1 / acceptance §11.4 (internal + external note on a ticket). |
| **P2** | **Threaded replies** in UI: `parent_activity_id` already in API — expose “Reply” on ticket discussion + project **Activity** page; validate one-level depth per plan | §5.1 threaded replies (one level MVP). |
| **P3** | **Ticket queue “stale” signal** — color or badge when ticket is older than N days without status change (N configurable per project later; start with global default) | Plan §5.1 queue + §13 success metric. |
| **P4** | **Task attachment parity** — same upload pattern for `subject_type=task` (or `POST .../tasks/{id}/attachments`) + activity linking | Avoid permanent ticket-only asymmetry; plan §4.1 Attachment allows task_id. |
| **P5** | **Non-image uploads** (pdf, txt) + stricter **quota / retention** hook (counter or doc only) | Plan §8.4 caps; §12 risk. |

---

## Batch G — Phase 1 plan parity (domain core “done”)

Aligned with **20260515-full-project.md §10 Phase 1** (Kanban + table, refs, keyboard shortcuts where feasible).

| # | Item | Why | Hints |
|---|------|-----|--------|
| G1 | **Kanban** for tasks (`/projects/[id]/tasks`) — columns by `status`, **drag-and-drop** between columns | §5.1 / §10 Phase 1; acceptance §11.3 | Prefer `@dnd-kit` or HTML5 DnD; `PATCH` or `POST .../transition` on drop; emit **activity** (`kind=status_change` or `comment` stub) if not already. |
| G2 | **Task detail route** ` /projects/[id]/tasks/[taskId]` | §7 web surface | Summary, description, subtasks link, assignee/due, link to component; optional thread later. |
| G3 | **Surface human refs everywhere** | `ref` already allocated for tasks/tickets — ensure **⌘K** / search can target them when G4 exists; show ref in headers | `api/app/services/ref_alloc.py`; tasks table already shows **Ref** column. |
| G4 | **`⌘K` command palette** (minimal): jump to project / task / ticket by title or ref; stub actions “New task here” | §5.1 / §10 Phase 1 (palette); §11.6 | `cmdk` or headless pattern from plan §7; server list endpoints or client cache. |
| G5 | **Project list health badges** (lightweight): open task count, open ticket count, “oldest open ticket age” | §5.1 health card / §10 | Read-only aggregates; defer full health card to later. |

**Done when:** User can **drag a task on Kanban**, open a **task detail** URL, and hit **⌘K** to jump by ref or title; projects list shows **at least one** health signal.

---

## Batch H — Phase 2 remainder (PM hub “alive”)

Aligned with **§10 Phase 2** after P1–P5 and Batch G foundations.

| # | Item | Why | Hints |
|---|------|-----|--------|
| H1 | **Quick Capture inbox** ` /inbox` + **`POST /v1/inbox`** + triage **`POST /v1/inbox/{id}/triage`** | §5.1 / §7 | Global modal shortcut `c` can follow; start with page + API. |
| H2 | **Watchers** model + **`POST/DELETE /v1/me/watch`** + **`/today`** section for watched tickets/tasks | §5.1 My Focus; plan §4.1 Watcher | SQL `watchers` table; RBAC read on subject. |
| H3 | **Richer SSE** (optional): push `{kind, subject_id}` or activity id so client avoids full reload | §8.3 | Today: poll / lightweight SSE id; extend payload. |
| H4 | **Markdown-ish editor** shared: `@` mention autocomplete, `#` ref links — incrementally | §5.1 | Can start with plain textarea + server-side mention parse (already partially there). |
| H5 | **Activity on task mutations** from web (create/assign/status) if not already uniform | §11.3 “see the activity entry” | Verify task create/patch writes `Activity` rows where plan expects. |

**Done when:** Inbox + triage happy path works; user can **watch** a ticket and see it on **`/today`**; task lifecycle creates **visible activity** without gaps.

---

## Batch I — Phase 3 preview (GitHub & polish)

Touch only when **G + H** are stable: **`GithubLink`** + PAT storage, commit poller, commit rows in activity (`github_commit`); saved views; theme polish per plan §10 Phase 3.

---

## Batch A — Schema discipline (maintain continually)

| # | Item | Why | Hints |
|---|------|-----|--------|
| A1 | **`sql/schema_changes.sql`** ↔ **`api/app/models`** | Primary DDL | `IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`. |
| A2 | **`sql/schema_indexes.sql`** | Indexes / constraints | Idempotent. |
| A3 | **`sql/schema_backfill.sql`** | Row fixes for existing DBs | Idempotent only. |
| A4 | **`sql/schema_inserts.sql`** | Seeds after bootstrap | `ON CONFLICT`; avoid random UUIDs for fixtures unless static. |

**Current tables (non-exhaustive):** `users`, `projects`, `project_members`, `components`, `tasks`, `activities`, `mentions`, `tickets`, **`attachments`**, **`project_counters`**.

---

## Completed batches (reference — do not reopen unless regressing)

| Batch | Scope | Status |
|-------|--------|--------|
| **B** | Project members, RBAC, PATCH project, web members/settings | **Done** |
| **C** | Components API + UI | **Done** |
| **D** | Tasks: API transitions, filters, **table** UI, **`ref`** via counters | **Done** (Kanban = **G1**) |
| **E** | Admin user forms, auth docs | **Done** |
| **F** | Activities, mentions, tickets queue API, **`/today`** | **Done** + **ticket case**, **image attachments**, queue ordering |

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
