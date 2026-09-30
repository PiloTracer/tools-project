# Plan-sync — importing plans into the project system

**Status:** Final v2.0 — architecture locked, **pending sign-off on D9–D11** (D1–D8 approved 2026-09-29)
**Version:** 2.0 · **Created:** 2026-09-29 · **Revised:** 2026-09-29 (verification pass + migration guarantee + obsolete handling + MOD-01 audit)
**Feature name:** Sync-from-plans (`plan-sync`)
**Source reference material (owner-designated):** `.work/feedback/plans-import/` (foundation ×4, full plan ×2)
**Next gate after sign-off:** `@feature-spec create - plan-sync` (SPEC must carry §15 Concept/NFR registry, MOD-01…MOD-08) → implementation

---

## 1. Executive summary

**What we want.** Drop a project plan (the markdown produced by the Agent OS planning chain) into `.work/feedback/plans-import/`, run a sync, and the project system builds a real project out of it: the right **milestones**, the right **tasks under each milestone**, in order, each task carrying its own definition of done. Then the team executes the plan milestone by milestone inside the app instead of inside a markdown file. Re-running the sync after a plan revision must reconcile cleanly — **including tasks the new plan makes obsolete**.

**The problem.** The app has **no concept of milestone, stage, phase, sprint, epic or iteration** — verified zero matches in `sql/` and `api/app/models/`. It has **no bulk-create endpoint**, so loading 153 tasks today means 153 API calls, each writing an activity row and firing a background GitHub request. The feature is not "an import button" — it is the missing *sequence* dimension of the data model.

**The architecture (locked):**

1. **First-class `milestones` table** + `tasks.milestone_id` + stable `plan_ref` on both. Reusing `components` or parent-tasks was rejected — wrong meaning, and rework later costs more than building it once (§5).
2. **Stage and iteration are the same entity.** Iteration = the milestone with status `active`. One table, three vocabularies.
3. **Two new provenance columns** — `plan_state` (`active | obsolete`) on tasks *and* milestones — so "the plan dropped this work" is distinguishable from "a human cancelled this work", and re-sync can resurrect it safely (§11, decision **D9**).
4. **Two-half import**: an agent skill parses the living, prose-heavy plan into a validated JSON manifest; a transactional API endpoint ingests it atomically and idempotently. No markdown parser in application code (§7).
5. **Migrations use the repo's existing restart runner.** DDL is appended idempotently to `sql/schema_changes.sql` / `sql/schema_indexes.sql`, which the API lifespan executes **on every container start** (`main.py:56-63`). No new migration files, no manual step, no ORM migrations — this satisfies the requirement that migrations "seamlessly and idempotently execute on restart" out of the box (§9.3, decision **D10**).
6. **Obsolete handling is explicit and status-aware**: removed-not-started → `cancelled` + `obsolete`; removed-in-progress → **conflict, never auto-killed**; removed-but-done → stays `done`, flagged obsolete; reappearing later → reactivated (§11.3, decision **D11**).

**Cost.** Four phases (schema+API / agent skill / UI / polish), all additive and idempotent. Two deliberate small decouplings are required (§13). Coupling audit **MOD-01: score `low`, `proceed_with_guards`** (Appendix C).

**Decision requested:** sign off **D9–D11** (below). D1–D8 are already approved.

---

## 2. Goal and success criteria

| # | Goal | Success measure |
|---|------|-----------------|
| G1 | A plan folder becomes a runnable project | One sync of `.work/feedback/plans-import/` produces 1 project, 12 milestones, 153 tasks — correct ordering and parentage |
| G2 | Structure is first-class, not text | Milestones filterable, ordered, with server-side progress roll-up |
| G3 | Sync is repeatable | Sync twice on unchanged plan = no-op; on amended plan = reported diff, no duplicates, no regressions |
| G4 | Sync is cheap to maintain | No markdown grammar parser in app code; plan-format drift costs a skill edit only |
| G5 | Existing projects unaffected | New columns/tables nullable or defaulted; migration idempotent |
| G6 | **Migration is restart-safe** | DDL applied automatically on API container start by the existing runner; verified by running the schema twice against a dev DB |
| G7 | **Obsolescence is handled** | A task dropped by a revised plan is marked obsolete per §11.3 matrix, reported in the sync diff, never silently deleted, never silently resurrected |

---

## 3. What the input actually looks like (evidence — measured)

Against `.work/feedback/plans-import/plans/20260925-full-plan.md`:

