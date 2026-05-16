# Session handoff — tools-project

**Date:** 2026-05-16 (updated)

## Start here (new session)

1. Read **`.ai/context/CONTEXT.md`** — ports, auth modes, repo map.  
2. Read **`.ai/context/NEXT.md`** — **implementation status matrix** (Batch **G** Phase 1 parity + carryover **P2–P5** + Batch **H** core); remaining gaps are called out there (**H4** editor wiring, **project** activity replies, retention/quota doc).  
3. Full product / MVP scope: **`.ai/plans/proposal/20260515-full-project.md`**. Short brief: **`preliminary.md`**.  
4. **Docker-only** tooling for Node/Python (see **`.cursorrules`**).  
5. **No Alembic** — DDL under **`sql/`** (`schema_changes` → `schema_indexes` → bootstrap → `schema_backfill` → `schema_inserts`).

---

## Snapshot

| Area | Status |
|------|--------|
| **Auth** | Dual **local** + **OAuth**; **`GET /v1/auth/config`** drives **`/login`**. |
| **Web** | **`AppShell`**: Today, Projects, **Inbox**, **⌘K** hint + **`CmdkPalette`**; **`/inbox`**; **`/projects/[id]/tasks`**: Kanban + table; **`/projects/[id]/tasks/[taskId]`** task detail; projects list **health** pills; ticket **threaded replies** (one level, API-enforced). **`WatchButtons`** on Today. |
| **API** | **`/v1/inbox`**, **`/v1/inbox/{id}/triage`**; **`/v1/me/watch`** (GET/POST/DELETE); **`/v1/me/today`** returns **`watched_tickets`**; **task** + project-level **attachments** (`file_sniff`: images + pdf + plain text); **`POST .../tasks/{id}/attachments`**; task create/patch/transition → **`write_activity`**; **SSE** activity stream includes `kind`, `subject_type`, `subject_id`. |
| **DB** | Tables: **`inbox_items`**, **`watchers`**; **`attachments.task_id`** nullable **`ticket_id`** (project- or task-scoped files). Indexes: **`uq_watchers_user_subject`**, **`ix_attachments_task_id`**, inbox indexes. |
| **`./bin/start.sh`** | Interactive menu: compose progress + keypress ack (see script header). |

---

## Verified (2026-05-16)

- `docker compose --profile dev run --rm --no-deps api python -m compileall -q app` — clean.  
- `docker compose --profile dev run --rm --no-deps web sh -lc "npm ci && npm run check && npm run build"` — clean (1 ESLint **warning**: `@next/next/no-img-element` in **`TicketDiscussion.tsx`**).  
- `docker compose --profile dev run --rm api python -m app.cli_schema apply-ddl` — clean after DDL additions.

---

## Recommended next work

See **`.ai/context/NEXT.md`** “Open / follow-up” row and **Batch I** when Phase 1–2 are stable.

High-value small follow-ups: wire **`MarkdownEditor`** where comments are authored (**H4**); **project** `/activity` reply UI to match tickets (**P2** remainder); inbox triage → optional **Activity** row; attachment **quota/retention** note or counter (**P5** doc).

---

## Where to read more

| Doc | Role |
|-----|------|
| **`.ai/context/NEXT.md`** | Status matrix + backlog |
| **`.ai/context/CONTEXT.md`** | Stable technical context |
| **`.cursorrules`** | **No Alembic**; **`sql/`** workflow |
| **`.ai/plans/proposal/20260515-full-project.md`** | Full MVP / north-star plan |

---

## Agent notes

- **Do not commit** `.env` or `credentials/`.  
- Removed dead **`api/app/services/image_sniff.py`** — use **`file_sniff.py`** only.
