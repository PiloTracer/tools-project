# Next batch — tools-project (prioritized work)

**Purpose:** Backlog derived from **`.ai/plans/proposal/20260515-full-project.md`** (phases §10–§11) and repo reality.  
**North star:** same file — Phase **1** (domain core) → **2** (activity & tickets depth) → **3** (GitHub & polish).  
**Run dev stack:** `.cursorrules` / `docker compose --profile dev up --build` or `./bin/start.sh`.

**Schema:** declarative **`sql/`** only — no Alembic. On API startup: `schema_changes.sql` → `schema_indexes.sql` → bootstrap → `schema_backfill.sql` → `schema_inserts.sql`.

**Latest (repo):** **2026-05-16** — Phase **1** parity items (**Batch G**) and most **carryover P2–P5** + **Batch H** core are implemented in working tree (see **Implementation status** below). **`sql/`** updated: **`inbox_items`**, **`watchers`**, **`attachments.task_id`**, nullable **`attachments.ticket_id`**. Batch **A** stays ongoing whenever models change.

---

## Implementation status (verified 2026-05-16)

| ID | Scope | Status | Evidence / notes |
|----|-------|--------|------------------|
| **G1** | Kanban + drag-drop | **Done** | `web/src/components/KanbanBoard.tsx` (HTML5 DnD); `TasksView` in `TasksClient.tsx`; transition via `/api/tasks/[id]/transition`. |
| **G2** | Task detail route | **Done** | `web/src/app/projects/[id]/tasks/[taskId]/page.tsx`. |
| **G3** | Human refs in UX | **Done** | Task refs on **`/today`**; **`CmdkPalette`** search by title/ref; tasks table already had Ref column. |
| **G4** | ⌘K command palette | **Done** | `web/src/components/CmdkPalette.tsx` + `AppShell.tsx`. |
| **G5** | Project list health | **Done** | `GET /v1/projects` adds `ProjectHealth`; `web/src/app/projects/page.tsx` pills. |
| **P2** | Threaded replies (1 level) | **Partial** | Ticket **`TicketDiscussion`**: Reply + threaded render; **`POST /v1/.../activities`** rejects nested parent. **Project `/activity`** reply UI still missing. |
| **P4** | Task attachment parity | **Done** | `POST /v1/projects/{pid}/tasks/{tid}/attachments`; activity **`meta_json`** validation for `subject_type=task`. |
| **P5** | Non-image uploads | **Partial** | **`api/app/services/file_sniff.py`**: pdf + plain text; **quota / retention** not implemented (doc/counter still open). |
| **H1** | Inbox + triage | **Done** | **`/v1/inbox`**, **`POST .../triage`** → task or ticket; `web/src/app/inbox/`, BFF `web/src/app/api/inbox/`. |
| **H2** | Watchers + Today | **Done** | **`watchers`** + **`POST/DELETE /v1/me/watch`**, **`GET /v1/me/watches`**; **`/v1/me/today`** includes **`watched_tickets`**; Today UI + `WatchButtons.tsx`. |
| **H3** | Richer SSE payload | **Done** | `activities.activity_stream` emits `kind`, `subject_type`, `subject_id` (client may still only use `latest_activity_id`). |
| **H4** | Markdown-ish editor | **Stub** | `web/src/components/MarkdownEditor.tsx` **not wired** into ticket/task composers. |
| **H5** | Activity on task mutations | **Done** | `api/app/services/activity_writer.py`; **`tasks`** router calls **`write_activity`** on create, assignee change, status patch, transition. |

**Earlier (2026-05-15, unchanged):** **P1** `activities.is_internal` end-to-end + ticket UI; **P3** ticket queue stale-age badges + legend.

### Open / follow-up (next sprint)

| # | Item |
|---|------|
| **P2** | **Reply** on **project** `/activity` (mirror ticket UX). |
| **H4** | Wire **`MarkdownEditor`** + incremental `#` / `@` helpers. |
| **P5** | Retention / size **quota** (counter or ops doc). |
| **H1** | Optional global **`c`** quick-capture shortcut. |
| **Batch I** | GitHub integration — gate until G+H stable. |

---

## Batch G — Phase 1 (reference)

Original acceptance: Kanban, task detail URL, ⌘K, health on projects list — **met** (see matrix).

---

## Batch H — Phase 2 (reference)

Inbox, watches, richer SSE, task activity — **met** (see matrix). **H4** editor integration remains.

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

**Current tables (non-exhaustive):** `users`, `projects`, `project_members`, `components`, `tasks`, `activities`, `mentions`, `tickets`, **`attachments`**, **`project_counters`**, **`inbox_items`**, **`watchers`**.

---

## Completed batches (reference — do not reopen unless regressing)

| Batch | Scope | Status |
|-------|--------|--------|
| **B** | Project members, RBAC, PATCH project, web members/settings | **Done** |
| **C** | Components API + UI | **Done** |
| **D** | Tasks: API transitions, filters, **table** UI, **`ref`** via counters | **Done** (Kanban = **G1**) |
| **E** | Admin user forms, auth docs | **Done** |
| **F** | Activities, mentions, tickets queue API, **`/today`** | **Done** + **ticket case**, **attachments**, queue ordering |
| **G** | Phase 1 parity: Kanban, task detail, ⌘K, project health | **Done** (see Implementation status) |
| **H** | Inbox, watches, SSE payload, task activity | **Core done**; **H4** editor wiring open |

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
