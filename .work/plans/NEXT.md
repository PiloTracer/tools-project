# Next batch — tools-project (prioritized work)

**Purpose:** Backlog derived from **`.work/plans/legacy-plans/proposal/20260515-full-project.md`** (phases §10–§11) and repo reality.  
**North star:** Phase **1** (domain core) → **2** (activity & tickets depth) → **3** (GitHub & polish) — see **§ Batch I — GitHub integration** below for the **active** specification.  
**Run dev stack:** `./bin/start.sh dev` (mode is mandatory: `dev` → `.env.dev`, `prd` → `.env.prd`; a bare `.env` is never read).

**Schema:** declarative **`sql/`** only — no Alembic. On API startup: `schema_changes.sql` → `schema_indexes.sql` → bootstrap → `schema_backfill.sql` → `schema_inserts.sql`.

****Latest (repo):** **2026-09-29** — plan-sync P1 complete: milestones + plan-import API shipped, all gates green (ruff, pyright, 49 tests), migration idempotent across restart×2, live smoke test passed. Prior: **2026-07-07** — Multi-tenancy implementation verified and repaired: all lint/type/test/DDL gates green (33 tests pass). Feature remains gated behind `MULTI_TENANCY_ENABLED=false`; default tenant backfill keeps existing single-tenant behavior working.

### Status at a glance (visual)

```text
Phase 1 (G)     ████████████████████  5/5   Done
Carryovers P    ████████████████████  3/3   Done (P2, P4, P5)
Phase 2 (H)     ████████████████████  5/5   Done (H1–H5)
Phase 3 (I)     ████████████████████  6/6   Done (I10a–I10g)
────────────────────────────────────────────────
Matrix (G+H+P)  ████████████████████  14/14 Done
Improvements    ████████████████████  8/8   Done (2026-06-29 sess 1)
Improvements    ████████████████████  5/5   Done (2026-06-29 sess 2)
Documentation   ████████████████████  12/12 Done (2026-06-29 sess 3)
Batch K         ████████████████████  3/3   Done (opp-to-project automation)
Batch L         ████████████████████  3/3   Done (client health dashboard)
Security fixes  ████████████████████  8/8   Done (config, auth, endpoint hardening)
Pen test rem.   ████████████████████  9/9   Done (all findings addressed)
Multi-tenancy   ████████████████████  Done  (implementation verified; 33 tests pass)

Open: none (**cross-LLM verification of the plan-sync P1 commit `11432fe` — PASS 2026-09-30**; see HANDOFF § Cross-LLM verification)
Active: **TNT iteration complete** (tenant context: single-tenant writes + multi-tenant selection; stack control plane + env-file contract) — **committed 2026-09-30** on owner instruction

### Recommended next
1. **NEXT SESSION (user directive 2026-09-29): cross-LLM verification of the plan-sync P1 commit.** Open the session with a *different* LLM than the one that authored the commit. Procedure: (a) `git log -1 --oneline` + `git show --stat HEAD` to locate the plan-sync commit; (b) review the diff against `.work/features/plan-sync/20260929-SPEC.md` rules R1–R27; (c) re-run gates inside the container (`docker exec tpr_api_tools_project_dev bash -c "cd /app && ruff check . && pyright . && python -m pytest -q"`); (d) record pass/fail in HANDOFF. **No new feature work until verification passes.**
2. **Multi-tenancy:** mark `.work/features/multi-tenancy/20260706-SPEC.md` as **Approved**, then add HTTP-level cross-tenant leak tests for all tenant-scoped routers (prospects, clients, client_contacts, admin_users, admin_webhooks, projects, agent_query).
3. Add automated tests for the ecosystem hub modifications (Mod 1–4) if not already covered.
4. Build satellite apps (CompanyBrain, OpsBoard, SignFlow, LedgerLite) that consume the ecosystem APIs.
5. Restart the dev stack and smoke-test tenant-scoped login + CRUD end-to-end.
6. **plan-sync P3:** web UI — milestone list, task-by-milestone filter, obsolete badge (SPEC §2); next iteration per plan-sync P1 scope split.
7. **plan-sync P2:** `@plan-sync` agent skill — work order for the framework handed over at `.work/prompts/20260929-plan-sync-skill-instructions.md` (decision: direct HTTP, option (a); MCP stays read-only). Deliver to `pilo.ai.logicbison`, then `@deploy-basic` here to pick up the skills table row.

### Intake queue
- 2026-07-06 · local · "assess making this app multi-tenant" → SPEC created at `.work/features/multi-tenancy/20260706-SPEC.md` (Draft)

## Current iteration — TNT: tenant context (single-tenant writes + multi-tenant selection)

**Milestone ref:** TNT · source: `.work/features/multi-tenancy/20260706-SPEC.md` (§Feature flag, R2, R2b, R4a/R4c, R5, R9b, R9c, R13a)
**Status:** complete — owner commit decision pending
**Started / Completed:** 2026-09-30
**Trigger:** owner-reported production defect — `POST /v1/projects` answered `400 tenant_id or tenant_slug is required for cross-tenant superuser` for the bootstrapped admin (`admin@example.com`, `tenant_id IS NULL`) while production runs `MULTI_TENANCY_ENABLED=false` (confirmed live: `GET https://project.cloudsys.win/v1/auth/config` → `multi_tenant:false`). Same defect was logged as a backlog candidate at the end of the plan-sync P1 block below.

### In scope
- Single-tenant (flag off): `get_current_tenant` returns the `default` tenant (SPEC §Feature flag); bootstrap + schema backfill guarantee that row; tenant-scoped creates stamp it
- Multi-tenant (flag on): subdomain → `X-Tenant-Slug` → authenticated user's tenant resolution, `403` when a caller names another tenant (R2b), `401` when nothing resolves
- Login: tenant-aware local login incl. tenant-less superusers, real `300 Multiple Choices` for per-tenant duplicate emails (R5/R9b)
- OAuth: tenant-scoped lookup, `300` on ambiguity, no auto-provisioning (R9b/R9c)
- Web: tenant selection cookie forwarded as `X-Tenant-Slug`, `/select-tenant` picker, login/oauth/logout lifecycle, middleware guard
- Env passthrough: every `Settings` field reachable through `docker-compose.dev.yml` / `docker-compose.prd.yml`; `.env.example` / `.env.dev` document them
- Dev image installs the `dev` extra so `pytest` runs in-container

### Out of scope (explicit)
- Marking the multi-tenancy SPEC `Approved` (owner action) and flipping `MULTI_TENANCY_ENABLED` in production (stays `false`)
- HTTP-level cross-tenant leak tests for *all* tenant-scoped routers (this iteration covers auth/login/tenancy resolution + clients; prospects/client_contacts/admin_users/admin_webhooks/agent_query remain per NEXT § Recommended next 2)
- plan-sync P2/P3, satellite apps

