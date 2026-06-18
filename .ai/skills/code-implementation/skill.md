---
name: code-implementation
description: >-
  Execute an approved implementation iteration: validate or generate the
  NEXT.md iteration block from the plan-master milestone, implement tasks per
  CONVENTIONS and FEATURE_STANDARD, gate each task on tests/lint, and finalize
  the iteration. Verification modes live in the **code-verify** skill. Use when the
  user says code-implementation plan, start, continue (optional - N, until blocked,
  or M{N}-T{a}..T{b}), complete, or status.
  Requires implementation-ready (plan-master Approved) or explicit HANDOFF waiver.
---

# code-implementation

Execute implementation iterations derived from an **Approved master plan** (`{PLANS_ROOT}/full/YYYYMMDD-full-plan.md`). Each iteration is scoped by a `## Current iteration` block in `NEXT.md` - validated before the first line of code, gated per task on tests/lint, and cross-verified before completion.

**Tool-agnostic** (Cursor, Claude Code, opencode, Codex). **Requires:** `implementation-ready: yes` from `@plan-master status`, or an explicit HANDOFF waiver noting which milestones may proceed early.

**Pairs with:** `session-control` (bookends), `plan-master` (milestone source and revisions), `code-verify` (milestone / uncommitted / last audits), `code-repair` (remediate verify/migration failures), `db-migration` (all schema changes), `.ai/standards/*CONVENTIONS*`, `.ai/standards/*FEATURE_STANDARD*` (paths from `.cursorrules`).

**Registry:** [`.ai/skills/SKILL_DEPENDENCIES.md`](../SKILL_DEPENDENCIES.md).

**Canonical path:** `.ai/skills/code-implementation/skill.md` · **Invocation examples:** `reference.md`

**Hard rules:**

- **No implementation without a valid iteration block.** If `NEXT.md` lacks one, run `plan` first (alias: `plan-iteration`).
- **No code without reading the relevant SPEC(s) first.** Evidence-first: read before writing.
- **No task is `done` until its gate passes.** Tests + lint + type-check must exit 0 before advancing.
- **Scope discipline.** Do not modify any file not declared in the task's file list. Undo and document any accidental out-of-scope change.
- **Schema changes go through `db-migration`.** Stop the task, create the migration script, resume. No inline DDL in application code. Follow `.cursorrules` § **Migration policy** (startup runner, verify, human approval for exceptions/test DML).
- **Verification commands** come from `{AGENT_RULES_FILE}` § Docker (or § local/CI from `REPLACE:TECH_STACK_DOC` when not containerized). Never hardcode another project's service name, workdir, or toolchain.
- **No host dependency installs** for containerized services (`{AGENT_RULES_FILE}` § Host hygiene) — e.g. run `npm ci` via `docker compose exec`, not on the host.
- **Protected files** per `{AGENT_RULES_FILE}` §Protected Files - require explicit user permission before modification. Stop and ask.
- **No secrets in code, tests, or comments.** Use `.env` variables or KMS references.
- **Completion Gate is non-negotiable.** Per `.cursorrules`: code changed → checks run → output reviewed → residual risks listed. Cannot be skipped.
- **AI-assisted default:** Cursor/agent sessions are **AI-assisted: yes** for MOD-06 unless the human explicitly declares **`human-only`** in the same message. Agents must not skip MOD-06 by self-classifying.
- **MOD-06 before complete:** `@concept-run - MOD-06` (or documented output path) is **required** before `@code-implementation complete` when any task in the iteration touched application source or tests (per DIRECTORY_MAP).
- **Every mode ends with a Completion checklist** - each item `pass` | `fail` | `skip` with evidence.

---

## Parse invocation

Normalize the user message to **verb** + optional **target**.

