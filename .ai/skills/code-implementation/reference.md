# code-implementation - reference

Supplement to `skill.md`. Invocation examples, NEXT.md templates, mode comparison, and edge cases.

---

## How to invoke

### Cursor

```
@code-implementation status
@code-implementation plan - M1
@code-implementation start
@code-implementation continue
@code-implementation continue - 5
@code-implementation continue - until blocked
@code-implementation continue - M4-T2..T6
@code-implementation complete
@code-verify milestone
@code-verify uncommitted
@code-verify last
```

Legacy aliases (still accepted):

```
@code-implementation plan-iteration - M1   # alias of "plan"
@code-implementation verify                # routes to @code-verify
@code-implementation verify uncommitted    # routes to @code-verify
@code-implementation task T3
```

### Claude Code / opencode / Codex

```
Follow .ai/skills/code-implementation/skill.md - status. Read-only.
```

```
Follow .ai/skills/code-implementation/skill.md - plan - M1.
Derive iteration block from plan-master and write it to NEXT.md.
```

```
Follow .ai/skills/code-verify/skill.md - uncommitted.
Diff-only audit: secrets, scope, tests/lint/type on changed files.
```

---

## Mode comparison

| | status | plan | start | continue | complete | task |
|---|--------|------|-------|----------|----------|------|
| Read NEXT.md | yes | yes | yes | yes | yes | yes |
| Write NEXT.md | no | yes | no | task status | yes | task status |
| Write HANDOFF | no | no | no | no | yes | no |
| Run tests/lint | no | no | no | per task (task gate) | CO2 then CO1 if needed | yes (task gate) |
| Run verify | - | - | - | optional `@code-verify uncommitted` | `@code-verify milestone` (CO2) | - |

**Continue batch targets:** omit `-` → 1 task; `- N` → up to N tasks or until stop; `- until blocked` → no cap; `- M4-T2..T6` → inclusive range. All modes stop on gate fail or blocker (same as "next N tasks or until failed").

**Three check layers:** **task gate** (mechanical, every task) · **`@code-verify uncommitted` / `last`** (diff audit, optional cadence) · **`@code-verify milestone`** (plan + SPEC matrix, before **complete**). Use **`code-verify`** skill for all verify modes.

---

## Typical session flow

```
@session-control start - implement M1 platform skeleton
@code-implementation status     ← check if iteration block exists
@code-implementation plan - M1  ← if block missing or invalid
@code-implementation start      ← load context, begin T1
@code-implementation continue - 5   ← up to 5 tasks, or stop on fail/blocker
@code-implementation continue - until blocked
@code-implementation status     ← progress check between batches
@code-verify milestone          ← approaching completion
@code-verify uncommitted        ← before commit
@code-verify last               ← after commit/push
@code-implementation complete   ← finalize + update HANDOFF/NEXT
@session-control close commit   ← commit and close session
```

---

## Quick invocation reference

| Goal | Prompt |
|------|--------|
| What tasks remain? | `@code-implementation status` |
| Generate iteration scope for M2 | `@code-implementation plan - M2` |
| Start fresh on current iteration | `@code-implementation start` |
| Resume one task | `@code-implementation continue` |
| Resume next N tasks (stop on fail/blocker) | `@code-implementation continue - 5` |
| Resume until gate fail or blocker | `@code-implementation continue - until blocked` |
| Resume explicit task range | `@code-implementation continue - M4-T2..T6` |
| Run a specific task (shorthand, active iteration) | `@code-implementation task T4` |
| Run a specific task (globally unique ID) | `@code-implementation task M1-T4` |
| Look up what a task requires (read-only) | `@plan-master show M1-T4` |
| See all tasks for a milestone | `@plan-master show M1` |
| Check work against Full Plan | `@code-verify milestone` |
| Audit uncommitted diff only | `@code-verify uncommitted` |
| Audit last commit or push | `@code-verify last` |
| Wrap up iteration | `@code-implementation complete` |
| Visual task matrix | `@code-implementation status` (datagrid/canvas) |

