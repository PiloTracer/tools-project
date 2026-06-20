# Session handoff — tools-project

**Date:** 2026-06-18

**Closed:** 2026-06-20 — backup/restore overhaul: .tar.gz volumes only, no pg_dump
**Updated:** 2026-06-20

**Open:** (none — session closed)

Treat prior closed sessions as historical only; see "What this cycle produced" below.

****Repository state:** All follow-ups complete. SPEC FR-5 runtime-verified (Alice sees Bob's company-scoped tasks). App logger cosmetic gap fixed (`logging.basicConfig` in `main.py`). `commit_subject_refs` normalized cross-link table + watcher hooks (I10f) implemented. Inbox `c` shortcut confirmed already implemented. Batch I (GitHub) + Batch J (CRM) complete. UI design foundation complete; all CRM screens delivered.

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
| **Web** | **`AppShell`**: Today, Projects, **Inbox**, **⌘K** + **`CmdkPalette`**; Kanban + task detail; project **health** pills; ticket **threaded** discussion + **project Activity** threaded replies; **`MarkdownEditor`** with **`@mention`** + **`#ref`**; **`WatchButtons`**. **GitHub tab** (`/projects/[id]/github`) with linked repos + commit table; **GitHub settings** (add/remove repos + PAT) in project settings; **`github_commit` activity cards** with rich SHA/preview rendering; **commit picker** ("Cite commit") in activity composer + reply forms. |
| **API** | Inbox, watches, **`/me/today`**, **`/me/users/search`**, **`/me/refs/search`**; attachments + quotas; SSE-rich activity hints; **GitHub:** **`GET/POST/DELETE /v1/projects/{id}/github/links`**, **`POST …/links/{link_id}/sync`**, **`GET …/github/commits`** (`CommitSummary` always includes **`html_url`**); background poll (**`app/github_background.py`**, **`GITHUB_*`** env). |
| **DB** | Includes **`github_links`** (encrypted **`token_cipher`**), **`github_commits`** (**`html_url` NOT NULL**). |
| **Config** | Attachments: `attachment_max_per_project`, `attachment_max_bytes_per_project`, `attachment_retention_days`. GitHub: **`github_sync_enabled`**, **`github_poll_interval_seconds`**, **`github_poll_initial_delay_seconds`**, **`github_commits_per_sync`**; optional **`GITHUB_TOKEN_ENCRYPTION_KEY`** (see **`.env.example`**). |
| **`./bin/start.sh`** | Interactive menu with cleanup, backup/restore, dev/prd mode routing, nuke. |
| **UI** | Foundation complete; all CRM screens delivered (prospects list/detail, clients list/detail); 14 catalog primitives. 3 screen SPECs pass `@ui-screen-spec review` — pending human approval (Draft→Approved). prospects-list SPEC already Approved. |

---

## Verified (2026-05-16)

- `docker compose --profile dev run --rm --no-deps api python -m compileall -q app` — clean.  
- `docker compose --profile dev run --rm --no-deps web sh -lc "npm ci --no-audit --no-fund && npm run check && npm run build"` — clean (**1 ESLint warning**: `@next/next/no-img-element` in **`TicketDiscussion.tsx`**).  
- `docker compose --profile dev run --rm api python -m app.cli_schema apply-ddl` — clean with **`github_*`** DDL.  
- FastAPI app imports; **github** tag visible at **`http://localhost:8300/docs`**.

---

## Verified (2026-06-19)

- `docker compose -f docker-compose.prd.yml build` — exit 0 (api + web prd images).
- Cold start (new volumes): 0 errors, 4× `Application startup complete`, 19 tables, `restarts=0`.
- Routes via Caddy HTTPS: `/healthz` 200 · `/v1/auth/config` 200 · `/` 200 HTML · `/docs` 200 · HTTP→HTTPS 308.
- Local login flow: JWT issued → `GET /v1/auth/me` 200 `is_superuser:true`.
- Restart stability: 0 errors, 4× `startup complete`, `restarts=0`.
- Standalone auth: bootstrap admin created, 50 prospects + 2 demo projects seeded.
- Fail-fast guards: empty env → exit 1 with clear message.

### Follow-up session (2026-06-19)

- `docker compose -f docker-compose.dev.yml --profile dev run --rm --no-deps api python -m compileall -q app` — **COMPILE_OK** (exit 0); validates `project_access.py`, `tasks.py`, `tickets.py`, `client_portal.py` company-scoping edits. `ruff` not installed in dev image (placeholder per `.cursorrules`).
- `docker compose -f docker-compose.dev.yml --profile dev run --rm --no-deps web npm run check` — **exit 0** (PASS, 0 errors + 0 warnings). Fixed: `ProspectPreview.tsx` `react-hooks/set-state-in-effect` error (restructured to render-time state reset + effect cleanup) and 8 `no-img-element` warnings across 7 files (eslint-disable-next-line, matching existing blob-URL-thumbnail convention).
- `npm run build` — **BUILD_OK** (exit 0).

---

## Recommended next work

All follow-ups are complete. The project has no open blocking work.

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
| `bin/start.sh` | Extended: cleanup, backup, restore, dev/prd mode routing, `confirm_yes` helper, menu input fix |
| `docker-compose.dev.yml`, `docker-compose.prd.yml` | Compose split into dev/prd variants |
| `.env.dev`, `.env.prd` | Environment files per mode |
| `sql/schema_indexes.sql` | Dedup DELETE + `uq_client_contacts_email` unique index |
| `sql/schema_inserts.sql` | Demo client user seed (alice@umbrella-corp.test, bcrypt, project grants) |
| `api/app/main.py` | Added imports: `project_clients`, `project_client_access` |
| `web/next.config.ts` | Added `turbopack: { root: "/app" }` for Next.js 16 |
| `web/src/app/client/login/page.tsx` | Form styling: `.field`/`.input`/`.label` classes, `stack-lg` spacing |
| `.work.ui/screens/prospects-list/20260618-SCREEN-SPEC.md` | Prospects list screen SPEC (Draft) — admin-dashboard, pipeline table view |
| `api/app/services/github_sync.py` | Fixed duplicate activity bug — only returns `is_new` commits |
| `api/app/github_background.py` | Only writes `github_commit` activity for genuinely new commits |
| `api/app/routers/github.py` | Added `q` search param to `GET /github/commits` |
| `api/app/routers/activities.py` | Added `github_ref` validation on activity create |
| `web/src/components/CommitPicker.tsx` | New CommitPicker component — search commits, insert markdown ref |
| `web/src/app/projects/[id]/activity/ActivityClient.tsx` | Rich `github_commit` activity card rendering; CommitPicker in composer + replies |
| `.work/plans/full/20260618-full-plan.md` | M4 tasks updated to `done` |
| `.work/plans/NEXT.md` | Batch I status updated to complete |
| `web/Dockerfile.prd` | Removed dead `COPY /app/public` (path doesn't exist in repo) |
| `docker-compose.prd.yml` | Added `PUBLIC_HOST` env to caddy service with `:?` fail-fast guard |
| `api/Dockerfile.prd` | `cli_schema apply-ddl` before `uvicorn --workers 4` + `SQL_SCHEMA_APPLY=false` — fixes DDL race (UniqueViolation + Deadlock across workers) |
| `.work.ui/screens/prospects-detail/20260619-SCREEN-SPEC.md` | Fixed: §3 states (added empty/partial/permission-denied), §8 catalog (Button/Input→native allowed), §12 UIS registry (UIS-01..09), §13 extractedRules provenance, §7 feature SPEC link |
| `.work.ui/screens/clients-list/20260619-SCREEN-SPEC.md` | Fixed: §3 states, §8 catalog, §12 UIS registry, §13 extractedRules + `(binding)` label, §7 API paths (`/api/`→`/v1/`) |
| `.work.ui/screens/clients-detail/20260619-SCREEN-SPEC.md` | Fixed: §3 states, §10 PII (`contact_email`→`contact_id`), §8 catalog, §12 UIS registry, §13 extractedRules + exampleIds (D1+D2), §7 API paths, §4 regionMap |
| `.work.ui/screens/{prospects-detail,clients-list,clients-detail}/20260619-SCREEN-SPEC.md` | Status flipped Draft→**Approved** 2026-06-19 (human-approved after passing `@ui-screen-spec review`) |
| `.work.ui/screens/prospects-list/20260619-SCREEN-SPEC-amendment-01.md` | Amendment to Approved prospects-list SPEC: §8 Button/Input `done`→`native allowed` per CATALOG.md § Missing |
| `api/app/services/project_access.py` | New `client_company_user_ids(db, acc)` helper — user ids of all contacts in the signed-in contact's client company (SPEC FR-5) |
| `api/app/routers/tasks.py`, `tickets.py`, `client_portal.py` | Client participant task/ticket visibility now scopes by **company contacts** (`assignee_id.in_(peer_ids)`) instead of just `user.id` — implements SPEC FR-5 |
| `web/src/app/projects/[id]/tickets/[ticketId]/TicketDiscussion.tsx` | Added `eslint-disable-next-line @next/next/no-img-element` to reply attachment `<img>` (matches existing pattern) — eliminates the `no-img-element` warning in this file |

## What this cycle produced (2026-06-20)

| Artifact | Description |
|----------|-------------|
| `api/app/main.py` | Added `logging.basicConfig(level=logging.INFO)` — startup SQL markers now visible |
| `sql/schema_changes.sql` | Added `commit_subject_refs` DDL |
| `sql/schema_indexes.sql` | Added indexes + unique constraint for `commit_subject_refs` |
| `api/app/models/commit_subject_ref.py` | SQLAlchemy model for `CommitSubjectRef` |
| `api/app/models/__init__.py` | Registered `CommitSubjectRef` |
| `api/app/schemas.py` | Added `CommitSubjectRefCreate`, `CommitSubjectRefOut`, `CommitSubjectRefListResponse` |
| `api/app/routers/commit_refs.py` | New router: GET/POST/DELETE `/v1/projects/{id}/github/refs` |
| `api/app/routers/activities.py` | Auto-create `CommitSubjectRef` when `github_ref` present in activity |
| Runtime verification | SPEC FR-5 cross-visibility verified with Alice + Bob (Umbrella Corp) |
| `bin/start.sh` | Backup/restore overhaul: no pg_dump, .tar.gz volume-only backup; restore now removes+recreates volumes to overwrite existing data |

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

### UI layer (see .work.ui/)
- Active UI milestone: Batch J — CRM Pipeline Front-End **closed 2026-06-19**
- Foundation complete: yes · Screen-spec-ready: yes
- Implementation complete: yes (all CRM screens delivered)
- All verifiers: PASS · All UIS concepts: PASS
- CATALOG.md populated (14 components); prospects-list SPEC Approved (+ amendment 01: Button/Input→native allowed)
- 3 screen SPECs reviewed, fixed, and **Approved** 2026-06-19 (prospects-detail, clients-list, clients-detail) — all pass `@ui-screen-spec review`
- NEXT_UI: `.work.ui/plans/NEXT_UI.md`

## Agent notes

- **Do not commit** `.env` or **`credentials/`** (never paste real PATs into chat).  
- **GitHub PAT today:** **`POST /v1/projects/{project_id}/github/links`** with JSON **`{ "github_repo_url": "https://github.com/org/repo", "github_token": "…" }`** — see **`NEXT.md` § I12** and OpenAPI **`/docs`**.  
- `MarkdownEditor`: **`mentionSuggestions`** + **`refSuggestions`** wired for project activity + ticket discussion.
- **Repo restructured:** old `.ai/context/*` and `.ai/plans/*` → `.work/`; `.ai/` now holds the Agent OS framework. See `.work/context/` and `.work/plans/legacy-plans/`.
- **`.ai.bak`** is a stale backup of old `.ai/` — all content already in `.work/`; safe to delete.