| Property | Value |
|----------|-------|
| Plan size | 953 lines, 25 H2 sections + 3 appendices |
| Milestones | **12** (M1…M12), each with Objective / Scope / Dependencies / Deliverables / Complexity / Testing / Acceptance / Validation / Rollback |
| Tasks | **153** rows, **153** unique IDs, format `M{N}-T{N}` |
| Task columns | `ID · Description · Files · FR/NFR · Complexity · Acceptance · Status` |
| Longest task description cell | **1463 chars** (M5-T15); next 1238, 1185 — vs `tasks.title VARCHAR(500)` |
| Version churn | v1.1 → v1.7 plus a correction pass — **plans are amended after approval** |
| ID guarantee | Appendix A `D20`: *"ids appended, never renumbered"* — this is the re-sync match key |

**Consequences:** (1) titles must be agent-authored short text with full body preserved; (2) import must be an *upsert with a diff*, or every plan revision duplicates the project; (3) a regex markdown parser would break on the next amendment — the strongest argument for the split in §7.

---

## 4. What the system can hold today (evidence)

| Capability | Status | Evidence |
|-----------|--------|----------|
| Milestone / stage / iteration / sprint / epic | **Absent** | `grep -riE "milestone\|sprint\|epic\|iteration\|phase" sql/ api/app/models/` → **no matches** |
| Task status vocabulary | `{todo, in_progress, blocked, done, cancelled}` — terminal = `{done, cancelled}` sets `closed_at` | `api/app/schemas.py:12`, `api/app/routers/tasks.py:49,139` |
| Status vocabulary parity in UI | Complete: 5 columns, 5 editor options, 5 select options | `web/src/components/KanbanBoard.tsx:17-23`, `TaskDetailEditor.tsx:12`, `TasksClient.tsx:89-93` |
| Grouping on a task | `component_id`, `parent_task_id` (one level), `status`, `priority` | `sql/schema_changes.sql:62,71` |
| Task list filter by parent | **Not supported** — only `component_id` is filterable | `api/app/routers/tasks.py:85-86` |
| `parent_task_id` in UI | Type-only, never rendered or edited | `web/src/app/projects/[id]/tasks/[taskId]/page.tsx:30` |
| Bulk **create** endpoint | **None** — only update-batch (`tasks.py:351`, `tickets.py:300`, `ids` + field updates) | all `.post(` routes enumerated across `api/app/routers/*.py` |
| Batch cap | 100 rows | `api/app/schemas.py:516-521` |
| Per-create side effects | 1 ref allocation + 1 activity row + fire-and-forget GitHub push (no webhook on create) | `api/app/routers/tasks.py:137-169` |
| Refs require `project_key` + `auto_prefix_enabled` | Yes | `api/app/services/ref_alloc.py:44-46` |
| Enabling `auto_prefix_enabled` | **Requires linked GitHub repo + live token round-trip** | `api/app/routers/projects.py:257-300` |
| Writes | JWT only (`get_current_user`, `deps.py:122`); personal/agent `X-Api-Key` accepted only by `require_agent_or_user` (`deps.py:181`), used exclusively by GET-only `agent_query.py` / `platform.py` | grep of router imports |
| Board grouping | Status columns only | `KanbanBoard.tsx:17-23` |
| Test suite | **Exists**: `api/tests/` (conftest, factories, 8+ suites), pytest configured (`testpaths=["tests"]`) | `api/pyproject.toml:64-66` |

**Reading of the gap:** the app models *work* and *state* well but has no *sequence* dimension. A plan is fundamentally a sequence. That mismatch is what this feature closes.

---

## 5. Options — milestone / stage / iteration architecture

| # | Option | Cost | Effective? | Efficient? | Best? | Verdict |
|---|--------|------|-----------|-----------|-------|---------|
| A | Reuse `components` as milestones | ~Zero backend | Poor — no status/order/gate; `components` means *module*, and plans also need components for BC1…BC14 → **collision** | Poor — free now, rework later | No | **Rejected** |
| B | Reuse `parent_task_id` | ~Zero backend | Poor — not filterable, never rendered, milestone becomes a Kanban card | Poor — needs UI work anyway | No | **Rejected** |
| C | Encode in text (title/ref prefix) | ~Zero | None — no grouping, no roll-up, no re-sync | Worst | No | **Rejected** |
| **D** | **First-class `milestones` table** + `tasks.milestone_id` + `plan_ref` | Medium, one-time | Strong — ordered, own status/gate/roll-up, filterable, re-syncable | Strong — pays for itself on project 2 | **Yes** | **Recommended** |
| E | Polymorphic `task_groups(kind=…)` | Medium+ | Flexible but speculative | Weaker — extra dispatch for a need not yet shown | No | **Rejected for v1** |