---

## Example milestone map (illustrative)

Validate with `@plan-master status` and the **approved** `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md` task section - do not copy this table into a live project without aligning to your master plan.

| Milestone | Name (example) | Key artifacts |
|-----------|----------------|---------------|
| M1 | Platform skeleton | CONVENTIONS, DIRECTORY_MAP, health route, migration runner |
| M2 | Core domain module A | `<slug-a>/SPEC` |
| M3 | Core domain module B + API stubs | `<slug-b>/SPEC` |
| M4 | External integration shell | integration SPEC + `docs/integration/MANIFEST.txt` |
| M5 | Integration E2E (sandbox) | Same SPEC + runbook |
| M6 | Frontend shell (if any) | UI conventions |

---

## NEXT.md iteration block - quick template

```markdown
## Current iteration - M1: platform skeleton (example)

**Milestone ref:** M1 · `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md` (task section)
**Status:** in-progress
**Started:** YYYY-MM-DD

### In scope
- App manifest, `REPLACE:PLATFORM_PACKAGE/` layer, health route, idempotent migration runner, dev entrypoint (per master plan M1)

### Out of scope (explicit)
- Business domain tables (later milestones)
- Optional frontend (later milestone)

### Tasks
| ID | Description | Files | Status | Notes |
|----|-------------|-------|--------|-------|
| M1-T1 | App dependency manifest | `REPLACE:APP_ROOT/...` | pending | |
| M1-T2 | Platform settings | `REPLACE:PLATFORM_PATH/settings.*` | pending | |
| M1-T3 | Database bootstrap | `REPLACE:PLATFORM_PATH/database.*` | pending | |
| M1-T4 | Migration runner + `001_init.sql` | runner + `REPLACE:MIGRATIONS_DIR/001_init.sql` | pending | |
| M1-T5 | HTTP health + lifespan migrations | app entry `main.*` | pending | |

### Acceptance criteria
- [ ] Dev stack healthy; `curl /health` → 200
- [ ] Migration runner idempotent on restart
- [ ] Task gate from `.cursorrules` passes

### Validation steps
- [ ] Commands from `.cursorrules` § Docker / verification (test, lint, type)
- [ ] Manual: health URL on host port from `.env` / dev-stack script

### Owner blockers
- none

### Concept / NFR registry (this iteration)
<!-- Required by skill.md § Valid iteration block criteria #6.
     One row per MOD-01…MOD-06 (or single `N/A - no pack` row if the repo has no concept pack). -->
| Concept id | Applies | Status | Evidence / trigger |
|------------|---------|--------|-------------------|
| MOD-01 | yes/no | pending/done/n-a | … |
| MOD-02 | yes/no | pending/done/n-a | … |
| MOD-03 | yes/no | pending/done/n-a | … |
| MOD-04 | yes/no | pending/done/n-a | … |
| MOD-05 | yes/no | pending/done/n-a | … |
| MOD-06 | **yes** | pending | Cursor/agent session - required before complete unless human-only |

### Cross-LLM verification
- Triggered: no

### Done this iteration
| Task | Completed | Notes |
|------|-----------|-------|
```

---

## Status output examples

### Text progress bar

```
████████░░ 80% (7 / 9 tasks done)   ← illustrative only
```

### Compact datagrid (illustrative - not live status)

```
## M1 - platform skeleton - in-progress (example)

| ID    | Task                                | Status (example) |
|-------|-------------------------------------|------------------|
| M1-T1 | app manifest                        | done             |
| M1-T2 | platform settings                   | done             |
| M1-T4 | migration_runner + 001_init.sql     | pending          |
| M1-T5 | main + /health                      | pending          |

Verify: not yet triggered
Owner blockers: none
```

### Canvas (when available)

Render the task matrix in a canvas with colour-coded status cells (done=green, in-progress=blue, blocked=red, pending=grey) and an animated progress bar. See the canvas skill for setup.

---

## Cross-LLM verification - prompt template

When triggering cross-LLM verification, use this compact prompt format:

```
Milestone: M{N} - {name}
Objective: {one paragraph from plan-master §19}

Tasks implemented:
- T1: {description} - Files: {list}
- T2: …

SPEC rules in scope (R1…):
{paste numbered rules from the relevant SPEC}

Review for:
1. {highest-risk gap from V2}
2. {second highest-risk gap}
3. {third}

Return: pass | fail | gaps-found, with specific file/rule citations.
```

---

## Integration with session-control

| Event | code-implementation action |
|-------|-----------------------|
| `session-control start` | Optional: run `@code-implementation status` to see current iteration before beginning |
| Interruption mid-task | Run `@session-control close` - HANDOFF notes "in-flight: T{N}" |
| `session-control close commit` | After `code-implementation complete`, provides the draft commit message |

---

## Edge cases

| Situation | Behavior |
|-----------|----------|
| NEXT.md has no `## Current iteration` | Run `plan` before start |
| Iteration block exists but milestone not in plan-master | Block is invalid; re-run `plan` with correct milestone |
| Master plan not Approved but HANDOFF has M1 waiver | Proceed with `plan - M1`; note waiver in start report |
| Schema change discovered mid-task | Stop task; run `@db-migration create`; resume after migration exists |
| Task T3 depends on T2 which is blocked | Mark T3 `blocked (depends on T2)`; surface both in status |
| All tasks done but test suite fails | Do not run complete; fix failing tests; re-run gate |
| Verify returns `fail` | Fix all high/med gaps; re-run verify; only skip low gaps with waiver |
| User asks for implementation-ready check | Redirect: `@plan-master status` - not code-implementation |
| Second model unavailable for cross-LLM (M1–M3) | Log `skipped - single-model session`; does not block complete |
| Second model unavailable for cross-LLM (**high-risk milestone** per threat model) | **fail** unless owner records a **human architect review** waiver in `{HANDOFF}` (name + date) per `code-verify` |
| Cursor/agent session: MOD-06 skipped | **fail** at CO1; run `@concept-run - MOD-06` or attach output before complete. **`human-only`** opt-out requires explicit human declaration in the same message |
| Protected file change needed | Stop; explain why; ask explicit permission; only proceed after yes |
| `continue - 5` and task 3 gate fails | Batch stops at task 3; tasks 4–5 not started |
| `continue - until blocked` and all tasks pass | Runs entire remaining queue; then recommend **complete** |
| `continue - M4-T2..T6` but T4 already `done` | Queue is T2, T3, T5, T6 only (skip done) |
| User says "implement next 5 tasks" | Same as `continue - 5` |

---

## Wrong prompts

| Prompt | Problem | Use instead |
|--------|---------|-------------|
| `@code-implementation start` with no NEXT.md iteration block | No scope | `plan - M{N}` first |
| `@code-implementation start` when implementation-ready: no | Prerequisite | `@plan-master status`; HANDOFF waiver or approve plan |
| `@plan-master greenfield` when plan-master-ready: no | Prerequisite | `@plan-foundation certify` first |
| `@code-implementation complete` with failing tests | Violates gate | Fix tests; rerun gate |
| Marking task done without running tests | Violates hard rule | Run task gate |
| `@code-implementation` for planning-only work | Wrong skill | `@plan-master continue` |
| Asking code-implementation if plan is "implementation-ready" | Wrong skill | `@plan-master status` |
| Running verification on host when `.cursorrules` requires containers | Wrong environment | Follow `{AGENT_RULES_FILE}` § Docker |

---

## Optional slash commands (team convention)

| Command | Maps to |
|---------|---------|
| `/impl status` | status |
| `/impl plan M1` | plan - M1 |
| `/impl start` | start |
| `/impl continue` | continue |
| `/impl continue 5` | continue - 5 |
| `/impl continue M4-T2..T6` | continue - M4-T2..T6 |
| `/impl done` | complete |
| `/impl verify` | `@code-verify milestone` (legacy: routes via `code-verify` skill) |

Document in project README if adopted.