| User says | Verb | Action |
|-----------|------|--------|
| `@code-implementation` **status** | status | Read-only: task matrix, progress snapshot |
| `@code-implementation` **plan** - M1 | plan | Generate/validate `## Current iteration` block from plan-master milestone |
| `code-implementation` **start** | start | Load iteration block, read SPECs/CONVENTIONS, begin first task |
| `code-implementation` **continue** | continue | [Continue protocol](#continue-protocol) - default **1** task (see target table) |
| `code-implementation` **continue** - 5 | continue | Batch: up to **5** tasks, same stop rules as below |
| `code-implementation` **continue** - until blocked | continue | Batch: tasks until gate **fail**, **blocked**, or queue exhausted |
| `code-implementation` **continue** - M4-T2..T6 | continue | Batch: inclusive task **range** in iteration order |
| `code-implementation` **complete** | complete | Finalize iteration: CO2 `@code-verify milestone` + CO1 gates + update HANDOFF/NEXT |
| `code-implementation` **verify** [uncommitted \| last] | - | **Legacy** - use `@code-verify` (see `code-verify` skill) |
| `code-implementation` **task** T3 | task | Execute a single task by shorthand ID (active iteration context) |
| `code-implementation` **task** M1-T3 | task | Execute a single task by globally unique ID; gate immediately |

**Aliases:** `impl`, `code`, `implement` → map to **continue** if iteration block exists, else **start**. **`plan-iteration`** is the legacy alias of **`plan`** - both work.

**Natural language (same semantics):** "implement the next 5 tasks", "continue until blocked/failed" → parse as **`continue - 5`** or **`continue - until blocked`** when the user is clearly invoking this skill.

**Ambiguous:** if `NEXT.md` has an iteration block but status is unknown → run abbreviated **status** and ask once.

**Disambiguation:** On **`continue`**, `- M4` alone is **not** a milestone (use **`plan - M4`**). After `-`, only: a positive integer (`5`), `until blocked`, or a task range (`M4-T2..T6`).

---

## Step 0 - Pick a mode

| Mode | Condition | Action |
|------|-----------|--------|
| **status** | progress/matrix/snapshot requested | [Status protocol](#status-protocol) - read-only |
| **plan** *(alias: `plan-iteration`)* | iteration block missing or invalid; user names a milestone | [Plan protocol](#plan-protocol) |
| **start** | valid iteration block exists; no task started | [Start protocol](#start-protocol) |
| **continue** | iteration in-progress; tasks pending or one in-progress | [Continue protocol](#continue-protocol) |
| **complete** | all tasks done or user signals completion | [Complete protocol](#complete-protocol) |
| **task** | user names `T{N}` or `M{N}-T{N}` | Execute that task; run gate; report |

Do not run `plan` when the user asked for **status** only. For any **verify** request, use **`@code-verify`** (`code-verify` skill).

**Suggested cadence:** `@code-verify uncommitted` before commit · `@code-verify last` after commit/push · `@code-verify milestone` before **complete**.

---

## NEXT.md iteration block format

The `## Current iteration` section is owned by this skill. `session-control` and `plan-foundation` manage other sections; do not delete or rewrite theirs.

**Template + filled example:** `reference.md` § "NEXT.md iteration block - quick template". The template has subsections: header (Milestone ref / Status / Started / Target), **In scope**, **Out of scope (explicit)**, **Tasks** (table: `ID | Description | Files | Status | Notes`), **Acceptance criteria**, **Validation steps** (tests/lint/type/manual), **Owner blockers**, **Cross-LLM verification**, **Done this iteration**, **Concept / NFR registry (this iteration)**.

### Task ID convention

Task IDs use the globally unique **`M{N}-T{N}`** format inherited from the approved plan-master (e.g. `M1-T3`). The shorthand `T{N}` is acceptable within this iteration block and in agent prompts when the active milestone is unambiguous. Always use the full `M{N}-T{N}` form in:

- Cross-milestone references
- HANDOFF and NEXT.md `## Done this iteration` table
- Traceability matrix in the plan-master

### Valid iteration block criteria

An iteration block is **valid** when all of the following are true:

1. Milestone ref present and traces to a task row in the approved plan-master §19.
2. In scope / out of scope sections are explicit (not empty).
3. At least one task row with at least one declared file path.
4. Acceptance criteria section present with at least one item.
5. Validation steps include at least one runnable test command from `{AGENT_RULES_FILE}`.
6. **`### Concept / NFR registry (this iteration)`** subsection is present with one row per architecture concept id **or** explicit `N/A` for each id with reason (if the repository has no concept pack, one row: `N/A - no pack`).

If any criterion fails → iteration block is **invalid** → run **plan** before **start**.

---

## Plan protocol

*(Legacy alias: `plan-iteration`. Both invocations resolve here.)*

Generates or validates the `## Current iteration` block in `NEXT.md` from the next incomplete milestone in the approved plan-master.

### PI1 - Verify prerequisites

1. Read `{HANDOFF}` - note owner blockers, waivers, M1-only authorizations.
2. Read `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md` (latest by date prefix). Confirm **Status: Approved** (or owner waiver recorded in HANDOFF for early M{N} start).
3. If no plan file → **stop** with the [blocked-report shape](#blocked-report-shape):
   - **Required:** Approved `*-full-plan.md`
   - **Detected:** no `{PLANS_ROOT}/full/*-full-plan.md`
   - **Run first:** `@plan-foundation certify plan-master-ready` → `@plan-master greenfield`
4. If plan is **Draft** and HANDOFF has **no** waiver naming milestone **M{N}** → **stop** with the same shape:
   - **Required:** plan `Status: Approved` **or** HANDOFF waiver for `M{N}`
   - **Detected:** plan is `Status: Draft`; no HANDOFF waiver for `M{N}`
   - **Run first:** `@plan-master status` → approve plan, or document HANDOFF waiver
5. Read `{ITERATION_CARRIER}` - find `## Done this iteration` and `## Recommended next` to determine which milestone is next.

**Note:** **implementation-ready** is checked at [ST0](#st0--implementation-gate) (**start** / **continue**), not at this step - you may build the iteration block once the plan is **Approved** (or milestone-waived per steps 2–4).

### Blocked-report shape

Per [SKILL_DEPENDENCIES.md § Blocked report shape](../SKILL_DEPENDENCIES.md#blocked-report-shape) - header: `## @code-implementation <command> - blocked (prerequisite)`.

### PI2 - Select target milestone

1. Identify the first incomplete milestone (M1…) in plan-master §19.
2. If user specified `plan - M{N}` (or legacy `plan-iteration - M{N}`), use that milestone directly; verify it exists in the plan.
3. Check dependencies: if the milestone declares prior milestones as dependencies, confirm they are done (or explicitly waived in HANDOFF).

### PI3 - Derive tasks

Copy the task rows from the plan-master §19 milestone verbatim into the iteration block. **Preserve the `M{N}-T{N}` IDs exactly as defined in the plan** - do not renumber or rename them. If the plan-master uses shorthand IDs, expand them to the full `M{N}-T{N}` form now.

For each task:

- Map to at least one file path (create or modify). If unknown, mark `TBD - owner needed` and add to Owner blockers.
- Link to FR or NFR from plan-master §3–4.
- Read the relevant SPEC(s) under `{FEATURE_SPEC_ROOT}/` for the bounded context. If a rule (R1…) is ambiguous → add to Owner blockers; do not invent a resolution.
- Estimate complexity: S / M / L. Flag L tasks as candidates for splitting.
- Detect schema changes: if any task requires DDL → add a migration sub-task (`db-migration create`) as T{N}a before the implementation task.

### PI4 - Write iteration block

Write the `## Current iteration` section into `NEXT.md` - insert after `## Recommended next`. Do not delete or overwrite other sections.

Include a **`### Concept / NFR registry (this iteration)`** subsection (table or explicit `N/A - no pack`). Rows must align with the **feature SPEC §15** (or equivalent) for the bounded contexts touched, or state why the iteration is **platform-only** with per-MOD `N/A` reasons.

### PI5 - Plan report

```markdown
## code-implementation plan - M{N}: {name}

**Milestone:** M{N} · {task count} tasks · **Source:** {plan-master path}
**Prerequisites:** pass | fail | waived

### Tasks derived
| ID | Description | Files | Complexity | FR/NFR |
|----|-------------|-------|------------|--------|
| T1 | … | … | S/M/L | FR-{N} |

### Ambiguities / blockers
{list or none - each with: description, blocks task, recommended owner action}

### Completion checklist
| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Approved plan read | pass/fail | path |
| 2 | Milestone found; dependencies clear | pass/fail | M{N} |
| 3 | Tasks derived with file paths | pass/fail | count |
| 4 | SPEC(s) read for ambiguity check | pass/skip | paths |
| 5 | Migration sub-tasks added (if schema changes) | pass/skip | |
| 6 | Iteration block written to NEXT.md | pass/fail | |
| 7 | Valid iteration block criteria met | pass/fail | criteria |
| 8 | Concept / NFR registry subsection present | pass/fail | rows or N/A |
```

---

## Start protocol

### ST0 - Implementation gate

Before ST1 (and before first line of application code):

1. Read `{HANDOFF}` for milestone waivers (e.g. M1 platform skeleton).
2. If HANDOFF waives the active iteration milestone → **pass** (note waiver in start report).
3. Else run `@plan-master status` (or read last recorded **Implementation-ready:** in HANDOFF if dated today).
4. If **implementation-ready: no** → **stop** with the [blocked-report shape](#blocked-report-shape):
   - **Required:** `implementation-ready: yes` **or** HANDOFF waiver for the active milestone
   - **Detected:** `implementation-ready: no` (Draft plan / missing plan / plan-master-ready expired)
   - **Run first:** `@plan-master status` → approve plan, or document HANDOFF waiver
5. If **yes** → proceed to ST1.

**Anti-pattern:** **start** or **continue** when only **plan-master-ready** is set - that unlocks planning and M1 *prep*, not broad implementation unless HANDOFF says so.

### ST1 - Mandatory reads

| # | File | Pass criteria |
|---|------|---------------|
| 1 | `.work/plans/NEXT.md` § Current iteration | Valid per [criteria](#valid-iteration-block-criteria) |
| 2 | Relevant SPEC(s) for bounded context | Can state: R1… rules, data model, invariants, error codes |
| 3 | `.ai/standards/*CONVENTIONS*` | Can state: module structure, naming, import rules, logging |
| 4 | `.ai/standards/*FEATURE_STANDARD*` | Can state: service/repo/test layout for this context |
| 5 | `.work/context/HANDOFF.md` | Know: owner blockers, waivers, previous session state |
| 6 | **Optional:** `.ai/docs/guides/workflows/README.md` (artifact matrix) and `20260518-guide-workflows-index.md` (curriculum), or repo equivalents | When concepts/workflows apply: know bootstrap, tutorials, and which artifacts touch plan vs implementation |

If any mandatory read **fails** → stop. Fix before implementing.

### ST2 - Environment snapshot

```bash
git status -sb
git log -1 --oneline
docker compose ps 2>/dev/null || true
```

Record: branch, clean/dirty, running services.

### ST3 - Assumption ledger

Before the first task, state the 3–5 most consequential assumptions for this iteration. Label each:

- **Confirmed** - cite SPEC rule, ADR, or **file path + quoted snippet** (or test command + exit code). Prose alone is not sufficient.
- **Inference** - likely but not proven; note partial evidence.
- **Unverified** - must check; append to `{PLANS_ROOT}/UNKNOWNS.md`.

Do not collapse Inference into Confirmed. A **Confirmed** label without a cite is treated as **Inference** in review.

### ST4 - Select first task

Pick T1 (or first pending task). Mark it `in-progress` in the task table. Announce the task, its file list, and which SPEC rules (R1…) govern it.

### ST5 - Start report

```markdown
## code-implementation start - M{N}: {name}

**Date:** {ISO date} · **Branch:** {branch} · **Tree:** clean | dirty

### Completion checklist
| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Iteration block valid | pass/fail | criteria |
| 2 | SPEC(s) read | pass/fail | paths |
| 3 | CONVENTIONS read | pass/fail | |
| 4 | FEATURE_STANDARD read | pass/fail | |
| 5 | HANDOFF read | pass/fail | |
| 6 | Environment snapshot | pass/skip | branch, services |
| 7 | Assumption ledger | pass | count |
| 8 | First task selected | pass | T{N} |

### You are cleared to implement when
All mandatory checks (1–5, 7–8) are **pass**. If any **fail**, fix before proceeding.

### First task
**{T{N}}:** {description}
**Files:** {list}
**SPEC rules in scope:** {R1…}
```

---

## Continue target (parse `-` argument)

Resolve the batch **before** the task loop. Default when `-` is omitted: **`count=1`**.

| User target | Batch mode | Task queue |
|-------------|------------|------------|
| *(omit)* | `count=1` | Next incomplete tasks in iteration table order |
| `- 5` or `- 5 tasks` | `count=5` | Next up to 5 incomplete tasks |
| `- until blocked` | `until-blocked` | Next incomplete tasks until a **stop condition** (below) |
| `- M4-T2..T6` | `range` | Inclusive `M4-T2` … `M4-T6` that exist in the active iteration block, in table order |

**Range rules:**

- Both endpoints must use full `M{N}-T{N}` ids (shorthand `T2..T6` allowed only when the active milestone is unambiguous - expand to `M{N}-T2..M{N}-T6`).
- Skip tasks already `done` (do not count toward work; they are not in the queue).
- If the range includes a `blocked` task that stays blocked after the unblock check → **stop the batch** at that task (do not skip within the range).

**Equivalence:** `@code-implementation continue - 5` means **implement the next 5 incomplete tasks, or fewer if a stop condition fires first** (gate fail, blocker, protected file, schema detour, or queue exhausted). Same as "implement the next 5 tasks or until blocked/failed."

---

## Continue protocol

1. Run [ST0 - Implementation gate](#st0--implementation-gate) (abbreviated if start ran in the same session with no plan/HANDOFF change).
2. **Parse continue target** → [Continue target](#continue-target-parse--argument). Emit the planned queue in the opening report (task ids + batch mode).
3. **Unblock check:** Read `{PLANS_ROOT}/UNKNOWNS.md` and `{HANDOFF}`. Scan the iteration block for any task with status `blocked`:
   a. For each `blocked` task in the queue: find the blocker in `### Owner blockers` and/or `UNKNOWNS.md`.
   b. If resolved → flip to `pending`; annotate `unblocked YYYY-MM-DD - <reason>`.
   c. If still `blocked` when that task is reached → **stop batch**; recommend `@session-control close` with blocker list.
4. If the queue is empty at start → report and recommend **complete** or **status**; do not implement.
5. **Per-task loop** (for each task in the queue until batch limit or stop):
   a. If task is `in-progress`: resume with file evidence (read before editing).
   b. If task is `pending`: read every file to modify **before** any change.
   c. Implement per CONVENTIONS, FEATURE_STANDARD, and SPEC rules (R1…).
   d. Do not modify files outside the task's declared file list.
   e. Run [Task gate](#task-gate).
   f. On gate **pass**: mark `done YYYY-MM-DD`; emit progress line: **`Batch {k}/{limit}: {M{N}-T{N}} done`** (see [Batch progress lines](#batch-progress-lines)); advance `k`.
   g. On gate **fail**: report exact output; diagnose; offer fix in-session. **Stop the batch** - do not start the next queued task until this task passes (user may re-run `continue` after fix).
   h. **Schema change mid-task:** invoke `@db-migration create`; **stop batch** unless user asked to resume the same batch in the same message.
   i. **Protected file** change needed without approval → **stop batch**; ask once.
   j. **Blocked task** encountered → see [Blocked task protocol](#blocked-task-protocol); **stop batch**.
6. **Batch-end sweep (mandatory).** After the loop ends for **any** reason - including a single-task `continue` where one or more files were modified - run the [Batch-end sweep](#batch-end-sweep) before reporting. Skip only when zero files changed (no completed task wrote to disk).
7. Emit [Batch summary](#batch-summary) (mandatory when batch mode is not a single task, recommended always). Include sweep verdict.
8. When **all** iteration tasks are `done`: recommend **complete** - do not auto-finalize.

### Batch progress lines

After each task that reaches `done` in a batch:

| Batch mode | Progress line format |
|------------|----------------------|
| `count=N` | `Batch {k}/{N}: {M{a}-T{b}} done` |
| `until-blocked` | `Batch {k}: {M{a}-T{b}} done (limit: until blocked)` |
| `range` | `Batch {k}/{R}: {M{a}-T{b}} done` where **R** = incomplete tasks in range at batch start |

Example: `Batch 3/5: M4-T4 done`

### Batch summary

```markdown
## code-implementation continue - batch summary

**Mode:** count=5 | until-blocked | range M4-T2..M4-T6
**Completed:** M4-T2, M4-T3 (2 tasks)
**Stopped because:** task gate fail on M4-T4 | blocked on M4-T5 | batch limit reached | all queued tasks done
**Sweep verdict:** pass | fail | skip - no files changed   (see Batch-end sweep)
**Next:** @code-implementation continue | @code-implementation continue - 3 | fix M4-T4 and re-run continue
```

### Batch-end sweep

Cheap audit on the **cumulative** changeset after a batch (or single-task `continue`) finishes. Prevents the "issues surface only after I ask" pattern - per-task gates run on one task's files; this sweep looks at the union.

**Run only when at least one task in the loop changed files.** If the loop stopped before any file changed (e.g. gate fail on first task pre-edit, blocker, protected-file refusal), record `skip - no files changed` and proceed to Batch summary.

| # | Step | How |
|---|------|-----|
| 1 | Cumulative diff snapshot | `git diff --stat` and `git diff --name-only` (working tree vs HEAD) |
| 2 | Cross-task self-review | Read the union diff. State in 3-6 bullets: refactor leftovers, dead helpers from completed tasks, symbol renames that may have stale call-sites, any file touched by more than one task in the batch |
| 3 | Auto-invoke `@code-verify uncommitted` | Run the skill; fold its verdict (pass / fail) into Batch summary `Sweep verdict` |
| 4 | Warnings inventory | Sum non-fatal lint/type warnings in files changed by the batch (per [Task gate](#task-gate) row "Warnings in touched files"). If any task left warnings in Notes, restate the total |

**On sweep `fail`:** do **not** claim batch success. Report the failing checks (e.g. uncommitted scope violation, secrets, protected file, fresh gate fail). Stop. Recommend `@code-repair repair - from uncommitted` (or fix in-session + re-gate), or `@session-control close` with the issue logged.

**On sweep `pass` with warnings or self-review findings:** batch succeeds; surface the findings in Batch summary and (when material) append to `{PLANS_ROOT}/UNKNOWNS.md` so they cannot get lost.

**Honesty:** The sweep replaces neither task gates nor `@code-verify milestone`. It is the **minimum** post-batch audit. `@code-verify milestone` is still required before **complete**.

### Stop conditions (all batch modes)

Stop the batch when **any** occurs (whichever comes first):

| # | Condition |
|---|-----------|
| 1 | Task gate **fail** on current task (after reporting; do not skip to next queued task) |
| 2 | Task **blocked** and still blocked after unblock check |
| 3 | **Protected file** change required without user approval in the same message |
| 4 | **Schema change** requires `@db-migration create` (stop unless user explicitly continues batch in same message) |
| 5 | **Batch limit** reached (`count=N` satisfied, or range fully processed) |
| 6 | No more **pending** / **in-progress** tasks in the queue |
| 7 | All iteration tasks **`done`** → recommend **complete** |

Regardless of which stop condition fired, run [Batch-end sweep](#batch-end-sweep) before emitting Batch summary if any file changed during the loop.

---

## Task gate

Run after every task implementation before marking `done`. All checks must pass. **Mechanical only** - no master-plan reads. For pre-commit or post-push audits with a verdict report, use `@code-verify` (**uncommitted** / **last** / **milestone**).

| Check | Command | Pass criteria |
|-------|---------|---------------|
| Unit tests (scoped) | `{AGENT_RULES_FILE}` § Docker - scoped `REPLACE:TEST_COMMAND` | Exit 0 |
| Full suite (smoke) | Same section - full `REPLACE:TEST_COMMAND` | Exit 0 |
| Lint | `REPLACE:LINT_COMMAND` (via compose exec when containerized) | Exit 0 |
| Type check | `REPLACE:TYPECHECK_COMMAND` | Exit 0 per CONVENTIONS or documented baseline exceptions |
| **Warnings in touched files** | Re-read lint/type output | Count non-fatal warnings in files this task changed; **0** or listed in task `Notes` |
| No secrets in diff | `git diff --unified=0` reviewed | Same rules as `code-verify` S1 - no keys, tokens, passwords, PEM material |
| Protected files | `git diff --name-only` reviewed | No `.cursorrules` §Protected Files paths unless user explicitly approved |
| Scope discipline | `git diff --name-only` | All paths in declared task file list |
| MOD-06 (AI-assisted) | `@concept-run - MOD-06` when iteration touched code | Output attached to PR, task `Notes`, or iteration registry; **required** before **complete** (see CO1) |
| **SC1 self-critique** | [SC1 - Self-critique](#sc1--self-critique) below | Five bullets recorded in task `Notes` or iteration log |

**Also verify (manual - no single exit code):**

- **Residual risks / deferred sub-work:** Before marking a task `done`, any follow-up work, untested edge cases, or known limitations discovered during implementation must be captured in the task's `Notes` column or appended to `{PLANS_ROOT}/UNKNOWNS.md` with a new U* row. Do not let deferred sub-work exist only in the agent report - promote it to a tracked artifact.
- **TODO / FIXME hygiene:** If the diff added any `TODO`, `FIXME`, `HACK`, or `XXX` comment, promote it to a `U*` row in `{PLANS_ROOT}/UNKNOWNS.md` **or** capture it in task `Notes` with owner/follow-up before marking `done`.
- **Observability:** If the task touches HTTP handlers, jobs, logging, or outbound calls: confirm fields and correlation/trace behavior match the feature SPEC §9 and `{OBSERVABILITY_SPEC}` (once customized for the project); otherwise note `n/a - no observability surfaces touched`.
- **Concept / MOD prompts:** Cursor/agent sessions are **AI-assisted: yes** by default (see `.ai/concepts/README.md` § Trigger table). Run MOD-06 per task or batch before **complete**; attach output skeleton to PR or iteration `Notes`. For multi-package edits, attach coupling-audit (MOD-01) when boundaries crossed. Rows in `### Concept / NFR registry` with `Applies=yes` must not remain `pending` before **complete** (CO1).

### SC1 - Self-critique

Two-minute structured re-read of the task diff before marking `done`. Answer all five in task `Notes` (or, in batch mode, the iteration log) - one bullet each, ≤1 line. **Do not** answer with "none" or "n/a" reflexively; if a row is truly empty, write the reason (e.g. `none - touched only one self-contained file`).

| # | Prompt | Purpose |
|---|--------|---------|
| 1 | What did I change beyond the declared file list or task scope, even if accidentally? | Scope drift |
| 2 | What is the most likely failure mode for this code in 3 months? | Hidden brittleness |
| 3 | Which referenced file did I assume unchanged but did not re-read this session? | Stale-assumption bugs |
| 4 | Is there a test for the first failure mode I would expect? If no, where is it captured? | Coverage gap → must land in `Notes` or `UNKNOWNS.md` |
| 5 | Any non-fatal lint / type / compiler warnings in touched files? Count + summary. | Warning rot |

If SC1 surfaces a real concern (not just "looks fine") → **either fix it now or open a `U*` row** in `{PLANS_ROOT}/UNKNOWNS.md` referencing this task. Marking `done` while leaving an SC1 concern undocumented is a gate **fail**.

### Post-fix re-gate

When the agent applies a fix in response to **any** reported issue - user-flagged, batch-end sweep finding, lint regression, or test failure - it **must re-run the full task gate** for the affected task(s) before claiming the fix succeeded. Visual inspection alone is not evidence of repair. The progress line for the re-gated task becomes:

```text
Task M{N}-T{N} re-gated <YYYY-MM-DD> after fix: pass | fail (<reason>)
```

This applies whether the original issue was caught inside the same batch, in a follow-up message, or on a later session.

**On any gate failure:** report exact output. Diagnose root cause. Fix. Re-gate per above. Do not mark task `done` or proceed to the next task until all checks pass.

**Scope violation** (file outside task list modified): stop immediately. Undo or stash the out-of-scope change. Document why in task Notes. If the out-of-scope change is genuinely necessary, update the task file list and note the expansion before proceeding.

---

## Status protocol

Read-only. No file writes.

1. Read `NEXT.md §Current iteration`.
2. Run `git diff --stat` and `git log --oneline -5`.
3. Count: pending / in-progress / done / blocked tasks.
4. Output:

```markdown
## code-implementation status - M{N}: {name}

**Status:** {iteration status} · **Date:** {ISO date}
**Branch:** {branch} · **Tree:** clean | dirty

### Task matrix
████░░░░░░ 40% (2 / 5 tasks done)

| ID | Description | Status | Files | Notes |
|----|-------------|--------|-------|-------|
| T1 | … | done 2026-05-18 | `…` | |
| T2 | … | done 2026-05-18 | `…` | |
| T3 | … | in-progress | `…` | |
| T4 | … | pending | | |
| T5 | … | blocked | | owner: legal / compliance approval |

### Acceptance criteria
| Criterion | Status |
|-----------|--------|
| … | pass / pending / fail |

### Cross-LLM verification
{status from iteration block}

### Owner blockers
{list or none}

### Residual risks / unknowns
{from UNKNOWNS.md entries opened this iteration}
```

**Visual / datagrid output:** on user request for a visual summary, render the task table with alignment and a text progress bar. Do not use emojis unless the user requests them.

---

## Verification (delegated)

All verify modes moved to **`code-verify`** (`.ai/skills/code-verify/skill.md`):

| Mode | When |
|------|------|
| `@code-verify milestone` | Before **complete**, ≥80% tasks, or full iteration audit |
| `@code-verify uncommitted` | Dirty tree, pre-commit |
| `@code-verify last` | After commit or push - audits whichever event was **last** |

Legacy `@code-implementation verify` → run **`@code-verify milestone`**.

---

## Complete protocol

**Execution order:** **CO2 → CO1 → CO3 → CO4 → CO5 → CO6** (milestone verify before final gates - avoids duplicate full-suite runs).

### CO2 - Verify (mandatory before complete)

Run **`@code-verify milestone`** if not run since the last task was completed. Verdict must be **pass** or **pass with gaps** (waivers documented in HANDOFF). **fail** blocks completion.

### CO1 - Full iteration gate

Run remaining iteration validation steps (manual checks and any steps not covered by CO2 shared Docker gates).

**Skip duplicate suite:** If CO2 shared gates (`REPLACE:TEST_COMMAND`, `REPLACE:LINT_COMMAND`, `REPLACE:TYPECHECK_COMMAND` per `{AGENT_RULES_FILE}`) already **passed** on the **current working tree** (no file changes since the milestone verify report), skip re-running them - record **skip - covered by CO2**. Otherwise run all three from `{AGENT_RULES_FILE}` § Docker (or local equivalents from `REPLACE:TECH_STACK_DOC`).

All **manual** validation steps in the iteration block (e.g. `curl /health`) must still pass. Failures must be fixed or waived with a documented owner line in HANDOFF.

**Concept/NFR registry gate:** Before completing a milestone, inspect `NEXT.md` `### Concept / NFR registry (this iteration)`. Any row with `Applies=yes` and `Status=pending` must be resolved - either run `@concept-run` for that MOD id, or document a `gap - <reason>` waiver with owner. CO1 fails if unresolved applicable concept rows remain.

**MOD-06 gate (mandatory when code changed):** If any task in the iteration modified application source or tests, CO1 **fails** unless MOD-06 output is attached (PR body, task `Notes`, or iteration registry with `Status=done` and evidence path). **`human-only`** opt-out requires explicit human declaration in the same message - agents cannot grant it retroactively.

### CO3 - Documentation updates

If the iteration surfaced documentation gaps:

- **SPEC amendment** → create `{FEATURE_SPEC_ROOT}/<context>/YYYYMMDD-SPEC-amendment-NN.md`. Do not edit a merged SPEC.
- **Full Plan gap** → note in HANDOFF; recommend `@plan-master revise - <reason>`.
- **Foundation gap** → note in HANDOFF; recommend `@plan-foundation continue` (rare - only for structural omissions).
- **New assumptions / risks / unknowns surfaced** → append to `{PLANS_ROOT}/ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md` respectively.

Do not edit archived decision prompts.

### CO4 - NEXT.md update

1. Set iteration block `**Status:** complete`.
2. Move all task rows to `### Done this iteration` with completion dates.
3. Set `## Recommended next` to the next milestone: `@code-implementation plan - M{N+1}` or the first task of M{N+1} if already scoped.
4. Clear the `## Current iteration` body or replace with a one-line reference: `M{N} complete - see Done section.`

### CO5 - HANDOFF update

Append to `## What this cycle produced`:
- Row per new file created.
- Row per existing file significantly modified.

Refresh `## Repository state` with current truth: which milestones are done, what is next, any owner actions pending.

### CO6 - Close report

```markdown
## code-implementation complete - M{N}: {name}

**Date:** {ISO date} · **Branch:** {branch}

### Completion checklist
| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | All tasks done | pass/fail | T{list} |
| 2 | Full test suite pass (or skip - covered by CO2) | pass/fail/skip | exit 0 |
| 3 | Lint/type-check pass (or skip - covered by CO2) | pass/fail/skip | |
| 4 | Verify pass (CO2; or gaps waived) | pass/fail/waived | verdict |
| 5 | No secrets in diff | pass/fail | |
| 6 | Scope discipline enforced | pass/fail | git diff |
| 7 | Schema changes via migrations | pass/skip | |
| 8 | SPEC amendments written (if needed) | pass/skip | paths |
| 9 | NEXT.md updated | pass/fail | |
| 10 | HANDOFF updated | pass/fail | |

### Commit message (draft - always present)
{per .cursorrules format}

### Follow-ups before next iteration
{ordered list}

### Next
{from NEXT.md - Recommended next}
```

---

## Blocked task protocol

When a task cannot proceed mid-implementation:

1. Mark task status `blocked` in the iteration block.
2. Record blocker in `### Owner blockers` and in `{PLANS_ROOT}/UNKNOWNS.md` (owner = "human" or named role; `blocks: T{N}`).
3. If the blocker is an ambiguity in SPEC or Full Plan → add to UNKNOWNS; surface in next status report; ask the user once.
4. Move to the next non-blocked pending task (if one exists).
5. If all tasks are blocked → do not hallucinate a resolution. Recommend `@session-control close` with the blockers listed explicitly.
6. Do not invent owner-decision resolutions. Pause and ask.

---

## Integration with other skills

| Skill | Integration |
|-------|-------------|
| `session-control` | Run `@session-control start` before `code-implementation start`; run `@session-control close [commit]` after `code-implementation complete` |
| `plan-master` | Source of milestones; use `@plan-master status` to confirm implementation-ready; `@plan-master revise` if plan gaps surface |
| `code-verify` | **milestone** (CO2) before **complete**; **uncommitted** / **last** optional pre-commit / post-push cadence; task gate runs inline checks - does not delegate to verify |
| `plan-foundation` | Rarely invoked during implementation; only when **milestone** verify surfaces a structural foundation gap |
| `db-migration` | Mandatory for any schema change; stop task, run `@db-migration create`, resume after migration script exists |
| **Concept pack** | Run applicable `prompt.md` during **`@code-verify milestone`**; **MOD-06 required** before **complete** when code changed; attach outputs to PR or `NEXT.md` |

---

## Anti-patterns

*(Behaviors not covered by Hard rules above; Hard rules are not restated here.)*

- Writing code without reading the relevant SPEC(s) first - the read precedes the edit.
- Reporting "tests pass" without running them and reviewing output.
- Skipping the task gate because "it's a small change."
- Skipping **SC1 self-critique** because the task "looked simple".
- Claiming a fix succeeded without **re-gating** the affected task(s).
- Skipping the **Batch-end sweep** at end of `continue` (single-task or batch).
- Proceeding to complete without `@code-verify milestone`.
- Skipping the **Concept / NFR registry** subsection in the active iteration when a concept pack is documented in agent rules.
- Skipping **MOD-06** by self-classifying an agent session as non-AI.
- Passing **Observability** in `@code-verify milestone` without checking SPEC §9 fields on touched code paths.
- Inventing a resolution for an owner-decision blocker.
- Editing merged SPECs or archived decision prompts during implementation.
- Logging PII (emails, tax IDs, amounts) in structured log events.
- Adding attribution comments ("Generated by…", "Created by AI").
- Marking implementation-ready in this skill (that is `@plan-master status`).

---

## Completion checklist (all modes)

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Mode detected correctly | pass/fail | |
| 2 | NEXT.md iteration block valid | pass/fail | criteria |
| 3 | SPEC(s) read before implementation | pass/skip | paths |
| 4 | CONVENTIONS + FEATURE_STANDARD read | pass/skip | |
| 5 | Task gate passed per task | pass/fail | exit codes |
| 5b | SC1 self-critique recorded per task | pass/fail | bullets in Notes |
| 5c | Post-fix re-gate executed (if any fix applied) | pass/skip | task ids re-gated |
| 6 | No out-of-scope files modified | pass/fail | git diff |
| 7 | No secrets in output | pass/fail | |
| 8 | Schema changes via db-migration | pass/skip | |
| 8b | Batch-end sweep run (continue mode) | pass/fail/skip | sweep verdict |
| 9 | `@code-verify milestone` (complete mode) | pass/skip | verdict |
| 10 | NEXT.md + HANDOFF updated (complete mode) | pass/skip | |
