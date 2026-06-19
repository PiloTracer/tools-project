# Session handoff — tools-project

**Date:** 2026-06-18

**Closed:** 2026-06-18 — all 4 milestones (M1–M4) of the clients-participants CRM plan complete. 26/26 tasks done.
**Updated:** 2026-06-18

Treat prior closed sessions as historical only; see "What this cycle produced" below.

**Repository state:** Framework aligned — brownfield repair complete: foundation doc 01 (scope), doc 04 (architecture), standards (CONVENTIONS, FEATURE_STANDARD, DIRECTORY_MAP), registries (ASSUMPTIONS, RISK_REGISTRY, UNKNOWNS), ADR-0001–0004 Decided. **Plan-master-ready: 2026-06-18.** `.cursorrules` REPLACE tokens resolved. **Batch J implementation gaps fixed:** prospect stage validation, pipeline service, client permission resolution in `deps.py`/routers, client portal pages, `actor_id` nullable for system activities, attachment purge wired. GitHub Batch I web (I10d) remains open pending a priority call.

## Start here (new session)

1. Read **`.work/context/CONTEXT.md`** — ports, auth modes, repo map (includes **`github_links` / `github_commits`**).  
2. Read **`.work/plans/NEXT.md`** — **G/H** matrix + **§ Batch I** (GitHub) + **§ Batch J** (clients-participants CRM).  
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

1. **Seed a client user** in `sql/schema_inserts.sql` so `/client/login` can be exercised locally.
2. **`github_ref` picker (M4-T4):** Build commit-cite UI for tasks/comments — backend validation exists, UI is TODO.
3. **Client task/ticket scope by company contacts:** Currently filtered by the signed-in contact's user_id; SPEC also mentions "their client company contacts".
4. **`next/image` migration:** Suppress or fix pre-existing ESLint warning in `TicketDiscussion.tsx`.
5. **Batch I web:** `/projects/[id]/github` page exists, `github_commit` activity is wired. Remaining polish is low priority.

---

## What this cycle produced

