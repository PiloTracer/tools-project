# Session handoff — tools-project

**Date:** 2026-05-16 (updated)

## Start here (new session)

1. Read **`.ai/context/CONTEXT.md`** — ports, auth modes, repo map.  
2. Read **`.ai/context/NEXT.md`** — **implementation status matrix** (Batch **G** + **H** + carryovers **all Done**); **open:** retention **purge** job, optional Inbox **`c`** shortcut, **Batch I** (GitHub).  
3. Full product / MVP scope: **`.ai/plans/proposal/20260515-full-project.md`**. Short brief: **`preliminary.md`**.  
4. **Docker-only** tooling for Node/Python (see **`.cursorrules`**).  
5. **No Alembic** — DDL under **`sql/`** (`schema_changes` → `schema_indexes` → bootstrap → `schema_backfill` → `schema_inserts`).

---

## Snapshot

| Area | Status |
|------|--------|
| **Auth** | Dual **local** + **OAuth**; **`GET /v1/auth/config`** drives **`/login`**. |
| **Web** | **`AppShell`**: Today, Projects, **Inbox**, **⌘K** + **`CmdkPalette`**; Kanban (`KanbanBoard` HTML5 DnD) + task detail; project **health** pills; ticket **threaded** discussion + **project Activity threaded replies**; **`MarkdownEditor`** wired with live `@mention` **+ `#ref`** autocomplete; **`WatchButtons`** on Today with watched tickets section. |
| **API** | Inbox, watches, **`/me/today`** + **`watched_tickets`**; task/project attachments + **`file_sniff`** (images + PDF + TXT); **per-project quotas** (file count via `ATTACHMENT_MAX_PER_PROJECT` + **byte total** via `ATTACHMENT_MAX_BYTES_PER_PROJECT`); **per-file 25 MiB** limit; **`retention_cutoff()`** helper + `ATTACHMENT_RETENTION_DAYS` config (hook ready, purge job deferred); task **activity** writes on create/transition/patch; **SSE** richer payload; **user search** (`GET /v1/me/users/search`) + **ref search** (`GET /v1/me/refs/search`) for autocomplete. |
| **Config** | New settings: `attachment_max_per_project` (default 500), `attachment_max_bytes_per_project` (default 0 = unlimited), `attachment_retention_days` (default 0). |
| **`./bin/start.sh`** | Interactive menu: compose progress + keypress ack (see script header). |

---

## Verified (2026-05-16)

- `docker compose --profile dev run --rm --no-deps api python -m compileall -q app` — clean.  
- `docker compose --profile dev run --rm --no-deps web sh -lc "npm ci && npm run check && npm run build"` — clean (1 ESLint **warning**: `@next/next/no-img-element` in **`TicketDiscussion.tsx`**).  
- `docker compose --profile dev run --rm api python -m app.cli_schema apply-ddl` — clean after DDL additions.  
- All API routers importable, all routes registered (inbox, watch, attachments, user search, ref search).

---

## Recommended next work

See **`.ai/context/NEXT.md`** and **Batch I** when Phase 1–2 are stable.

Small polish: wire retention purge job cron (hook exists in `attachment_storage.retention_cutoff()`); add global **`c`** shortcut for Inbox capture; swap inline `<img>` in ticket discussion for `next/image` or suppress ESLint rule.

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
- `MarkdownEditor` supports `mentionSuggestions` and `refSuggestions`; both are wired everywhere via `GET /v1/me/users/search` and `GET /v1/me/refs/search`. Type `@` for user mention, `#` for task/ticket ref lookup.
