# Session handoff — tools-project

**Date:** 2026-06-18 (session close — repo restructured: `.ai/` → Agent OS framework, content migrated to `.work/`)

**Session status:** Closed · goal: verify `.ai.bak` content is safe to delete and confirm migration to `.work/`

**Repository state:** Structural repo reorganization — old `.ai/context/*` and `.ai/plans/*` migrated to `.work/`; `.ai/` now holds Agent OS framework (skills, templates, standards); `.cursorrules` is now the generic template.

## Start here (new session)

1. Read **`.work/context/CONTEXT.md`** — ports, auth modes, repo map (includes **`github_links` / `github_commits`**).  
2. Read **`.work/plans/NEXT.md`** — **G/H** matrix + **§ Batch I** (**I10** sub-track truth table, **I11** vs plan §11, **§ I12** = configure repo + PAT **via `/docs` or `curl`** until web UI exists).  
3. Full product / MVP scope: **`.work/plans/legacy-plans/proposal/20260515-full-project.md`**. Short brief: **`preliminary.md`**.  
4. **Docker-only** tooling for Node/Python (see **`.cursorrules`**).  
5. **No Alembic** — DDL under **`sql/`** (`schema_changes` → `schema_indexes` → bootstrap → `schema_backfill` → `schema_inserts`).

---

## Snapshot

| Area | Status |
|------|--------|
| **Auth** | Dual **local** + **OAuth**; **`GET /v1/auth/config`** drives **`/login`**. |
| **Web** | **`AppShell`**: Today, Projects, **Inbox**, **⌘K** + **`CmdkPalette`**; Kanban + task detail; project **health** pills; ticket **threaded** discussion + **project Activity** threaded replies; **`MarkdownEditor`** with **`@mention`** + **`#ref`**; **`WatchButtons`**. **No** project **GitHub** settings page or **`/projects/[id]/github`** route yet — use **API** (**`/docs`**) to add repo links until **I10d** web ships. |
| **API** | Inbox, watches, **`/me/today`**, **`/me/users/search`**, **`/me/refs/search`**; attachments + quotas; SSE-rich activity hints; **GitHub:** **`GET/POST/DELETE /v1/projects/{id}/github/links`**, **`POST …/links/{link_id}/sync`**, **`GET …/github/commits`** (`CommitSummary` always includes **`html_url`**); background poll (**`app/github_background.py`**, **`GITHUB_*`** env). |
| **DB** | Includes **`github_links`** (encrypted **`token_cipher`**), **`github_commits`** (**`html_url` NOT NULL**). |
| **Config** | Attachments: `attachment_max_per_project`, `attachment_max_bytes_per_project`, `attachment_retention_days`. GitHub: **`github_sync_enabled`**, **`github_poll_interval_seconds`**, **`github_poll_initial_delay_seconds`**, **`github_commits_per_sync`**; optional **`GITHUB_TOKEN_ENCRYPTION_KEY`** (see **`.env.example`**). |
| **`./bin/start.sh`** | Interactive menu: compose progress + keypress ack (see script header). |

---

## Verified (2026-05-16)

- `docker compose --profile dev run --rm --no-deps api python -m compileall -q app` — clean.  
- `docker compose --profile dev run --rm --no-deps web sh -lc "npm ci --no-audit --no-fund && npm run check && npm run build"` — clean (**1 ESLint warning**: `@next/next/no-img-element` in **`TicketDiscussion.tsx`**).  
- `docker compose --profile dev run --rm api python -m app.cli_schema apply-ddl` — clean with **`github_*`** DDL.  
- FastAPI app imports; **github** tag visible at **`http://localhost:8300/docs`**.

---

## Recommended next work

1. **Batch I web (plan §7 / `NEXT.md` I10d):** Next.js **`/projects/[id]/github`** + project **settings** subsection to POST **`github_repo_url`** + **`github_token`** (BFF proxy pattern like other routes).  
2. **`github_commit` activity rows** on sync (**I10c** remainder) + optional SSE hint updates.  
3. **`github_ref`** attach flow (**I10e**) for tasks / comments.  

**Small polish:** retention purge cron; global **`c`** Inbox shortcut; **`next/image`** or ESLint override for ticket discussion thumbnails.

---

## What this cycle produced

| Artifact | Description |
|----------|-------------|
| `.work/` | Project-specific working content (CONTEXT, HANDOFF, NEXT, legacy plans) migrated from old `.ai/` |
| `.ai/` | Agent OS framework structure (skills, standards, templates, concepts, workflows) |
| `.cursorrules` | Replaced with generic Agent OS cursorrules template (project-agnostic) |
| `.ai.bak` analysis | Verified all content already present in `.work/` — safe to delete |

## Where to read more

| Doc | Role |
|-----|------|
| **`.work/plans/NEXT.md`** | Status matrix + **Batch I** spec + **§ I12** (configure GitHub **now** via API) |
| **`.work/context/CONTEXT.md`** | Stable technical context |
| **`.cursorrules`** | Agent OS framework rules; **No Alembic**; **`sql/`** workflow |
| **`.work/plans/legacy-plans/proposal/20260515-full-project.md`** | Full MVP / north-star plan |

---

## Agent notes

- **Do not commit** `.env` or **`credentials/`** (never paste real PATs into chat).  
- **GitHub PAT today:** **`POST /v1/projects/{project_id}/github/links`** with JSON **`{ "github_repo_url": "https://github.com/org/repo", "github_token": "…" }`** — see **`NEXT.md` § I12** and OpenAPI **`/docs`**.  
- `MarkdownEditor`: **`mentionSuggestions`** + **`refSuggestions`** wired for project activity + ticket discussion.
- **Repo restructured:** old `.ai/context/*` and `.ai/plans/*` → `.work/`; `.ai/` now holds the Agent OS framework. See `.work/context/` and `.work/plans/legacy-plans/`.
- **`.ai.bak`** is a stale backup of old `.ai/` — all content already in `.work/`; safe to delete.