| Artifact | Description |
|----------|-------------|
| `.work/` | Project-specific working content (CONTEXT, HANDOFF, NEXT, legacy plans) migrated from old `.ai/` |
| `.ai/` | Agent OS framework structure (skills, standards, templates, concepts, workflows) |
| `.cursorrules` | Agent OS cursorrules template with project-specific `REPLACE:` values resolved |
| `.ai.bak` analysis | Verified all content already present in `.work/` — safe to delete |
| `.work/plans/foundation/20260618-01-initial-scope.md` | Product scope doc (brownfield synthesis) — includes PM + CRM domains |
| `.work/plans/foundation/20260618-04-architecture.md` | Architecture foundation — bounded contexts, tech stack, ADR register |
| `.ai/standards/CONVENTIONS.md` | Python + TypeScript coding conventions (inferred from repo) |
| `.ai/standards/FEATURE_STANDARD.md` | Feature SPEC template and lifecycle standard |
| `.ai/standards/DIRECTORY_MAP.md` | Repository layout and bounded context → directory mapping |
| `.work/plans/ASSUMPTIONS.md` | Assumption ledger |
| `.work/plans/RISK_REGISTRY.md` | Risk registry |
| `.work/plans/UNKNOWNS.md` | Unknowns registry (CRM architecture questions now decided in ADR-0001; Batch I vs CRM priority still open) |
| `.work/decisions/README.md` | ADR index |
| `.work/features/clients-participants/20260618-SPEC.md` | Feature SPEC: client companies, contacts, project access, sales pipeline — **Approved** |
| `.work/decisions/0001-client-contact-model.md` | ADR: client contact identity, access model, pipeline, roles |
| `.work/decisions/0002-backend-stack.md` | ADR: Python 3.11, FastAPI, SQLAlchemy async, PostgreSQL 16 |
| `.work/decisions/0003-frontend-stack.md` | ADR: Next.js 16, React 19, TypeScript |
| `.work/decisions/0004-hosting-deployment.md` | ADR: Docker Compose, dual auth, Fernet PAT encryption |
| `.work/plans/full/20260618-full-plan.md` | Full implementation plan — 4 milestones, 22 tasks, **Approved** |
| `api/app/models/prospect.py`, `client.py`, `client_contact.py`, `project_client.py`, `project_client_access.py` | 5 SQLAlchemy models for CRM (M1) |
| `sql/schema_changes.sql`, `sql/schema_indexes.sql` | DDL + indexes for 5 new CRM tables + `activities.actor_id` nullable |
| `sql/schema_inserts.sql` | Seed fixtures: prospects, client, contacts |
| `api/app/routers/prospects.py` | Prospects CRUD + stage transition with business rules |
| `api/app/routers/clients.py` | Clients CRUD router |
| `api/app/routers/client_contacts.py` | Client contacts sub-resource CRUD |
| `api/app/routers/project_clients.py` | Project-client link/unlink API |
| `api/app/routers/project_client_access.py` | Client access grant/revoke/update API |
| `api/app/routers/client_portal.py` | Client portal API: `/v1/me/client/projects/*` endpoints |
| `api/app/schemas.py` | Extended with 15+ CRM Pydantic schemas |
| `api/app/deps.py`, `api/app/services/project_access.py` | Client permission resolution: `get_current_client_participant`, `require_client_project_access`, `resolve_project_access` |
| `api/app/services/pipeline_service.py` | Prospect-to-client promotion service |
| `api/app/services/attachment_service.py` | Attachment retention purge service |
| `api/app/services/activity_writer.py` | `actor_id` made optional for system activities |
| `api/app/services/github_sync.py`, `api/app/github_background.py` | `github_commit` activity rows on sync, attachment purge wired in poll loop |
| `api/app/routers/activities.py` | Client `is_internal = false` filter, comment permission |
| `api/app/routers/tasks.py`, `api/app/routers/tickets.py` | Client participant scoping (visibility, create/edit gates) |
| `web/src/app/client/login/page.tsx` | Client portal login page |
| `web/src/app/client/dashboard/page.tsx` | Client dashboard listing accessible projects |
| `web/src/app/client/projects/[id]/page.tsx` | Client project detail: tasks + public activity |
| `web/src/app/projects/[id]/github/page.tsx` | GitHub commit history page |
| `web/src/app/projects/[id]/settings/page.tsx` | Project settings with GitHub repo management |
| `web/src/components/CmdkPalette.tsx` | Global `c` quick-capture shortcut → `/inbox` |

## Where to read more

| Doc | Role |
|-----|------|
| **`.work/plans/NEXT.md`** | Status matrix + **Batch I** spec + **§ Batch J** (clients-participants CRM) |
| **`.work/plans/full/20260618-full-plan.md`** | Full implementation plan — milestones M1–M4 |
| **`.work/context/CONTEXT.md`** | Stable technical context |
| **`.work/decisions/README.md`** | ADR index (0001–0004) |
| **`.cursorrules`** | Agent OS framework rules; **No Alembic**; **`sql/`** workflow |
| **`.work/plans/legacy-plans/proposal/20260515-full-project.md`** | Full MVP / north-star plan |

---

## Agent notes

- **Do not commit** `.env` or **`credentials/`** (never paste real PATs into chat).  
- **GitHub PAT today:** **`POST /v1/projects/{project_id}/github/links`** with JSON **`{ "github_repo_url": "https://github.com/org/repo", "github_token": "…" }`** — see **`NEXT.md` § I12** and OpenAPI **`/docs`**.  
- `MarkdownEditor`: **`mentionSuggestions`** + **`refSuggestions`** wired for project activity + ticket discussion.
- **Repo restructured:** old `.ai/context/*` and `.ai/plans/*` → `.work/`; `.ai/` now holds the Agent OS framework. See `.work/context/` and `.work/plans/legacy-plans/`.
- **`.ai.bak`** is a stale backup of old `.ai/` — all content already in `.work/`; safe to delete.