**D1 (approved): Option D.** **D2 (approved):** stage/iteration collapse — *iteration := milestone with status `active`*; milestone vocabulary `pending | active | blocked | done | cancelled`. No `stages`/`iterations` tables. Non-goal: `parent_milestone_id` nesting — re-open only if a plan genuinely needs two sequencing levels.

---

## 6. Recommended architecture (target model)

```text
project  (existing)
  ├── component            (existing — reserved for bounded contexts / modules)
  ├── milestone            (NEW — the sequence dimension)
  │     id, project_id, key 'M1', name, summary, description,
  │     status, plan_state, sort_order, start_at, due_at, plan_ref
  └── task                 (existing + 3 columns)
        + milestone_id  → milestones.id   (nullable, SET NULL)
        + plan_ref      'M4-T4'           (nullable, unique per project)
        + plan_state    'active'          (NOT NULL DEFAULT 'active')
```

| Dimension | Answers | Represented by |
|-----------|---------|----------------|
| **When / in what order** | What do we do next? | `milestones` (NEW) |
| **Where in the system** | Which module? | `components` (existing; BC1…BC14 mapping is optional, P4) |
| **What is the work** | What must be true when done? | `tasks` (+ `parent_task_id` for genuine sub-tasks) |
| **Where did it come from** | Plan-synced or manual? Alive or dropped by a revision? | `plan_ref` + `plan_state` (NEW) |

Mapping the sample plan:

| Plan concept | Target | Rule |
|--------------|--------|------|
| Project "Mendarion" | `projects` row | name/slug/key/description from plan header (project created via existing `POST /v1/projects`, then imported — keeps one sanctioned creation path) |
| Milestone `M1…M12` | `milestones` row | `key`, `sort_order`, block → `description` |
| Milestone Objective/Gate/Rollback | `milestones.description` | verbatim markdown |
| `BC1…BC14` annotations | `components` | optional, P4, only when a milestone names exactly one BC |
| Task `M1-T5` | `tasks` row | `plan_ref`, agent-written short `title`, full text → `description` |
| Task `Acceptance` cell | top of `tasks.description` | it is the contract |
| Task `Complexity` / `FR/NFR` | `tasks.description` text | **not** mapped to `priority` (complexity ≠ urgency) |
| Task plan `Status` | `status` | `pending→todo`, `done→done`, `blocked→blocked`, `deferred→cancelled` |
| Risk/unknown/assumption/decision registries | **not imported** | stay in `.work/` (§17) |

---

## 7. Import pipeline (D3, approved)