### Tasks
| ID | Description | Files | Status | Notes |
|----|-------------|-------|--------|-------|
| TNT-T1 | Shared tenancy helpers (default tenant, write-tenant resolution) | `api/app/services/tenancy.py` | done | new module |
| TNT-T2 | Tenant resolution dependency + auth deps publish the caller's tenant | `api/app/deps.py`, `api/app/main.py` | done | flag-off → `default`; flag-on → subdomain/header/user; 403 on foreign tenant |
| TNT-T3 | Bootstrap always ensures the `default` tenant | `api/app/bootstrap.py` | done | was flag-gated |
| TNT-T4 | Tenant-scoped creates stamp the resolved tenant | `api/app/routers/projects.py`, `api/app/routers/clients.py`, `api/app/routers/prospects.py`, `api/app/routers/admin_webhooks.py`, `api/app/routers/admin_users.py`, `api/app/routers/me_api_keys.py`, `api/app/routers/integrations.py` | done | single-tenant admin no longer needs `tenant_slug`; multi-tenant keeps R13a |
| TNT-T5 | Local login tenant context + `300 Multiple Choices`; token echoes tenant binding | `api/app/routers/auth.py`, `api/app/schemas.py` | done | cross-tenant superuser can log in on any tenant context |
| TNT-T6 | OAuth tenant-scoped lookup, ambiguity → `300`, no auto-provisioning | `api/app/services/oauth_userinfo.py` | done | R9b/R9c |
| TNT-T7 | Web tenant plumbing: cookie, `X-Tenant-Slug` forwarding, picker, lifecycle, guard | `web/src/shared/server/tenant.ts`, `web/src/shared/server/session.ts`, `web/src/shared/server/proxy-api.ts`, `web/src/middleware.ts`, `web/src/app/api/auth/tenant/route.ts`, `web/src/app/api/auth/local/login/route.ts`, `web/src/app/api/auth/logout/route.ts`, `web/src/app/oauth/complete/route.ts`, `web/src/app/select-tenant/page.tsx`, `web/src/app/select-tenant/SelectTenantPanel.tsx`, `web/src/app/projects/page.tsx`, `web/src/app/login/page.tsx`, `web/src/shared/types/me.ts` | done | picker validates against `/v1/admin/tenants` (fail-closed) |
| TNT-T8 | Env passthrough for API + web services, both stacks | `docker-compose.dev.yml`, `docker-compose.prd.yml`, `.env.example`, `.env.dev` | done | protected surfaces — owner-approved in-message 2026-09-30 |
| TNT-T9 | Dev image installs the `dev` extra (pytest in container) | `api/Dockerfile.dev` | done | protected surface — owner-approved in-message 2026-09-30 |
| TNT-T10 | Regression tests: resolution, login, OAuth scope | `api/tests/test_tenancy_resolution.py`, `api/tests/test_login_tenant_context.py`, `api/tests/test_oauth_tenant_scope.py`, `api/tests/conftest.py`, `api/tests/factories.py` | done | 20 new tests |
| TNT-T11 | Gates: ruff, pyright, pytest, schema runner ×2, restart ×2, web check + build, live dual-mode checks | (validation steps) | done | see below |
| TNT-T12 | Foreign dirty files present but **not** part of this iteration (declared for scope honesty) | `.gitignore`, `.work/feedback/20260930-uncommitted-changes-feedback.md` | n-a | `.gitignore` changed by host tooling during the session; feedback report authored by a separate session — owner decides keep/revert |
| TNT-T13 | Iteration bookkeeping + change-safety evidence | `.work/plans/NEXT.md`, `.work/context/HANDOFF.md` | done | iteration block, MOD-06 summary, cross-LLM verification record |
| TNT-T14 | Stack control plane: mandatory dev/prd mode, mode-only env files, `bin/env-check.sh` preflight | `bin/start.sh`, `bin/env-check.sh`, `.env.example`, `.env.dev`, `README.md`, `.work/docs/QUICK_START.md`, `.work/context/CONTEXT.md`, `api/README.md` | done | no bare `.env` reachable; env completeness verified before every Docker action |
| TNT-T15 | Env files 1-to-1 aligned (example / dev / prd) + prd duplicate-key repair + dev SSO wiring + doc references | `.cursorrules`, `docker-compose.dev.yml`, `bin/env-check.sh`, `.env.example`, `.env.dev`, `README.md`, `api/README.md` | done | prd file repaired in `/mnt/work/Projects/tools-project-secret/` (timestamped backup kept); values preserved, only `PUBLIC_HOST` de-duplicated |
| TNT-T16 | Plan-sync usage reference doc (sync example with project UUID, modes, ref/commit-linking caveat, troubleshooting) | `.work/docs/reference/PLAN_SYNC.md`, `README.md` | done | example: `@plan-sync sync - <plan> --project 6becd67b-…` (Mendarion) |
| TNT-T17 | Plan-sync P3 web UI: tasks grouped by milestone + milestone/plan-state filters + friendly task presentation, SPEC R21a amendment, framework work order | `web/src`, `.work/features/plan-sync/20260929-SPEC.md`, `.work/feedback/adjustments-for-plan-sync-skill/`, `.work/docs/reference/PLAN_SYNC.md`, `README.md` | done | 12 milestones / 159 imported tasks readable at a glance; description parser tolerates legacy + R21a shapes |
| TNT-T18 | Owner feedback on plan-sync P3: task detail returns to the exact view/filter you came from, original technical text available on the task detail, and the Members "Add member" button actually works | `web/src/app/projects/[id]/tasks/`, `web/src/app/projects/[id]/members/InviteMemberForm.tsx`, `web/src/components/PlanTaskBody.tsx` | done | verified in a real browser: view/filter survive the round trip, member added end-to-end, 0 client errors |

### Acceptance criteria
- [x] Single-tenant: bootstrapped admin creates project/client/prospect/webhook/user/API key → 201, rows in the `default` tenant (T1–T4)
- [x] Single-tenant: tenant-bound user behavior unchanged (T2)
- [x] Multi-tenant: Bearer-only session resolves the user's own tenant; foreign `X-Tenant-Slug` → 403; cross-tenant superuser writes into the selected tenant; nothing resolved → 401 (T2, T4)
- [x] Ambiguous email → `300` with choices (local login and OAuth); unknown OAuth email → 401 (T5, T6)
- [x] Missing `default` row → 500 with actionable detail instead of a NULL-tenant write (T2/T4)
- [x] Web: login persists the tenant; BFF forwards `X-Tenant-Slug`; session without a selection routes to the picker; picker rejects unknown slugs (T7)
- [x] Every `Settings` field reachable from both compose files (T8)
- [x] Gates green inside the container + web build (T11)

### Validation steps
- [x] 2026-09-30T16:41:50-06:00 `docker exec tpr_api_tools_project_dev bash -c "cd /app && ruff check . && pyright . && python -m pytest -q"` → ruff `All checks passed`; pyright `0 errors, 0 warnings, 0 informations`; `69 passed`
- [x] Schema runner ×2 (documented `MIGRATION_RUN_CMD`): `python -m app.cli_schema apply-ddl` → no errors; only pre-existing `SQL file empty or unparsed, skipping: /sql/schema_inserts.sql` (that file is 0 bytes)
- [x] API container restart ×2 → `/healthz` `{"status":"ok","db":"ok"}`; `SELECT slug,name FROM tenants WHERE slug='default'` → `default | Default Organization`
- [x] Web: `npm run check` (eslint) clean; `npm run build` → `✓ Compiled successfully`; route table includes `/select-tenant` and the middleware
- [x] Live single-tenant: `POST /v1/projects` as `admin@example.com` → 201; `GET /v1/projects` → 200; `/v1/auth/config` → `multi_tenant:false`; web `/projects` → 200
- [x] Live multi-tenant (stack run with `MULTI_TENANCY_ENABLED=true`, no new DB rows): login with `tenant_slug=default` → 200 + `prj_tenant` cookie; `/projects` with cookie → 200 (proves header forwarding); without cookie → 307 `/select-tenant?next=%2Fprojects`; `/select-tenant` → 200 listing `Default Organization`; `POST /api/auth/tenant {default}` → 200, `{does-not-exist}` → 404
- [x] `touch-scope-verify --strict` → pass (scope declared by this block); `blast-radius-check` → warn (high lines/areas + protected hits, owner-approved)

### Owner blockers
- Protected surfaces touched (`docker-compose.dev.yml`, `docker-compose.prd.yml`, `.env.example`, `api/Dockerfile.dev`) — approved by the owner in the same message that requested them (2026-09-30: items 1–3), per `.cursorrules` § Protected Files.
- Commit is **not** performed by the agent: staging scope + draft message handed over (standing rule).

### Concept / NFR registry (this iteration)
| Concept id | Applies | Status | Evidence / trigger |
|------------|---------|--------|-------------------|
| MOD-01 | yes | done | Diff crosses 3 boundaries (api / web / deploy config) — coupling note inside the MOD-06 summary below (no new runtime coupling: existing HTTP surface only) |
| MOD-02 | no | n-a | No new synchronous network hop: the web→API path is unchanged; only one header added |
| MOD-03 | no | n-a | No new billable unit |
| MOD-04 | no | n-a | No new deployable or on-call surface |
| MOD-05 | no | n-a | No service extraction |
| MOD-06 | **yes** | done | AI-assisted: yes — risk summary attached below; recommendation `merge_with_conditions` |
| MOD-07 | no | n-a | No app-side LLM prompt composition |
| MOD-08 | no | n-a | No IaC change |

#### MOD-06 output — AI change risk summary (TNT, 2026-09-30)

```markdown
## AI change risk summary
- AI-assisted: yes
- Boundaries crossed: 3 — API service (`api/`), web app (`web/`), deployment config
  (`docker-compose.dev.yml`, `docker-compose.prd.yml`, `.env.example`, `api/Dockerfile.dev`).
  [measured: `git diff --name-only` + untracked list; 38 files, ~754 changed lines]
- New cross-boundary deps: none at runtime — the web app reaches the API only through the
  existing HTTP surface (one added request header `X-Tenant-Slug`); no new route family,
  service, shared model, or DB access path. Config coupling is intentional and symmetric
  (both compose files + `.env.example` carry the same variable set).
- Test isolation: ok for the API — command:
  `docker exec tpr_api_tools_project_dev bash -c "cd /app && python -m pytest -q
  tests/test_tenancy_resolution.py tests/test_login_tenant_context.py
  tests/test_oauth_tenant_scope.py"` (20 tests isolate tenant resolution, login and OAuth
  scope); full suite `69 passed` [measured 2026-09-30T16:41:50-06:00].
  Weak for the web app — repo has no JS test runner (`web/package.json` = lint only);
  web evidence is eslint + `next build` + live curl/redirect checks [measured].
