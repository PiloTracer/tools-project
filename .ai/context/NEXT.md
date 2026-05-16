# Next batch — tools-project (prioritized work)

**Purpose:** Backlog derived from **`.ai/plans/proposal/20260515-full-project.md`** (phases §10–§11) and repo reality.  
**North star:** same file — Phase **1** (domain core) → **2** (activity & tickets depth) → **3** (GitHub & polish).  
**Run dev stack:** `.cursorrules` / `docker compose --profile dev up --build` or `./bin/start.sh`.

**Schema:** declarative **`sql/`** only — no Alembic. On API startup: `schema_changes.sql` → `schema_indexes.sql` → bootstrap → `schema_backfill.sql` → `schema_inserts.sql`.

**Latest (repo):** **2026-05-16** — Phase **1** (**Batch G**) and Phase **2** core (**Batch H** + **P2–P5** mostly closed). **Working tree** may still carry edits on **project Activity** (`ActivityClient` / `page`), **ticket discussion** (`TicketDiscussion`), and **`attachments`** router — re-verify before treating as shipped. **`sql/`**: **`inbox_items`**, **`watchers`**, **`attachments`** with nullable **`task_id`** / **`ticket_id`**. Batch **A** whenever models change.

---

## Implementation status (verified 2026-05-16)

| ID | Scope | Status | Evidence / notes |
|----|-------|--------|------------------|
| **G1** | Kanban + drag-drop | **Done** | `web/src/components/KanbanBoard.tsx` (HTML5 DnD); `TasksView` in `TasksClient.tsx`; transition via `/api/tasks/[id]/transition`. |
| **G2** | Task detail route | **Done** | `web/src/app/projects/[id]/tasks/[taskId]/page.tsx`. |
| **G3** | Human refs in UX | **Done** | Task refs on **`/today`**; **`CmdkPalette`** search by title/ref; tasks table already had Ref column. |
| **G4** | ⌘K command palette | **Done** | `web/src/components/CmdkPalette.tsx` + `AppShell.tsx`. |
| **G5** | Project list health | **Done** | `GET /v1/projects` adds `ProjectHealth`; `web/src/app/projects/page.tsx` pills. |
| **P2** | Threaded replies (1 level) | **Done** | Ticket **`TicketDiscussion`**: Reply + thread; **project** **`ActivityClient`**: Reply + thread + `MarkdownEditor`; API rejects nested **`parent_activity_id`**. |
| **P4** | Task attachment parity | **Done** | `POST .../tasks/{id}/attachments`; activity validation for `subject_type=task`. |
| **P5** | Non-image uploads + caps | **Partial** | **`file_sniff`** (pdf, txt); UI **`filterUploadableFiles`**; upload **`413`** when payload exceeds **25 MiB** per file (`attachments.py`); **per-project file count** cap (**`429`**, `Settings.attachment_max_per_project`, env **`ATTACHMENT_MAX_PER_PROJECT`**). **Open:** per-project **total bytes** quota; **`retention_cutoff()`** in **`attachment_storage.py`** is **not** wired to download filtering or a purge job; **`attachment_retention_days`** / **`ATTACHMENT_RETENTION_DAYS`** exist on **`Settings`** but no job consumes them yet. |
| **H1** | Inbox + triage | **Done** | **`/v1/inbox`**, triage → task or ticket; web **`/inbox`** + BFF. |
| **H2** | Watchers + Today | **Done** | Watch API; **`/v1/me/today`** `watched_tickets`; Today UI. |
| **H3** | Richer SSE payload | **Done** | Stream JSON + **`ActivityStreamHint`** shows `kind`. |
| **H4** | Markdown-ish editor | **Partial** | **`MarkdownEditor`** on **project** composer + replies and **ticket** composer/reply with live **`mentionSuggestions`** → **`GET /v1/me/users/search`** (`ActivityClient.tsx`, `TicketDiscussion.tsx`). **`refSuggestions`** prop unused in app (no `#` task/ticket autocomplete until ref-search API + wiring). |
| **H5** | Activity on task mutations | **Done** | `api/app/services/activity_writer.py`; **`tasks`** router calls **`write_activity`** on create, assignee change, status patch, transition. |

**Earlier (2026-05-15, unchanged):** **P1** `activities.is_internal` end-to-end + ticket UI; **P3** ticket queue stale-age badges + legend.

### Open / follow-up (next sprint)

| # | Item |
|---|------|
| **H4** | **`refSuggestions`** + task/ticket **ref search** API (or reuse palette search) for `#` completion in **`MarkdownEditor`**; optional shared wrapper. |
| **P5** | Per-project **byte** totals; wire **`retention_cutoff`** into list/download or a **purge/cron** path; admin surfacing for caps/retention (optional). |
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
| **H** | Inbox, watches, SSE payload, task activity | **Core done**; **H4** `#` ref completion still open |

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