| # | Approach | Verdict |
|---|----------|---------|
| P | Client loops `POST /tasks` ×153 | **Rejected** — no atomicity (failure at #90 orphans 89 rows), side-effect storm, cannot create milestones |
| Q | Deterministic markdown parser in Python | **Rejected** — brittle against v1.x amendments and 1463-char cells; silent mis-parses |
| R | Direct SQL/ORM seed | **Rejected** — bypasses RBAC/refs/activity; DB writes need explicit human approval |
| **S** | **Agent parses → JSON manifest → transactional API ingest** | **Chosen** — semantic work done by the thing that already reads these plans; app does the deterministic part |

**Half 1 — agent skill `@plan-sync`** (framework side, outside this repo): read `.work/feedback/plans-import/**` → extract manifest → validate against published schema (counts, ID format, title ≤200, uniqueness) → render preview (created/updated/obsolete/conflicts) → on confirmation POST → report result.

**Half 2 — `POST /v1/projects/{project_id}/plan-import`:** pydantic manifest schema → `dry_run` support → **one transaction** for all milestones + tasks → suppressed side effects (§13) → returns `{created, updated, obsolete, reactivated, conflicts}`.

**Manifest envelope (protocol detail added in v2.0):** `manifest_version`, `source_path`, `plan_version` (e.g. `v1.7`), `project` block, `milestones[]`, `tasks[]`, optional `components[]`. Version field lets the API reject unknown future formats fast instead of half-applying them.

---

## 8. Architectural redirection (final)

### 8.1 Layers and the single sanctioned path

```text
  .work/feedback/plans-import/*.md          (plan source of truth — never written by sync)
            │
            │  @plan-sync skill (framework)  — parse, validate, preview, confirm
            ▼
  JSON manifest  ──POST /v1/projects/{id}/plan-import──►
            │                                            (auth: X-Api-Key or JWT + project RBAC)
            ▼
  api/app/services/plan_import.py           — THE only bulk write path; one transaction
       │        │            │
       ▼        ▼            ▼
  milestones  tasks      ref_alloc        (activity: ONE summary row; GitHub push: ONE deferred call)
       │
       ▼
  sql/schema_changes.sql + schema_indexes.sql  — executed by lifespan on every API restart
```

**Rules that keep this solid:**
- **Single-writer discipline per concern:** single-row CRUD stays in `routers/tasks.py`; *only* `services/plan_import.py` writes in bulk. Both go through the same SQLAlchemy models — no raw SQL from Python, no second persistence path.
- **The plan file stays authoritative for content; the app stays authoritative for execution state.** Sync never writes back to `.work/` (one-way flow), and plan revisions never overwrite local `status` (§11).
- **No new deployable, no new network hop, no new background service** — MOD-02/03/04/05 do not apply.

### 8.2 File touch-map (what implementation will add/change)

| Layer | File | Change |
|-------|------|--------|
| SQL | `sql/schema_changes.sql` | append `CREATE TABLE milestones` + 3 `ADD COLUMN IF NOT EXISTS` — **all idempotent** |
| SQL | `sql/schema_indexes.sql` | append 6 partial/ordinary indexes, `IF NOT EXISTS` |
| Model | `api/app/models/milestone.py` | new |
| Model | `api/app/models/__init__.py` | import + `__all__` entry (registration is explicit, verified) |
| Model | `api/app/models/task.py` | 3 columns |
| Schemas | `api/app/schemas.py` | `MilestoneCreate/Out`, `PlanImportManifest/Result`, `TaskOut` + fields, list-filter params |
| Service | `api/app/services/plan_import.py` | new — validate, upsert, reconcile, report |
| Router | `api/app/routers/milestones.py` | new — list/create/patch + import endpoint |
| Router | `api/app/main.py` | import block + 2 `app.include_router(...)` lines (registration is an explicit list, verified `main.py:118-151`) |
| Auth | `api/app/routers/projects.py:257` | split prefix/registry gating (D6) |
| Auth | import route only | accept `X-Api-Key` via `require_agent_or_user` (D7) |
| Web | tasks page, board, project page | milestone filter/column, chip row, milestone list, obsolete badge/filter (§14) |
| Framework | `.ai` skill `plan-sync` | new skill (outside this repo) |

### 8.3 MOD-01 coupling audit (run for this change)

See **Appendix C** for the full audit output. Summary: boundaries crossed **4** (api layers, sql, web, framework skill), shared persistence = `tasks` table with a documented single-writer split, **coupling score: `low`** (`measured`), **human architectural review: `required`** — which is exactly this sign-off. Recommendation: `proceed_with_guards`.

**MOD-06 (ai-amplification) is required** at implementation time — every line of this feature is agent-authored; re-run the prompt per implementation slice and attach to PR/iteration notes. MOD-02…MOD-05, MOD-07, MOD-08: not applicable (reasons in the Appendix C registry; copy into SPEC §15).

---

## 9. Data model and migrations

### 9.1 DDL (appended to existing files)

```sql
-- sql/schema_changes.sql  (idempotent — re-runs on every container start)
CREATE TABLE IF NOT EXISTS milestones (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    key         VARCHAR(32),
    name        VARCHAR(200) NOT NULL,
    summary     TEXT,
    description TEXT,
    status      VARCHAR(40) NOT NULL DEFAULT 'pending',
    plan_state  VARCHAR(16) NOT NULL DEFAULT 'active',
    sort_order  INT NOT NULL DEFAULT 0,
    start_at    TIMESTAMPTZ,
    due_at      TIMESTAMPTZ,
    plan_ref    VARCHAR(64),
    created_by  UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS milestone_id UUID REFERENCES milestones (id) ON DELETE SET NULL;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS plan_ref      VARCHAR(64);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS plan_state    VARCHAR(16) NOT NULL DEFAULT 'active';
```

```sql
-- sql/schema_indexes.sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_milestones_project_key ON milestones (project_id, key)      WHERE key IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_milestones_project_ref ON milestones (project_id, plan_ref) WHERE plan_ref IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_tasks_project_plan_ref ON tasks       (project_id, plan_ref) WHERE plan_ref IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_milestones_project_status     ON milestones (project_id, status);
CREATE INDEX IF NOT EXISTS ix_milestones_project_sort       ON milestones (project_id, sort_order);
CREATE INDEX IF NOT EXISTS ix_tasks_project_milestone       ON tasks       (project_id, milestone_id);
CREATE INDEX IF NOT EXISTS ix_tasks_project_plan_state      ON tasks       (project_id, plan_state);
```

`UNIQUE (project_id, plan_ref)` makes G3 enforceable **by the database**. `sort_order` is required because `key` sorts as text (`M1, M10, M11, M12, M2…` is wrong). All three task columns are nullable/defaulted → every existing row untouched.

### 9.2 ORM

Column definitions added to `Task` and the new `Milestone` model must mirror the SQL exactly (repo convention: SQL is applied by the runner; models are the mapping). Partial unique indexes stay declared in `schema_indexes.sql`, not in the model — matching the existing `commit_subject_ref.py:25` pattern.

### 9.3 Migration & restart mechanism (requirement: seamless + idempotent on container restart)

**Verified mechanism** — no new tooling needed, the repo already has exactly this:

```text
API container start (FastAPI lifespan, main.py:56-63)
  ├─ init_db()          → run_pre_bootstrap  → schema_changes.sql + schema_indexes.sql   (DB, db.py:43-49)
  ├─ run_bootstrap()    → seeds/reference data
  └─ run_post_bootstrap → schema_backfill.sql + schema_inserts.sql                      (main.py:62-63)
```

Facts (all `measured` from source):
- Runs on **every API restart**, gated by `sql_schema_apply` which defaults **True** (`config.py:40`).
- Files are split by phase and executed in a fixed order (`schema_sql.py:18-25`); each statement is executed individually via `sqlparse` (`schema_sql.py:66-88`).
- The inventory of `schema_*.sql` is asserted against a fixed list (`schema_sql.py:40-52`) — **adding a new numbered migration file would violate it**.
- Docker resolves `sql/` via `SQL_SCHEMA_DIR` or the mounted `./sql` (`schema_sql.py:55-63`).

**Therefore, D10 (decision):**
1. DDL goes **only** into `sql/schema_changes.sql` and `sql/schema_indexes.sql` — the phases the lifespan already runs pre-bootstrap.
2. Every statement must be idempotent (`IF NOT EXISTS`, guarded `ADD COLUMN`, `CREATE … IF NOT EXISTS`) because it re-executes on **every** restart. This is already the file-wide convention.
3. **No new migration files, no Alembic, no manual step, no seed data required for this feature.**
4. Verification: apply twice in a dev DB (restart the API container twice) and confirm zero errors + no duplicate objects — part of the P1 gate (§15).

---

## 10. API surface

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| `GET` | `/v1/projects/{id}/milestones` | Ordered list | project access |
| `POST` | `/v1/projects/{id}/milestones` | Create one (manual path stays sanctioned) | contributor+ |
| `PATCH` | `/v1/milestones/{id}` | Edit / transition | contributor+ |
| `POST` | `/v1/projects/{id}/plan-import` | **Bulk upsert** from manifest; `dry_run` supported | **D7:** `X-Api-Key` or JWT + project RBAC |
| `GET` | `/v1/projects/{id}/tasks?milestone_id=&plan_state=` | New filters beside `component_id` | project access |

`TaskOut` gains `milestone_id`, `plan_ref`, `plan_state`. No generic bulk-create API — the import endpoint exists because a plan is a document.

---

## 11. Re-sync and obsolete handling (strengthened — D4/D9/D11)

Plans are amended after approval (the reference was amended six times). This section is the contract for what a revision does to existing work.

### 11.1 Match key
`plan_ref` (`M4-T4`), unique per project — guaranteed stable by the source plan's own `D20` rule. Milestones match on `plan_ref` too (`M4`).

### 11.2 Provenance: `plan_state` (D9)

Two orthogonal facts, kept separate:

| Field | Answers | Values |
|-------|---------|--------|
| `status` | *workflow state* — what a human did with this work | `todo / in_progress / blocked / done / cancelled` (existing vocab, UI already supports all five) |
| `plan_state` | *provenance* — does the current plan still call for this work? | `active / obsolete` (new) |

**Why not an `obsolete` status value instead:** status is user-workflow semantics; obsolescence is plan-provenance semantics. Overloading status would (a) require touching `TASK_STATUSES` (`schemas.py:12`), Kanban columns (`KanbanBoard.tsx:17-23`), the editor (`TaskDetailEditor.tsx:12`) and every select in `TasksClient.tsx` — churn with no benefit; (b) make "user cancelled it" indistinguishable from "the plan dropped it", which the diff report and reactivation logic both need. `plan_state` is one defaulted column on each of two tables.

### 11.3 The obsolete action matrix (D11)

When a task exists locally (`plan_state=active`) but is **absent from the new manifest**:

| Local `status` | Action on commit | Rationale |
|----------------|------------------|-----------|
| `todo`, `blocked` | → `status='cancelled'`, `plan_state='obsolete'` | Never started, plan no longer wants it. `cancelled` is already terminal + renders in all UI surfaces; `closed_at` set per existing terminal handling |
| `in_progress` | **No automatic change** → reported as `conflict` | Work is under way — sync must not silently kill it. Operator resolves in the review step: keep (stays `active`) or explicitly mark obsolete (then apply row above) |
| `done` | `status` stays `done`, `plan_state='obsolete'` | Finished work is historical fact; flagging provenance is enough |
| `cancelled` | `plan_state='obsolete'` only | Already terminal; record provenance |

**Milestones dropped from the manifest:** same logic with the milestone vocabulary — `done` stays `done` + `plan_state='obsolete'`; otherwise → `status='cancelled'` + `plan_state='obsolete'`. Tasks hanging off it keep their own matrix result.

**Reactivation (task or milestone reappears in a later plan):** `plan_state='active'`; if sync previously cancelled it (`status='cancelled'` while obsolete), restore `status='todo'`. Human-set `cancelled` on an `active` task is never touched by sync.

**Never deleted** — repo rule: no deletion without explicit permission. Obsolete items stay visible via a `plan_state=obsolete` filter (and an "Obsolete" badge), so the history of what the plan dropped is auditable.

### 11.4 Commit rules
1. `dry_run` **always** precedes commit in the skill; the preview shows `created / updated / obsolete / reactivated / conflicts` counts plus the conflict list.
2. Content fields (`name`, `description`, `sort_order`, `summary`) refresh from the manifest; **local `status` is preserved** — a revision cannot revert completed work to `pending`.
3. Divergences between manifest status and local status are *reported*, not applied.
4. Conflict list = in-progress orphans + title-length violations + duplicate manifest IDs + `sort_order` collisions + tasks referencing a milestone absent from the manifest.
5. All of the above inside one transaction; a failure leaves the project exactly as before.

---

## 12. Task content mapping

```markdown
Title:   <agent-written short title, ≤200 chars — required in the manifest>

## Acceptance   ← the contract, first thing in the body
<plan Acceptance cell, verbatim>

## Source
`M4-T4` · 20260925-full-plan.md v1.7 · Complexity: L · Traces: FR5, NFR12

**Files:** `sharing/resolver.py`, `shared/cache.py`
```

Titles are agent-authored because six plan descriptions exceed `VARCHAR(500)` (max 1463) — truncation would destroy meaning on exactly the compliance-heavy tasks that matter most.

---

## 13. Side effects and authentication (D5–D7, approved)

| Effect per create (`tasks.py:137-169`) | ×153 cost | Import behaviour |
|----------------------------------------|-----------|------------------|
| ref allocation + counter | cheap, valuable | **Keep** — refs are the point of the counter |
| 1 activity row | 153 feed entries | **Suppress** — write **one** summary activity per import (optional: one per milestone) |
| `spawn_push_task_ref` fire-and-forget HTTP | up to 153 background requests | **Defer** — single push at end, or none |
| webhook `task.done` | — | Not fired on create path (verified) — unchanged |

**D6:** gate `auto_prefix_enabled` on `project_key` alone (`projects.py:257-300` currently requires link+token for *both* prefix and registry) — otherwise imported projects get `ref = NULL`. `github_task_registry_enabled` keeps its link+token gate; the two features are genuinely independent.
**D7:** accept `X-Api-Key` on `POST /plan-import` **only** (existing `require_agent_or_user`, `deps.py:181`), then normal project RBAC (contributor+); shared agent key stays rejected when multi-tenancy is on.

---

## 14. UI support (great-support scope, P3)

- **Milestone list** on the project page: key, name, status, progress bar (`done/total`), sort order, obsolete dimming.
- **Milestone filter + column** on the Tasks table, plus **`plan_state` filter** (`active` default, `obsolete` opt-in).
- **Milestone chip row** above the Kanban to scope the board (columns stay status-based — D1).
- **"Obsolete" badge** on task cards/rows whose `plan_state='obsolete'`, with one-click restore to `active` for the reactivation case.
- **Task detail** shows milestone, `plan_ref`, `plan_state`.
- **Import UX:** the skill's preview is the primary surface in v1; a small in-app "last sync" banner (counts + timestamp) is P4.

Out of v1: Kanban columns grouped by milestone, timeline/gantt, milestone dependencies, burndown.

---

## 15. Phasing, effort, verification gates

Effort banded **S / M / L** (`estimated` — the source plan itself treats schedule estimation as out of scope).

| Phase | Scope | Effort |
|-------|-------|--------|
| **P1** | DDL (§9) + milestone CRUD + `plan-import` service/endpoint (§10–§11) + D6/D7 decouplings + backend tests | **M** |
| **P2** | `@plan-sync` agent skill: parse → validate → preview → POST → report | **S–M** |
| **P3** | UI (§14) | **M** |
| **P4** | Polish: BC→component mapping, deferred registry push, in-app sync banner | **S** |

**Verification gates for implementation** (P1 exit):
1. `pytest` in the API container — full suite green (repo has an existing suite: `api/tests/`, `pyproject.toml` testpaths) plus new tests: import creates 12 milestones/153 tasks · second import is a no-op · local `done` survives re-import · obsolete matrix (all four rows) · in-progress → conflict not auto-killed · reactivation restores `todo` · cross-project `plan_ref` uniqueness · `dry_run` writes nothing · `X-Api-Key`/RBAC behaviour.
2. **Migration idempotency:** restart the API container twice against a dev DB — zero errors, no duplicate objects (D10 verification).
3. `ruff check .`, `pyright .`, `python -m compileall` — clean (run in container, per host-hygiene rules).
4. `@code-verify milestone` + **MOD-06** prompt attached per slice; MOD-01 re-run if the diff crosses more than one hard boundary.

---

## 16. Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Plan format drift breaks manifest extraction | Import fails/mis-reads | Manifest schema validated at API boundary; drift costs a **skill** edit, zero app-code change (the point of D3) |
| Re-import regresses completed work | Lost status | Local-status-wins (§11.4) + mandatory dry-run diff |
| **In-progress task orphaned by a revision** | Under-way work silently killed | **Never auto-killed** — conflict row, explicit operator resolution (§11.3) |
| Obsolete work invisible → gets re-executed | Wasted effort | `plan_state` filter + badge; obsolete stays queryable, not deleted |
| Activity/GitHub push storm | Feed/API noise | §13 suppression |
| Long titles truncated | Meaning lost | Manifest requires agent titles ≤200 |
| Two truths: app milestones vs `NEXT.md` iterations | Confusion | One-way flow; sync never writes `.work/` |
| Restart applies DDL unexpectedly in prod | Surprise change | Additive-only DDL + `sql_schema_apply` is the repo's existing, documented switch — no new behaviour |
| Scope creep | Delay | Binding non-goals (§17) |

---

## 17. Non-goals (binding)

1. No import of risks, unknowns, assumptions, decision logs, FR/NFR tables or traceability matrices.
2. No writing to `.work/plans/NEXT.md` or `HANDOFF.md`.
3. No generic bulk-create API.
4. No Kanban-by-milestone columns, gantt, or inter-milestone dependencies in v1.
5. No `iterations`/`stages` tables (D2); no `parent_milestone_id` nesting.
6. No deletion of anything on re-sync (§11.3).
7. No new migration files or ORM migration tooling (D10).

---

## 18. Decisions

**Approved 2026-09-29 (D1–D8):** first-class milestones table · stage/iteration collapse · agent-manifest import · `plan_ref` upsert with local-status-wins · side-effect suppression · `auto_prefix_enabled` decoupling · `X-Api-Key` on import endpoint · scope P1–P3.

**New in v2.0 — sign-off requested:**

| # | Decision | Recommendation |
|---|----------|----------------|
| **D9** | Obsolescence representation | **`plan_state` column** (`active/obsolete`) on tasks + milestones — provenance separate from workflow status; reject a new `obsolete` status value |
| **D10** | Migration mechanism | **Append idempotent DDL to existing `sql/schema_*.sql`**; executed by the lifespan on every container start (`main.py:56-63`); no new files, no manual step |
| **D11** | Obsolete action matrix | Per-status matrix in §11.3 — started-not-finished = **conflict, never auto-killed**; done keeps `done`; reappearing work reactivates; nothing deleted |

---

## Appendix A — Decision log

| ID | Date | Choice | Alternatives rejected |
|----|------|--------|-----------------------|
| D1 | 2026-09-29 | First-class `milestones` table | `components` reuse (collides with BCs) · `parent_task_id` reuse (invisible, wrong) · text encoding (no structure) |
| D2 | 2026-09-29 | Stage/iteration = milestone entity | Separate stages/iterations tables (three sync surfaces, one level needed) |
| D3 | 2026-09-29 | Agent parses, API ingests | Python markdown parser (brittle) · N× loop (no atomicity) · direct SQL (RBAC bypass) |
| D4 | 2026-09-29 | `plan_ref` upsert, local-status-wins | Plan-status-wins (reverts done work) · recreate (duplicates) |
| D5 | 2026-09-29 | Suppress per-task activity, defer registry push | Per-task effects (153 rows + 153 HTTP calls) |
| D6 | 2026-09-29 | `auto_prefix_enabled` on `project_key` only | Keep GitHub-link gate (imported tasks lose refs) |
| D7 | 2026-09-29 | `X-Api-Key` on import endpoint only | JWT-only (agent sync impossible) · global key writes (too broad) |
| D8 | 2026-09-29 | v1 = P1–P3, non-goals binding | Full import incl. registries (not work items) |
| **D9** | 2026-09-29 | `plan_state` provenance column | New `obsolete` status value (UI/API churn; conflates provenance with workflow) |
| **D10** | 2026-09-29 | DDL into existing restart-run `schema_*.sql`, idempotent | New numbered migration files (violates `SCHEMA_SQL_FILE_ORDER` inventory check, `schema_sql.py:40-52`) · manual apply step (violates restart requirement) |
| **D11** | 2026-09-29 | Per-status obsolete matrix; in-progress = conflict | Mark-all-obsolete (kills under-way work) · delete-orphans (destructive) · ignore-orphans (stale tasks look live) |

---

## Appendix B — Evidence index

| Claim | Evidence |
|-------|----------|
| No milestone/stage/iteration concept | `grep -riE "milestone\|sprint\|epic\|iteration\|phase" sql/ api/app/models/` → no matches |
| Migrations run on every API start | `main.py:56-63` (lifespan) → `db.py:43-49` (`init_db` → pre-bootstrap) + `schema_sql.py:101-126` |
| Fixed file order + inventory assertion | `schema_sql.py:18-25,40-52` |
| `sql_schema_apply` default True | `api/app/config.py:40` |
| Task status vocab + terminal set | `schemas.py:12`, `tasks.py:49,139` |
| UI status parity (5/5/5) | `KanbanBoard.tsx:17-23`, `TaskDetailEditor.tsx:12`, `TasksClient.tsx:89-93` |
| No bulk create | all `.post(` routes enumerated; only `tasks.py:351` / `tickets.py:300` update-batch |
| Batch cap 100 | `schemas.py:516-521` |
| Per-create side effects | `tasks.py:137-169` (ref, activity, push; no webhook) |
| Ref gating | `ref_alloc.py:44-46` |
| `auto_prefix_enabled` needs link+token | `projects.py:257-300` |
| JWT-only writes; key auth read-only | `deps.py:122` vs `deps.py:181`; only `agent_query.py`/`platform.py` import it, both GET-only |
| Parent not filterable / not in UI | `tasks.py:85-86`; `tasks/[taskId]/page.tsx:30` (type only) |
| Board is status-grouped | `KanbanBoard.tsx:17-23` |
| Explicit router registration list | `main.py:118-151` |
| Model registry is explicit | `api/app/models/__init__.py` imports + `__all__` |
| Test suite exists | `api/tests/` (conftest, factories, 8+ files), `pyproject.toml:64-66` |
| 153 tasks / 12 milestones / 1463-char max / 6 amendments / D20 | measured on `plans/20260925-full-plan.md` |
| One milestone per iteration block | `.work/plans/NEXT.md` iteration blocks (M5–M8, MT) |
| `tasks.title` limit 500 | `sql/schema_changes.sql:64` |

---

## Appendix C — MOD-01 coupling audit (run 2026-09-29)

**Inputs:** repo layout (single backend deployable `api`, frontend `web`, `sql/` mounted, framework skill outside repo) · design note = this proposal · test commands: `pytest` (configured), `ruff`, `pyright` — run in container.

```markdown
## Coupling audit summary
- Boundaries crossed: 4 — api/app (routers + services + models), sql/, web/, framework skills
- New or tighter dependencies: plan_import service → Task/Milestone models, ref_alloc, activity_writer;
  milestones router → auth/project_access deps; import route → require_agent_or_user
- Shared persistence risks: `tasks` table written by two paths (single-row router + bulk plan_import) —
  mitigated: single-writer split per concern, same ORM models, one transaction per import, no raw SQL
- Coupling score: low (evidence: measured — single deployable, no new network hop, no new background
  service, all DDL additive/defaulted, no cross-owner shared mutable state)
- Human architectural review: required — reason: AI-assisted diff crosses >1 hard boundary
  (api layers + sql + web); this proposal is that review

## Recommendation
proceed_with_guards

## Guardrails if merging now
- Tests: full pytest suite + the plan-import matrix in §15 (incl. restart-twice migration check)
- Rollout: additive schema only; `sql_schema_apply` is the existing kill-switch; rollback =
  stop applying the new statements (columns are nullable/defaulted, nothing destructive)
```

**Concept / NFR registry (proposal stage; copy to SPEC §15):** MOD-01 `yes` (audit above) · MOD-06 `yes, required at implementation` · MOD-02/03/04/05/07/08 `no` — no new hop / billable unit / deployable / distribution / prompt composition / IaC.

---

## Next action

**Owner sign-off on D9–D11.** Then: `@feature-spec create - plan-sync` (SPEC carries §15 registry from Appendix C) → `@code-implementation plan - P1`.