- Human architectural review: required — reason: >1 boundary crossed and the change alters
  authorization/tenant-resolution semantics (who may read/write which tenant's rows) in a
  system serving production traffic.
- Blast radius: if this change is wrong, the failure modes are (a) a tenant-scoped write is
  attributed to the wrong tenant, or (b) a caller reads another tenant's rows. (a) is bounded
  by `resolve_write_tenant_id` + the NOT NULL `tenant_id` columns (a missing tenant now fails
  loudly instead of writing NULL); (b) is bounded by resolution order (caller's own tenant wins;
  a foreign subdomain/slug is 403) and by the `users` CHECK constraint that keeps tenant-less
  users superuser-only. Single-tenant deployments are unaffected in behaviour except that the
  bootstrapped admin gains the writes it should always have had. Worst operational case: a
  multi-tenant deployment (production is *not* one today) rejects requests it previously
  served — fail-closed, no data loss, no migration to roll back (no schema change in this diff).

## Recommendation
merge_with_conditions — all gates green and both modes live-verified, but the diff crosses
3 boundaries and changes auth semantics in a deployment with no JS test runner.

## Conditions if merge_with_conditions
- Must add tests: web-side coverage for the tenant cookie lifecycle once a JS test runner
  exists; API leak tests for the remaining tenant-scoped routers (prospects,
  client_contacts, admin_users, admin_webhooks, agent_query) — tracked as NEXT § Recommended
  next 2.
- Must split PR: exclude the two foreign dirty files (`.gitignore`,
  `.work/feedback/20260930-uncommitted-changes-feedback.md`) from the staging scope.
- Owner review of the OAuth no-auto-provisioning behaviour change (SPEC R9c alignment) and of
  the protected-file edits before merge.
```

## Current iteration — plan-sync P1: schema + import API

**Milestone ref:** plan-sync P1 · source: `.work/features/plan-sync/20260929-SPEC.md` (Approved) + `.work/plans/proposals/20260929-plan-sync-proposal.md` §15 P1
**Status:** complete (2026-09-29)
**Started:** 2026-09-29
**Completed:** 2026-09-29 — gates green (ruff, pyright, pytest 49/49), migration restart×2 idempotent, live smoke test 14/14 checks OK
**Waiver:** no plan-master exists in this repo (brownfield, legacy plans only); operator instruction 2026-09-29 ("go full" on plan-sync) is the implementation authorization. Tasks trace to SPEC rules R1–R27 instead of a master-plan §19 table.

### In scope
- DDL: `milestones` table, `tasks.milestone_id`/`plan_ref`/`plan_state`, indexes (idempotent, restart-run) — SPEC R27
- Milestone model + registration; task columns
- Schemas: `MilestoneCreate/Out`, `PlanImportManifest/Result`, `TaskOut`+filters
- `plan_import` service: validate, transactional upsert, obsolete matrix, conflict report, side-effect suppression — SPEC R5–R20
- Milestone router: CRUD + `POST /v1/projects/{id}/plan-import` (JWT or X-Api-Key) — SPEC R2, R3, R11
- D6: `auto_prefix_enabled` decoupled from GitHub link gate — SPEC R23
- Task list filters `milestone_id`, `plan_state` — SPEC R25
- Backend tests T1–T11 + migration idempotency T12; gates ruff/pyright/pytest

### Out of scope (explicit)
- Web UI (next iteration, P3)
- Agent skill `@plan-sync` (framework repo, P2)
- BC→component mapping, sync banner (P4)
- Kanban-by-milestone, gantt, registries import (SPEC §2)

### Tasks
| ID | Description | Files | Status | Notes |
|----|-------------|-------|--------|-------|
| T1 | DDL: milestones table + 3 task columns + indexes | `sql/schema_changes.sql`, `sql/schema_indexes.sql` | done | idempotent only (ADR-0004); verified restart×2, zero errors |
| T2 | Milestone model + Task columns + registration | `api/app/models/milestone.py`, `api/app/models/task.py`, `api/app/models/__init__.py` | done | partial uniques stay in SQL |
| T3 | Schemas: milestones, manifest, result, task filters | `api/app/schemas.py` | done | |
| T4 | plan_import service (validate/upsert/obsolete/report) | `api/app/services/plan_import.py` | done | + flush after milestone loop (autoflush disabled in test factory; tasks need milestone ids) |
| T5 | Milestone router + import endpoint + registration | `api/app/routers/milestones.py`, `api/app/main.py` | done | + `agent_identity.ensure_agent_user` FK anchor (agent key's synthetic user is not in `users`) |
| T6 | D6: split auto_prefix vs registry gating | `api/app/routers/projects.py` | done | registry gate preserved (400 verified live) |
| T7 | Task list filters milestone_id, plan_state | `api/app/routers/tasks.py` | done | |
| T8 | Tests: import matrix, auth, D6, filters | `api/tests/test_plan_sync.py` | done | 16 tests; SPEC §11 T1–T11 |
| T9 | Gates: ruff, pyright, pytest + migration restart×2 | (validation steps) | done | container-exec; plus live smoke test (14 checks) |

### Acceptance criteria
- [x] Fresh import manifest → 12 milestones + 153 tasks; second import idempotent (T1, T2)
- [x] Obsolete matrix all 4 rows + in-progress conflict never auto-killed (T4)
- [x] Local `done` survives re-import; nothing deleted (T3, R18)
- [x] `dry_run` writes nothing; commit atomic (T6)
- [x] 1 summary activity for 10-task import; no webhooks (T7)
- [x] X-Api-Key allowed only on import; role checks enforced (T8)
- [x] `auto_prefix_enabled` works without GitHub link; imported tasks get refs (T10)
- [x] Restart twice → migration idempotent, zero errors (T12)
- [x] Gates green: ruff, pyright, pytest (T13)

### Validation steps
- [x] `docker compose -f docker-compose.dev.yml exec api ruff check .` → All checks passed
- [x] `docker compose -f docker-compose.dev.yml exec api pyright .` → 0 errors
- [x] `docker compose -f docker-compose.dev.yml exec api pytest -q` → 49 passed
- [x] Restart API container twice; confirm `Executing SQL file` lines + no errors; spot-check `\d milestones` → 15 columns incl. plan_ref/plan_state; tasks has milestone_id/plan_ref/plan_state
- [x] Manual: `POST /v1/projects/{id}/plan-import?dry_run=true` returns diff, DB unchanged → live smoke [5]/[6] (counts 2/5, tasks total 0)

### Owner blockers
- none

### Concept / NFR registry (this iteration)
| Concept id | Applies | Status | Evidence / trigger |
|------------|---------|--------|-------------------|
| MOD-01 | yes | done | Coupling audit in proposal Appendix C: score `low`, `proceed_with_guards`; diff touches api+sql only (web deferred) |
| MOD-02 | no | n-a | No new synchronous network hop |
| MOD-03 | no | n-a | No new billable unit |
| MOD-04 | no | n-a | No new deployable/on-call surface |
| MOD-05 | no | n-a | No service extraction |
| MOD-06 | **yes** | done | AI-assisted: yes; risk summary attached below (2026-09-29) |
| MOD-07 | no | n-a | No app-side LLM prompt composition |
| MOD-08 | no | n-a | No IaC change |

#### MOD-06 output — AI change risk summary (plan-sync P1, 2026-09-29)

```markdown
## AI change risk summary
- AI-assisted: yes
- Boundaries crossed: 1 — API service (Python app + its own restart-run SQL schema;
  one deploy unit: api container). Web untouched; framework repo untouched (P2
  deferred); `.work` docs are not a code boundary. Aligns with MOD-01 Appendix C
  (score: low, proceed_with_guards).
- New cross-boundary deps: none — intra-package imports only
  (routers/services/models within api); no new network hop, service, or shared DB access.
- Test isolation: ok — command: `docker exec tpr_api_tools_project_dev python -m pytest -q
  tests/test_plan_sync.py` (16 tests isolate import/obsolete/auth/D6/filter logic;
  failure→fix cycle observed during this session). Full suite: 49 passed [measured]
- Human architectural review: optional — reason: boundaries_crossed ≤ 1 and
  isolated tests exist; owner reviews before merge regardless.
- Blast radius: if wrong, a single project's task/milestone metadata could be
  mis-statused or wrongly marked obsolete — never deleted (R18), single transactional
  write path, dry_run available, one summary activity row for audit. Migration is
  additive and idempotent (IF NOT EXISTS), verified across restart×2 [measured].
  The deps.py edit touches the shared X-Api-Key auth path (platform/agent_query)
  but is value-identical (named constants + dead-import removal), covered by the
  full 49-test suite [measured].

## Recommendation
merge_ok — single boundary, isolated tests green, gates green (ruff, pyright,
pytest 49/49), live smoke test 14/14, no destructive operations.

## Conditions if merge_with_conditions
- (none)
```

### Cross-LLM verification
- Triggered: no (not a high-risk threat-model milestone)

### Done this iteration
| Task | Completed | Notes |
|------|-----------|-------|
| T1 DDL | 2026-09-29 | milestones table (15 cols) + 3 task columns + 7 indexes; restart×2 idempotent |
| T2 models | 2026-09-29 | `models/milestone.py` + Task/Project relationships |
| T3 schemas | 2026-09-29 | milestone + manifest + result schemas, `MILESTONE_STATUSES`, `PLAN_TASK_STATUS_MAP` |
| T4 service | 2026-09-29 | `services/plan_import.py` R5–R20; +flush fix (task.milestone_id was NULL without it) |
| T5 router | 2026-09-29 | milestones CRUD + plan-import endpoint; +`services/agent_identity.py` FK anchor for agent-key writes |
| T6 D6 gate | 2026-09-29 | auto_prefix decoupled from GitHub link; registry gate retained |
| T7 filters | 2026-09-29 | `milestone_id` + `plan_state` query filters |
| T8 tests | 2026-09-29 | `tests/test_plan_sync.py` — 16 tests (SPEC T1–T11, D6, D7, R2, R13) |
| T9 gates | 2026-09-29 | ruff clean, pyright 0 errors, pytest 49/49, restart×2, live smoke 14/14 |
| Pre-existing lint debt | 2026-09-29 | cleared 3 baseline findings outside plan-sync scope to get gates green: `client_portal.py` SIM102 (nested if), `admin_users.py` pyright nullable `user_id` guard, `deps.py` dead `Request` import — all behavior-neutral |
| MOD-06 | 2026-09-29 | risk summary attached above; recommendation merge_ok |

**Left in dev DB:** project "Plan Sync Smoke Test" (`bd3b7835-cb2c-454e-b091-513df5233436`, slug `plan-sync-smoke`, key PSMOKE) from the live smoke run — no project DELETE endpoint exists; safe to remove manually if undesired.

**Observation (pre-existing, not plan-sync):** in single-tenant mode the bootstrap admin (`tenant_id` NULL) cannot `POST /v1/projects` (400 "tenant_id or tenant_slug is required for cross-tenant superuser") because `get_current_tenant` returns None when `MULTI_TENANCY_ENABLED=false`. Smoke test used the tenant-bound dev user instead. **Fixed 2026-09-30** — see «Current iteration — TNT» above (this defect reached production; owner-reported).

## Current iteration (2026-07-06)

**Goal:** Land ecosystem hub modifications 1–4 with passing task gate.

| # | Task | Status | Notes |
|---|------|--------|-------|
| T1 | Implement outbound event dispatcher (Mod 1) | **Done** | `api/app/services/webhook_dispatcher.py`, `api/app/routers/admin_webhooks.py`, `api/app/models/webhook_subscription.py` |
| T2 | Implement platform whoami (Mod 2) | **Done** | `api/app/routers/platform.py` |
| T3 | Implement cross-app references (Mod 3) | **Done** | `api/app/routers/external_refs.py` |
| T4 | Implement RFP award webhook (Mod 4) | **Done** | `api/app/routers/integrations.py` |
| T5 | Fix lint/type failures across codebase | **Done** | ruff + pyright clean |
| T6 | Fix GitHub token encryption error in dev stack | **Done** | `.env.dev` key + compose env passthrough + invalid dev link removed |
| T7 | Update iteration scope in NEXT.md | **Done** | this section |
| T8 | Add pytest + tests for new routers/services | **Done** | 25 tests in `api/tests/` covering Mod 1–4 + utilities |

## Done this iteration

- All Mod 1–4 code implemented and registered in `app/main.py`.
- `ruff check .` passes.
- `pyright .` passes (0 errors, 0 warnings).
- Dev stack starts cleanly; API / web health endpoints respond.
- GitHub poll no longer crashes on missing/invalid encryption key.

## New features (2026-07-06)

### Ecosystem hub modifications (Mod 1–4)

| ID | Scope | Status | Evidence |
|----|-------|--------|----------|
| Mod 1 | Outbound event dispatcher — HMAC-signed webhooks + admin subscriptions | **Done** | `api/app/services/webhook_dispatcher.py`, `api/app/routers/admin_webhooks.py`, `api/app/models/webhook_subscription.py` |
| Mod 2 | Platform whoami — shared identity for satellite apps | **Done** | `api/app/routers/platform.py` — `GET /v1/platform/whoami` |
| Mod 3 | Cross-app references — generic `external_refs` over `commit_subject_refs` | **Done** | `api/app/routers/external_refs.py` |
| Mod 4 | RFP award webhook — accept `tools-rfp` award, promote to client/project | **Done** | `api/app/routers/integrations.py` — `POST /v1/integrations/rfp/award` |

## New features (2026-07-01)

### M — Agent Query API

| ID | Scope | Status | Evidence |
|----|-------|--------|----------|
| M1 | `/v1/agent/` aggregation endpoints (projects, context, tasks, tickets, search) | **Done** | `api/app/routers/agent_query.py` — 5 endpoints, Pydantic response models, single-query N+1 optimization |
| M2 | Personal API keys (`POST /v1/me/keys`, `GET /v1/me/keys`, `DELETE /v1/me/keys/{id}`) | **Done** | `api/app/routers/me_api_keys.py` — SHA-256 hashed, `tools_project_` prefix, one-time plaintext display |
| M3 | `user_api_keys` table + model | **Done** | `sql/schema_changes.sql`, `api/app/models/user_api_key.py` — UUID PK, key_hash, key_prefix, last_used_at |
| M4 | `require_agent_or_user` X-Api-Key auth | **Done** | `api/app/deps.py` — resolves: agent_api_key → user_api_keys (SHA-256) → Bearer JWT |
| M5 | MCP server (5 tools) | **Done** | `.opencode/mcp/project-mcp/mcp_server.py` — JSON-RPC 2.0, reads `~/.tools-project-key` or env |
| M6 | Web UI: `/settings/api-keys` | **Done** | `web/src/app/settings/api-keys/` — table, create dialog with one-time secret display, revoke confirmation |
| M7 | Documentation + tutorial | **Done** | `.work/docs/agent-query-api.md` (reference), `.work/docs/tutorials/LLM-2-API_SETUP.md` (step-by-step) |
| M8 | Feature SPEC | **Done** | `.work/features/agent-query-api/20260701-SPEC.md` |

## New features (2026-06-29)

### K — Opportunity-to-Project Automation
| ID | Scope | Status | Evidence |
|----|-------|--------|----------|
| K1 | Auto-scaffold project + tasks on prospect promotion | **Done** | `api/app/services/pipeline_service.py` — 7 onboarding tasks, client link, access grants, activity entry |
| K2 | Return project info in promotion response (API) | **Done** | `ProspectStageChangeResponse.promoted_project`, `ProspectPromoteResponse` |
| K3 | Frontend: "View project" link in success dialog | **Done** | Detail page + list page both show project link alongside client link |

### L — Client Health Dashboard
| ID | Scope | Status | Evidence |
|----|-------|--------|----------|
| L1 | `GET /v1/clients/health` endpoint with scoring | **Done** | `api/app/routers/client_health.py` — task completion, ticket burden, activity recency weighted score |
| L2 | Health dashboard UI on `/clients` | **Done** | Toggle "Health"/"List" view, stat cards, color-coded health cards with scores |
| L3 | Feature SPECs reviewed and Approved | **Done** | `.work/features/opp-to-project-auto/` + `client-health-dashboard/` |

---

## Implementation status — Phases 1–2 (verified 2026-05-16)

| ID | Scope | Status | Evidence / notes |
|----|-------|--------|------------------|
| **G1** | Kanban + drag-drop | **Done** | `web/src/components/KanbanBoard.tsx` (HTML5 DnD); `TasksView` in `TasksClient.tsx`; transition via `/api/tasks/[id]/transition`. |
| **G2** | Task detail route | **Done** | `web/src/app/projects/[id]/tasks/[taskId]/page.tsx`. |
| **G3** | Human refs in UX | **Done** | Task refs on **`/today`**; **`CmdkPalette`** search by title/ref; tasks table already had Ref column. |
| **G4** | ⌘K command palette | **Done** | `web/src/components/CmdkPalette.tsx` + `AppShell.tsx`. |
| **G5** | Project list health | **Done** | `GET /v1/projects` adds `ProjectHealth`; `web/src/app/projects/page.tsx` pills. |
| **P2** | Threaded replies (1 level) | **Done** | Ticket **`TicketDiscussion`**: Reply + thread; **project** **`ActivityClient`**: Reply + thread + `MarkdownEditor`; API rejects nested **`parent_activity_id`**. |
| **P4** | Task attachment parity | **Done** | `POST .../tasks/{id}/attachments`; activity validation for `subject_type=task`. |
| **P5** | Non-image uploads + caps | **Done** | **`file_sniff`** (pdf, txt); per-file **25 MiB** limit (**`413`**); **per-project file count** cap (**`429`**, `Settings.attachment_max_per_project`, **`ATTACHMENT_MAX_PER_PROJECT`**); **per-project byte total** quota when set above zero (**`429`**, `Settings.attachment_max_bytes_per_project`, **`ATTACHMENT_MAX_BYTES_PER_PROJECT`**); **retention hook** (`retention_cutoff()` + **`ATTACHMENT_RETENTION_DAYS`** — purge job deferred). |
| **H1** | Inbox + triage | **Done** | **`/v1/inbox`**, triage → task or ticket; web **`/inbox`** + BFF. |
| **H2** | Watchers + Today | **Done** | Watch API; **`/v1/me/today`** `watched_tickets`; Today UI. |
| **H3** | Richer SSE payload | **Done** | Stream JSON + **`ActivityStreamHint`** shows `kind`. |
| **H4** | Markdown-ish editor | **Done** | **`MarkdownEditor`** on **project** composer + threaded replies and **ticket** discussion with **`mentionSuggestions`** and **`refSuggestions`** (BFF + API). |
| **H5** | Activity on task mutations | **Done** | `api/app/services/activity_writer.py`; **`tasks`** router calls **`write_activity`** on create, assignee change, status patch, transition. |

**Earlier (2026-05-15, unchanged):** **P1** `activities.is_internal` end-to-end + ticket UI; **P3** ticket queue stale-age badges + legend.

### Open / follow-up (non–Batch I)

| # | Item |
|---|---|
| **P5** | Wire **retention** purge cron job (hook `retention_cutoff()` exists); admin surfacing for caps (optional). |
| **H1** | Optional global **`c`** quick-capture shortcut. |
| **J0** | **Batch J — CRM clients-participants:** schema + models; prospects CRUD + pipeline transitions; clients, contacts, project linking; client access/permission resolution; `/client/login` + limited project view. |

**Batch I (GitHub) — shipped vs next:** see **§ I10** (sub-track status) and **§ I12** (how to add repo + PAT **today** without a web form). **`20260515-full-project.md`** Phase **3** / §11 item **8** remain **open** until the **GitHub** web tab and **`github_commit`** activity feed land.

---

## Batch G — Phase 1 (reference)

Original acceptance: Kanban, task detail URL, ⌘K, health on projects list — **met** (see matrix).

---

## Batch H — Phase 2 (reference)

Inbox, watches, richer SSE, task activity, markdown editor — **met** (see matrix).

---

## Batch I — GitHub integration (Phase 3) — **specification**

This section **extends** **`20260515-full-project.md`** §4.1 / §5.1 / §6 / §8.5 with product choices that stay **easy to integrate** and **loosely coupled** to multiple UI surfaces (project overview, activity feed, task detail, ticket thread, Today, ⌘K, future watcher digests, etc.).

### I0 — Alignment with the existing plan (unchanged intent)

- **Read-only MVP first:** link repos → poll GitHub → cache commits → surface in **Activity** as `kind = github_commit` (already allowed in `api/app/schemas.py` activity kinds).
- **Auth for GitHub API:** **PAT** per link for MVP; **GitHub App** as the documented upgrade path (same tables; different credential column / flow).
- **No plaintext tokens in DB:** store **`token_cipher`** (Fernet-at-rest; key from **`GITHUB_TOKEN_ENCRYPTION_KEY`** or derived from **`JWT_SECRET`** — see **`.env.example`**); never return or log token values. Aligns with plan’s “no plaintext PAT in DB”; GitHub App remains the upgrade path.
- **Polling before webhooks:** default **interval** (e.g. **5 minutes**, configurable); **conditional requests** / **ETag** where possible; **backoff** on `403`/`429`.
- **Webhooks later:** reuse the same **upsert commit** pipeline the poller uses.

### I1 — Ease of integration (design principles)

1. **Single write pipeline** — All GitHub API results normalize into **`github_commits`** (cache). Optional derived **`activities`** rows for stream visibility; **do not** teach the UI to scrape GitHub directly.
2. **Stable read DTO** — Expose a small **`CommitSummary`** (and optional **`CommitDetail`**) JSON shape from **`GET /v1/.../commits`** so **any** widget (cards, tables, pickers, markdown previews) consumes one contract.
3. **Reference, don’t fork** — “Attach commit to task / comment / ticket” stores a **pointer** (`github_commit_id` or `{ owner, repo, sha }` + resolved `link_id`) in **`activities.meta_json`** and/or a dedicated **`commit_subject_refs`** table (see **I7**). Never duplicate the full message body in five places; join to cache.
4. **Project-scoped RBAC** — All link and commit routes go through existing **`require_project_access`** / mutation rules (maintainers configure links; viewers read commits).

### I2 — Linking model: multiple repositories per project (and optional component)

| Concept | Rule |
|--------|------|
| **Anchor unit** | **Primary:** `project_id` (required). **Optional:** `component_id` for finer grouping (matches plan’s `GithubLink` with nullable `component_id`). |
| **Cardinality** | **Many links per project** — each row is one GitHub repo connection. |
| **User input** | Accept **`https://github.com/owner/repo`** (or `owner/repo`); **normalize** to `owner`, `repo`. Validate with a lightweight **HEAD** or **repo metadata** call on save. |
| **Credential** | **PAT** at link create; stored as **`token_cipher`** (Fernet). Upgrade path: external secret ref / GitHub App (plan). |

**Implemented DDL (see `sql/schema_changes.sql`):** `github_links` — `id`, `project_id`, `component_id` NULL, **`owner`**, **`repo`**, **`token_cipher`** (encrypted PAT), **`poll_interval_seconds`**, `last_synced_at`, `last_seen_sha`, `created_by`, timestamps. **`github_commits`** — `github_link_id`, **`sha`**, **`message`**, author fields, **`committed_at`**, **`html_url` NOT NULL**, optional `raw_json`.

### I3 — Sync behavior: on start + periodic

| Trigger | Behavior |
|---------|----------|
| **API lifespan** | If **`github_sync_enabled`**, starts **`github_poll_loop`** (**`app/github_background.py`**): waits **`github_poll_initial_delay_seconds`**, then syncs **each link** in its own DB transaction on every **`github_poll_interval_seconds`** interval. |
| **Per-link interval** | Column **`github_links.poll_interval_seconds`** is stored for future per-link scheduling; **current** loop uses the **global** env interval only. |
| **Manual** | **`POST /v1/projects/{project_id}/github/links/{link_id}/sync`** (maintainer/owner). |

**Ingestion:** GitHub **`/repos/{owner}/{repo}/commits`** (or compare API if you branch-scope later). Upsert into **`github_commits`**; for **each new** row optionally insert **`activities`** (`kind=github_commit`, `subject_type=project`, `subject_id=project_id`, `actor_user_id=NULL` system, `meta_json` holds `{ link_id, sha, html_url, message_head }`).

### I4 — Commit cache: full history + “what to show in lists”

**Table sketch:** `github_commits` — `id`, `github_link_id`, `sha` (40 hex), `short_sha` generated or computed, `author_name`, `author_email` NULL, `message` TEXT, `committed_at`, `html_url`, `parents_json` optional, `raw_json` optional (debug / forward-compat), unique `(github_link_id, sha)`.

**List / enumerate contract (UX + API):** every row returned to the client **must** allow the user to identify:

| Field | Requirement |
|-------|----------------|
| **Which project** | Implicit from route (`project_id`) **or** explicit `project_id` + `project_key` / name in DTO when listing cross-project (e.g. admin or future global search). |
| **Which repo** | `owner`, `repo` (from link join). |
| **Commit identity** | **Full `sha`** in API payloads; UI may show **7-char** abbreviation **only alongside** access to full SHA (tooltip, copy button, or expand row). |
| **Commit message** | Return **full `message`** from cache for detail views. For **dense lists**, provide **`message_preview`** — **at least 120 characters** (meets “≥ 100 chars” ask with margin); suffix with ellipsis when truncated. **Recommendation:** 120 list / full in drawer. |
| **Verify on GitHub** | Persist GitHub’s **`html_url`** for every commit (see plan **`GithubCommit.html_url`** and “**click → diff link on GitHub**”). **Every** list row, activity card, and `github_ref` chip **must** expose it (e.g. “Open commit” / link on SHA). Developers verify **diff and files on GitHub** in the browser — **no embedded code or diff preview** in-app for MVP unless you explicitly expand scope later. |

**Pagination:** cursor-based (`sha` + `committed_at`) for “full history” browsing on **`/projects/{id}/github`** and API.

### I4.1 — Action checklist: `html_url` required + verification UX

Execute these when implementing Batch I (check off in PRs). **Goal:** any widget can render **“Open on GitHub”** with **no extra DB/API round-trip** beyond the payload it already holds.

| # | Layer | Exact action |
|---|--------|--------------|
| 1 | **`sql/schema_changes.sql`** | Add column **`html_url` TEXT NOT NULL** on **`github_commits`**. If you must allow legacy rows during rollout, use `NOT NULL` only after backfill; **never** ship new ingests without a URL. |
| 2 | **Ingest / upsert** | When mapping GitHub API commit → row, set **`html_url`** from the payload’s **`html_url`** field. **If absent** (rare), **derive** `https://github.com/{owner}/{repo}/commit/{sha}` and store that — still satisfies NOT NULL and deep-link contract. |
| 3 | **`api/app/schemas.py` (or equivalent)** | Define **`CommitSummary`** (and **`CommitDetail`** if split) with **`html_url: AnyHttpUrl | str`** **required** (no optional). Same for any **`GithubCommitOut`** used by routers. |
| 4 | **List/detail routes** | **`GET .../github/commits`** and **`GET .../github/commits/{sha}`** always **serialize `html_url`** from the row; do not omit for size — previews are already truncated separately via **`message_preview`**. |
| 5 | **`activities.meta_json` (system `github_commit`)** | On insert, always include **`html_url`** alongside `sha`, `owner`, `repo`, `link_id`, `commit_id` (see **§ I5**). |
| 6 | **`github_ref` validation (writes)** | On POST/PATCH of activities/tasks/tickets that include **`github_ref`**: require **`html_url`** **or** accept omit only if server **re-resolves** `commit_id` and **injects** `html_url` before save (prefer **require** on client for fewer round-trips). |
| 7 | **`body_md` for `github_commit` rows** | Use Markdown link target = stored **`html_url`** for the short SHA anchor (see **§ I5**). |
| 8 | **Web — GitHub table** | **SHA** cell: `<a href={html_url} target="_blank" rel="noopener noreferrer">` (abbrev label + `title` with full SHA). Add **external-link icon** consistent with design system. |
| 9 | **Web — message preview** | Make preview **also** clickable to **`html_url`** **or** add adjacent **“Open on GitHub”** control; **same** `html_url` for both (primary verification path). |
| 10 | **Web — activity card `kind=github_commit`** | Read **`meta_json.html_url`**; render **SHA + “Open on GitHub”** without fetching commit again. |
| 11 | **Web — commit chips / picker output** | When inserting a chip or markdown snippet, include **`html_url`** in the stored structure so rendered chips link out. |
| 12 | **Tests** | API contract tests: list + detail responses **assert** `html_url` matches expected `https://github.com/.../commit/...` pattern. Web smoke (optional): link `href` present in DOM fixture. |
| 13 | **Docs / OpenAPI** | Mark **`html_url`** **required** in OpenAPI schema + one example row in `/docs`. |

**Optional later (do not block MVP):** add **`parents_json`** (or first parent SHA) on **`github_commits`** and a small helper **`compare_url(parent, sha)`** → `https://github.com/{owner}/{repo}/compare/{parent}...{sha}`; **PR link** via separate integration. **Still** link-out only unless you explicitly choose embedded previews.

---

### I5 — Activity stream integration (`github_commit`)

- **Automatic stream entries** for newly discovered commits (system actor).
- **`body_md`:** short human line, e.g. ``[`abc123f`](url) **owner/repo** first line of message…`` — keeps Today / rollup readable.
- **`meta_json`:** machine-friendly `{ "link_id", "commit_id", "sha", "owner", "repo", "html_url", "message_preview" }` for widgets and SSE clients (already have `kind` in SSE hints).

### I6 — Attaching a commit to tasks, comments, and other feedback

**Goal:** user can **cite** any cached commit on a **task**, **activity comment** / **reply**, **ticket** note, or future types — without hard-wiring GitHub into every composer.

**Recommended approach (loose coupling):**

1. **`CommitReference` in `meta_json`** (MVP, fast): convention `github_ref: { "commit_id": "<uuid>", "sha": "<40>", "owner", "repo", "html_url" }` (include **`html_url`** so chips stay deep-linkable even if join is skipped). Validated on POST/PATCH: commit must belong to same `project_id` as the subject.
2. **Optional normalized table** `commit_subject_refs` (scalable): `id`, `github_commit_id`, `subject_type` (`task` / `ticket` / `activity` / …), `subject_id`, `created_by`, `created_at` — powers “all tasks referencing this commit”, watcher notifications, and deduplication. **Architecture should allow adding this table without breaking I6.1.**

**UI:** picker modal or ⌘K entry “Insert commit…” → searches **`GET /v1/projects/{id}/github/commits?q=`** → inserts markdown snippet or structured chip stored as above.

**Not required in first slice:** inline diff or **source code preview** inside tools-project; PR objects; status checks. **Verification** = **open `html_url` on GitHub** (commit page / compare as GitHub provides).

### I7 — Loose integration layer (for watchers, collaborators, developers)

| Layer | Responsibility |
|-------|----------------|
| **`GitHubSyncPort` (protocol)** | `fetch_commits_since(link, cursor) -> list[NormalizedCommit]` — swappable test fake / live httpx client. |
| **`CommitRepository` (DB)** | Upsert commits; list by project / link; resolve `sha` → row. |
| **`ActivityWriter` extension** | `write_github_commit_activity(...)` beside existing `write_activity`. |
| **`CommitSummary` DTO** | Shared JSON schema documented in OpenAPI; **must** include **`html_url`** (and `sha`, `owner`, `repo`, `message_preview`, timestamps). Imported by web types codegen or hand mirror. |

**Widgets** (non-exhaustive) should depend **only** on **`CommitSummary`** + **`github_ref` meta** — not on Octokit-specific shapes:

- Project **GitHub** tab — full history table.
- **Activity** card renderer for `kind=github_commit`.
- **Task detail** sidebar — “Linked commits”.
- **TicketDiscussion** — commit chips in thread.
- **Today** — optional “recent commits in watched projects” (later).

### I8 — API surface (extends plan §6)

Keep the plan’s routes; extend for **many links** and **history**:

```
GET    /v1/projects/{project_id}/github/links
POST   /v1/projects/{project_id}/github/links     { github_repo_url?, owner?, repo?, github_token, component_id?, poll_interval_seconds? }
DELETE /v1/projects/{project_id}/github/links/{link_id}
POST   /v1/projects/{project_id}/github/links/{link_id}/sync

GET    /v1/projects/{project_id}/github/commits   ?link_id=&limit=
```

**Not implemented yet:** `PATCH …/links/{link_id}`; `GET …/github/commits/{sha}` detail; cursor pagination (extend as needed). The `q` search param on `GET …/github/commits` **is** implemented.

### I9 — Web surface (extends plan §7) — **Done**

- **`/projects/[id]/github`** — linked repos + **paginated** commit table (columns: time, repo, SHA copy, **120+ char preview**, author).
- **Settings sub-section** — add / remove repo links (owner/repo URL + token), test connection, poll interval override per link (advanced).
- **Reuse** `Activity` feed component for auto `github_commit` rows; **separate** rich history table for “full log” browsing.

**Shipped (per I10d / HANDOFF):** `/projects/[id]/github` page + commit table, `/projects/[id]/settings` add/remove repos + PAT form, `github_commit` activity cards in `ActivityClient`.
**Still pending:** cursor pagination on the commit table (see § I8), “test connection” control, per-link `poll_interval_seconds` override in the settings form.

### I10 — Phased delivery (Batch I sub-tracks)

| Sub | Scope | Status |
|-----|-------|--------|
| **I10a** | `sql/` + models **`github_links`**, **`github_commits`** | **Done** — indexes + **`html_url` NOT NULL**; **§ I4.1** row **1**. |
| **I10b** | Link CRUD API + encrypted token | **Done** — `POST/GET/DELETE …/github/links` (no **`PATCH`** link yet). |
| **I10c** | Poller + upsert + `github_commit` activity rows | **Done** — **httpx** sync + **lifespan** background loop + manual **`POST …/sync`**; `activities` rows with `kind=github_commit` written only for **new** commits. |
| **I10d** | `GET …/github/commits` + GitHub page UI | **Done** — **API + `CommitSummary`** (`html_url` required) **done**; **Next.js** **`/projects/[id]/github`** + table UI **done**; `github_commit` activity cards render with rich SHA/repo/preview. |
| **I10e** | **`github_ref`** validation + picker | **Done** — backend validation in `activities.py`; `CommitPicker` component with search; integrated into activity composer + reply forms. |
| **I10f** | (Optional) `commit_subject_refs` + watcher hooks | **Done** — table + model + router + auto-create on activity `github_ref`. |
| **I10g** | Plan §3 polish carryovers | **Done** — optional Inbox **`c`** shortcut still deferred. |

### I11 — Acceptance (Batch I) vs **`20260515-full-project.md`** §11

| # | Plan / NEXT criterion | Status |
|--:|------------------------|--------|
| 1 | Maintainer links **≥2** repos; **no token** in API responses or logs | **Done** — **`/projects/[id]/settings`** web form; tokens **encrypted at rest**; **`GET …/links`** omits secret fields. |
| 2 | Commits visible in **activity** + **GitHub** tab within a poll cycle | **Done** — **`/projects/[id]/github`** page; `github_commit` activities in feed with rich card rendering. |
| 3 | List rows: project, repo, SHA, **≥120** char preview, **`html_url`** | **Done** — web table on GitHub tab; `CommitSummary` enforces `html_url`. |
| 4 | Attach commit to **task** / **comment** | **Done** — **`github_ref`** validation in `activities.py`; **`CommitPicker`** component with search. |
| 5 | New widgets consume **`CommitSummary`** only | **Yes** — API contract and web widgets. |

### I12 — Configure GitHub repo + PAT **today** (API / OpenAPI — no web UI yet)

There is **no** Next.js screen for URL/token yet (plan **`/projects/[id]/github`** + settings — **I10d** web). Until that ships, use **`http://localhost:8300/docs`** (tag **`github`**) or any HTTP client with a normal **Bearer JWT** (same auth as the rest of the API). **Role:** project **owner** or **maintainer** only.

**Create link + initial sync** (body uses **`GithubLinkCreate`** — either **`github_repo_url`** *or* **`owner` + `repo`**, plus **`github_token`**):

```http
POST /v1/projects/{project_id}/github/links
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "github_repo_url": "https://github.com/octocat/Hello-World",
  "github_token": "<github_pat_fine_grained_or_classic>"
}
```

Then:

```http
GET /v1/projects/{project_id}/github/commits
Authorization: Bearer <access_token>
```

**Manual re-sync:** `POST /v1/projects/{project_id}/github/links/{link_id}/sync`. **Background poll:** controlled by **`GITHUB_SYNC_ENABLED`**, **`GITHUB_POLL_INTERVAL_SECONDS`**, **`GITHUB_POLL_INITIAL_DELAY_SECONDS`**, **`GITHUB_COMMITS_PER_SYNC`** (see **`.env.example`**).

---

## Batch J — clients-participants (CRM)

**Source:** `.work/features/clients-participants/20260618-SPEC.md` (Approved) + ADR-0001.  
**Goal:** Add client companies, contacts, sales pipeline, and limited client project access.

### J0 — Decisions / prerequisites (done)

- ADR-0001 decided: separate `client_contacts` with optional `user_id`; `project_clients` join table; dedicated `project_client_access`; separate `prospects` table; individual user accounts; `/client/login`; `is_internal` visibility boundary.
- Unknowns registry updated; architecture foundation doc aligned.

### J1 — Schema + models (first slice)

Add idempotent DDL in `sql/schema_changes.sql` and SQLAlchemy models:

1. `prospects`
2. `clients` (with `slug` generation from company name)
3. `client_contacts` (includes `role` for `contact` / `contact_admin`)
4. `project_clients`
5. `project_client_access`
6. Optional V1: `client_referrals`, `client_onboarding_items`

Run `apply-ddl` twice to verify idempotency.

### J2 — Prospects API + UI

- `api/app/routers/prospects.py`: list, create, get, update, delete, `PATCH /stage` with transition validation. **Done.**
- `web/src/app/prospects/`: list page, detail page with tabs (overview, activity, referrals), stage transition widget. **Screen SPEC created (Draft)** — `.work.ui/screens/prospects-list/20260618-SCREEN-SPEC.md`. Build pending UI design foundation.

### J3 — Clients + contacts API + UI

- `api/app/routers/clients.py`: client CRUD + contacts sub-routes.
- `web/src/app/clients/`: list, detail (contacts, projects, onboarding tabs).
- Auto-create `clients` record when prospect reaches `won`.

### J4 — Project-client linking

- `api/app/routers/project_clients.py`: link/unlink clients to projects; include client summary on project GET.
- Web: client badge on project list/header; client section in project settings.

### J5 — Client access + permission resolution

- `api/app/routers/project_client_access.py`: grant/revoke/update client contact access.
- Modify `api/app/deps.py` to check `project_client_access` alongside `project_members`.
- Enforce `is_internal = false` visibility for client participants.

### J6 — Client portal

- `web/src/app/client/login/`: separate login page.
- Limited client dashboard + project view: only assigned tasks/tickets, public activity, no settings/GitHub/internal activity.

### J7 — Pipeline flags + optional polish

- `api/app/services/pipeline_flags.py`: surface follow-up / check-in / breakup / review-for-lost flags.
- Optional V1: referrals UI, onboarding checklist UI.

### J8 — Acceptance

- [ ] Client CRUD + contacts end-to-end.
- [ ] Prospect stage transitions validated.
- [ ] Project linked to client; internal team sees client summary.
- [ ] Client participant login sees only allowed projects and public activity.
- [ ] Client participant cannot view internal activity, project settings, members, or GitHub.

---

## Batch A — Schema discipline (maintain continually)

| # | Item | Why | Hints |
|---|------|-----|-------|
| A1 | **`sql/schema_changes.sql`** ↔ **`api/app/models`** | Primary DDL | `IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`. |
| A2 | **`sql/schema_indexes.sql`** | Indexes / constraints | Idempotent. |
| A3 | **`sql/schema_backfill.sql`** | Row fixes for existing DBs | Idempotent only. |
| A4 | **`sql/schema_inserts.sql`** | Seeds after bootstrap | `ON CONFLICT`; avoid random UUIDs for fixtures unless static. |

**Current tables (non-exhaustive):** `users`, `projects`, `project_members`, `components`, `tasks`, `activities`, `mentions`, `tickets`, **`attachments`**, **`project_counters`**, **`inbox_items`**, **`watchers`**, **`github_links`**, **`github_commits`**.  
**Still planned (optional):** **`commit_subject_refs`** for normalized cross-links + **`github_commit`** activity rows (API sync today only writes **`github_commits`** + link metadata).

---

## Completed batches (reference — do not reopen unless regressing)

| Batch | Scope | Status |
|-------|--------|--------|
| **B** | Project members, RBAC, PATCH project, web members/settings | **Done** |
| **C** | Components API + UI | **Done** |
| **D** | Tasks: API transitions, filters, **table** UI, **`ref`** via counters | **Done** (Kanban = **G1**) |
| **E** | Admin user forms, auth docs | **Done** |
| **F** | Activities, mentions, tickets queue API, **`/today`** | **Done** + **ticket case**, **attachments**, queue ordering |
| **G** | Phase 1 parity: Kanban, task detail, ⌘K, project health | **Done** (see matrix) |
| **H** | Inbox, watches, SSE payload, task activity, markdown editor | **Done** (see matrix) |
| **I** | GitHub & polish | **Done** — see **§ Batch I** |

---

## Quick verification commands (Docker)

```bash
docker compose --profile dev up --build
docker compose --profile dev run --rm api python -m app.cli_schema apply-ddl   # DDL → bootstrap → backfill/inserts
curl -s "http://localhost:8300/docs"   # GitHub routes under tag `github`
docker compose --profile dev run --rm --no-deps web sh -lc "npm ci --no-audit --no-fund && npm run check && npm run build"
```

---

## Current iteration — M7: Outbound event dispatcher

**Milestone ref:** M7 · Feature SPEC: `.work/features/outbound-event-dispatcher/20260706-SPEC.md`
**Status:** complete
**Started:** 2026-07-06

### Tasks
| ID | Description | Files | Status | Notes |
|----|-------------|-------|--------|-------|
| M7-T1 | webhook_subscriptions table + model | `sql/schema_changes.sql`, `api/app/models/webhook_subscription.py` | done | DDL + SQLAlchemy model |
| M7-T2 | webhook_dispatcher service | `api/app/services/webhook_dispatcher.py` | done | dispatch_event with retry + HMAC signing |
| M7-T3 | admin CRUD router | `api/app/routers/admin_webhooks.py` | done | POST/GET/DELETE with superuser guard |
| M7-T4 | Wire into event-producing routes | `prospects.py`, `clients.py`, `tasks.py`, `tickets.py` | done | prospect.stage_changed/won, client.created, task.done, ticket.created/closed |
| M7-T5 | Register router + gate | `api/app/main.py` | done | compileall pass, 38 routes |

### Done this iteration
| Task | Completed | Notes |
|------|-----------|-------|
| M7-T1 | 2026-07-06 | webhook_subscriptions DDL + model |
| M7-T2 | 2026-07-06 | webhook_dispatcher with retry |
| M7-T3 | 2026-07-06 | admin webhook CRUD router |
| M7-T4 | 2026-07-06 | Wiring in 4 routers |
| M7-T5 | 2026-07-06 | Gate: compileall pass, 38 routes |

---

## Current iteration — M8: Cross-app external refs

**Milestone ref:** M8 · Feature SPEC: `.work/features/cross-app-refs/20260706-SPEC.md`
**Status:** complete
**Started:** 2026-07-06

### Tasks
| ID | Description | Files | Status | Notes |
|----|-------------|-------|--------|-------|
| M8-T1 | Schema: add source_app, external_url, label to commit_subject_refs | `sql/schema_changes.sql`, `sql/schema_indexes.sql` | done | ALTER TABLE + index |
| M8-T2 | Extend CommitSubjectRef model | `api/app/models/commit_subject_ref.py` | done | New columns |
| M8-T3 | External refs CRUD router | `api/app/routers/external_refs.py` | done | POST/GET/DELETE per project |
| M8-T4 | Register router + gate | `api/app/main.py` | done | compileall pass, 38 routes |

### Done this iteration
| Task | Completed | Notes |
|------|-----------|-------|
| M8-T1 | 2026-07-06 | Schema migration + index |
| M8-T2 | 2026-07-06 | CommitSubjectRef extension |
| M8-T3 | 2026-07-06 | external_refs router |
| M8-T4 | 2026-07-06 | Gate: compileall pass, 38 routes |

---

## Current iteration — M6: Platform whoami endpoint

**Milestone ref:** M6 · Feature SPEC: `.work/features/platform-whoami/20260706-SPEC.md`
**Status:** complete
**Started:** 2026-07-06
**HANDOFF waiver:** This feature is outside the original M1-M4 plan. Approved SPEC exists; implementing as an additive extension.

### In scope
- Schemas: `WhoamiUser`, `WhoamiCompany`, `WhoamiResponse`
- Router `GET /v1/platform/whoami` reusing `require_agent_or_user` auth
- Lookup `client_contacts` by `user_id`, join `clients` for name
- Register router in `main.py`

### Out of scope (explicit)
- Full OAuth2 Authorization Server
- User registration or signup
- Rate limiting specific to this endpoint

### Tasks
| ID | Description | Files | Status | Notes |
|----|-------------|-------|--------|-------|
| M6-T1 | Add whoami schemas | `api/app/schemas.py` | done 2026-07-06 | `WhoamiUser`, `WhoamiCompany`, `WhoamiResponse` |
| M6-T2 | Create platform router | `api/app/routers/platform.py` | done 2026-07-06 | `GET /v1/platform/whoami` |
| M6-T3 | Register router in main.py | `api/app/main.py` | done 2026-07-06 | Import + `include_router` |
| M6-T4 | Task gate — compile, verify | — | done 2026-07-06 | `compileall` pass, app loads 36 routes |

### Acceptance criteria
- [ ] `GET /v1/platform/whoami` returns user + companies with valid auth
- [ ] Unauthenticated returns 401
- [ ] Compileall pass

### Validation steps
- [ ] `docker compose --profile dev run --rm --no-deps api python -m compileall -q app`

### Owner blockers
- none

### Concept / NFR registry (this iteration)
| Concept id | Applies | Status | Evidence / trigger |
|------------|---------|--------|-------------------|
| MOD-01 | no | n/a | Single bounded context (API) |
| MOD-02 | no | n/a | No AI-assisted PR |
| MOD-03 | no | n/a | No cost-sensitive decisions |
| MOD-04 | no | n/a | No distributed-system concerns |
| MOD-05 | no | n/a | No compliance surface |
| MOD-06 | yes | done 2026-07-06 | 0 boundaries, no new deps, read-only query — merge_ok |
| MOD-07 | no | n/a | No ops-load impact |

### Cross-LLM verification
- Triggered: no

### Done this iteration
| Task | Completed | Notes |
|------|-----------|-------|
| M6-T1 | 2026-07-06 | WhoamiUser, WhoamiCompany, WhoamiResponse schemas |
| M6-T2 | 2026-07-06 | platform router: GET /v1/platform/whoami |
| M6-T3 | 2026-07-06 | Router registered in main.py |
| M6-T4 | 2026-07-06 | Gate: compileall pass, app imports (36 routes) |

---

## Current iteration — M5: RFP award webhook receiver

**Milestone ref:** M5 · Feature SPEC: `.work/features/rfp-award-webhook/20260706-SPEC.md`
**Status:** complete
**Started:** 2026-07-06
**HANDOFF waiver:** This feature is outside the original M1-M4 plan. Approved SPEC exists; implementing as an additive extension.

### In scope
- `rfp_webhook_secret` config setting in `Settings`
- In-memory idempotency store with 24h TTL
- HMAC-SHA256 signature verification dependency
- Schemas: `RfpAwardPayload`, `RfpAwardResponse`
- New router `POST /v1/integrations/rfp/award` — accepts webhook, resolves/creates prospect, transitions to won, runs promotion pipeline
- Register router in `main.py`

### Out of scope (explicit)
- `integration_secrets` DB table (single env var for V1)
- DB-backed idempotency (in-memory for MVP)
- Outbound webhook dispatcher (Modification 1 — separate feature)
- Cross-app reference table (Modification 3 — separate feature)
- Web UI for webhook configuration
- Tests (unit/integration — added as follow-up after manual verification)

### Tasks
| ID | Description | Files | Status | Notes |
|----|-------------|-------|--------|-------|
| M5-T1 | Add `rfp_webhook_secret` to config + in-memory idempotency store | `api/app/config.py` | done 2026-07-06 | Single env var; dict-based idempotency with expiry |
| M5-T2 | Add schemas for RFP award payload and response | `api/app/schemas.py` | done 2026-07-06 | `RfpAwardPayload`, `RfpAwardResponse` |
| M5-T3 | Create HMAC signature verification dependency | `api/app/deps.py` | done 2026-07-06 | `verify_webhook_signature` |
| M5-T4 | Create `integrations` router with `POST /v1/integrations/rfp/award` | `api/app/routers/integrations.py` | done 2026-07-06 | Resolve/create prospect, call `pipeline_service`, return client+project |
| M5-T5 | Register router in `main.py` | `api/app/main.py` | done 2026-07-06 | Import + `include_router` |
| M5-T6 | Task gate — compile, verify | — | done 2026-07-06 | `compileall` pass, app loads 35 routes |

### Acceptance criteria
- [ ] `POST /v1/integrations/rfp/award` with valid HMAC signature returns 201 with client + project
- [ ] Invalid signature returns 401
- [ ] Missing required fields returns 422
- [ ] Idempotency key prevents duplicate processing
- [ ] Same email reuses existing prospect/contact
- [ ] Compileall pass

### Validation steps
- [ ] `docker compose --profile dev run --rm --no-deps api python -m compileall -q app`

### Owner blockers
- none

### Concept / NFR registry (this iteration)
| Concept id | Applies | Status | Evidence / trigger |
|------------|---------|--------|-------------------|
| MOD-01 | no | n/a | Single bounded context (API) — no cross-boundary coupling |
| MOD-02 | no | n/a | No AI-assisted PR |
| MOD-03 | no | n/a | No cost-sensitive decisions — tiny endpoint |
| MOD-04 | no | n/a | No distributed-system concerns |
| MOD-05 | no | n/a | No compliance surface |
| MOD-06 | yes | done 2026-07-06 | Agent-assisted code — run. Output: 0 boundaries, no new cross-boundary deps, test isolation missing. Recommendation: merge_with_conditions — add tests before production traffic |
| MOD-07 | no | n/a | No ops-load impact |

### Cross-LLM verification
- Triggered: no

### Done this iteration
| Task | Completed | Notes |
|------|-----------|-------|
| M5-T1 | 2026-07-06 | rfp_webhook_secret config + in-memory idempotency store |
| M5-T2 | 2026-07-06 | RfpAwardPayload + RfpAwardResponse schemas |
| M5-T3 | 2026-07-06 | verify_webhook_signature HMAC dependency |
| M5-T4 | 2026-07-06 | integrations router: POST /v1/integrations/rfp/award |
| M5-T5 | 2026-07-06 | Router registered in main.py |
| M5-T6 | 2026-07-06 | Gate: compileall pass, app imports (35 routes) |

---

*Update this file when a batch completes; keep **HANDOFF** snapshot in sync. Batch I detail lives in **§ Batch I** above. Paths moved: old `.ai/context/*` → `.work/context/`, `.ai/plans/*` → `.work/plans/legacy-plans/`, `.ai/context/NEXT.md` → `.work/plans/NEXT.md`.*

---

## Current iteration — Multi-tenancy verification & repair

**Milestone ref:** Multi-tenancy · Feature SPEC: `.work/features/multi-tenancy/20260706-SPEC.md`
**Status:** complete
**Started:** 2026-07-07

### Tasks
| ID | Description | Files | Status | Notes |
|----|-------------|-------|--------|-------|
| MT-T1 | Fix `admin_users.py` SyntaxError and lint issues | `api/app/routers/admin_users.py` | done | `request: Request` ordering, unused variable |
| MT-T2 | Tenant-scope slug uniqueness | `api/app/routers/clients.py`, `api/app/routers/projects.py`, `api/app/services/pipeline_service.py` | done | Unique per `(slug, tenant_id)` |
| MT-T3 | Webhook tenant isolation | `api/app/services/webhook_dispatcher.py`, `api/app/routers/admin_webhooks.py` | done | Filter by tenant_id; payload includes tenant context |
| MT-T4 | Cross-tenant superuser guards | `api/app/routers/me_api_keys.py`, `api/app/routers/admin_webhooks.py` | done | Reject key creation; require tenant on create |
| MT-T5 | RFP-award tenant assignment | `api/app/routers/integrations.py` | done | Prefer tenant-scoped system user; default tenant fallback |
| MT-T6 | Test/DDL compatibility | `api/tests/factories.py`, `api/tests/conftest.py`, `api/tests/test_webhook_dispatcher.py` | done | Factories default to default tenant; fixture fixed |
| MT-T7 | Full verification gate | — | done | ruff pass, pyright 0 errors, compileall pass, DDL idempotent, pytest 33 pass |

### Done this iteration
| Task | Completed | Notes |
|------|-----------|-------|
| MT-T1 | 2026-07-07 | admin_users.py syntax + lint fixes |
| MT-T2 | 2026-07-07 | Per-tenant slug uniqueness across clients/projects |
| MT-T3 | 2026-07-07 | Webhook dispatcher tenant-scoped delivery |
| MT-T4 | 2026-07-07 | Cross-tenant superuser guardrails |
| MT-T5 | 2026-07-07 | RFP-award uses tenant-scoped system actor |
| MT-T6 | 2026-07-07 | Test suite compatible with mandatory tenant columns |
| MT-T7 | 2026-07-07 | All gates green |

### Acceptance criteria
- [x] `ruff check .` passes
- [x] `pyright .` passes (0 errors, 0 warnings)
- [x] `python -m compileall -q app` passes
- [x] `python -m app.cli_schema apply-ddl` is idempotent (ran twice)
- [x] `pytest tests/` passes (33/33)

### Owner blockers
- none

### Next recommended
- Mark multi-tenancy SPEC as Approved.
- Add HTTP-level cross-tenant leak tests for all tenant-scoped routers.
