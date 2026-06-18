---
name: code-verify
description: >-
  Run implementation verification gates: milestone, uncommitted, last commit/push,
  or read-only status. Accepts explicit modes or open-language requests mapped to
  implementation context (.cursorrules, NEXT, SPECs, plan §19). Tool-agnostic;
  verification commands from .cursorrules.
---

# code-verify

Verification layer for the implementation workflow. **Does not implement features** and **does not** own `NEXT.md` iteration planning (that is `code-implementation`).

**Pairs with:** `code-implementation` (task gates + calls milestone verify before **complete**), `session-control` (pre-commit), `concept-run` (MOD rows in milestone verify), `.cursorrules` Completion Gate.

**Canonical path:** `.ai/skills/code-verify/skill.md` · **Invocation examples:** `reference.md`

**Hard rules:**

- **Evidence-first** - cite file paths, `git` output, and command exit codes; never claim pass without output.
- **Verification commands** from `{AGENT_RULES_FILE}` § Docker or local/CI section (same as `code-implementation`).
- **Secrets scan** is mandatory on every mode that inspects a diff.
- **No HANDOFF/NEXT writes** except optional update to `### Cross-LLM verification` when user explicitly asks to record milestone verify result.
- **Protected files** (`.cursorrules` §Protected Files): modified in diff without owner permission → **fail**.
- **AI-assisted default:** Diffs from Cursor/agent sessions are AI-assisted unless the human declared **`human-only`** in the same message. MOD-06 **fail** (not `skip`) when code changed and no MOD-06 output path is cited.
- **Open language** — when the user does not name an explicit mode, emit a [Request interpretation](#open-language-interpretation-free-requests) block before running the protocol; map intent to `milestone` | `uncommitted` | `last` | `status`.
- Every mode ends with a **Completion checklist** - each item `pass` | `fail` | `skip` with evidence.

---

## Parse invocation

Normalize to **mode** + optional scope. Use ASCII hyphen **`-`** between tokens.

| User says | Mode | Action |
|-----------|------|--------|
| `@code-verify` **milestone** | milestone | [Milestone verify](#milestone-verify-protocol) - alias of legacy full **verify** |
| `@code-verify` **verify** | milestone | Same as **milestone** (default if bare `@code-verify` and iteration active) |
| `@code-verify` **uncommitted** | uncommitted | [Uncommitted verify](#uncommitted-verify-protocol) |
| `@code-verify` **last** | last | [Last verify](#last-verify-protocol) |
| `@code-verify` **status** | status | [Status protocol](#status-protocol) - read-only; suggests verify mode |
| `code-verify` **last commit** | last | Same as **last** |
| `code-verify` **last push** | last | Same as **last** (mode resolves which event was later) |
| `@code-implementation` **verify** | milestone | **Legacy** - run this skill **milestone** mode |
| `@code-implementation` **verify** **uncommitted** | uncommitted | **Legacy** - run **uncommitted** mode |
| Open language (see below) | *(infer)* | [Open language interpretation](#open-language-interpretation-free-requests) → then protocol |

**Open language → mode hints** (non-exhaustive; confirm via interpretation block):

| User intent (examples) | Likely mode |
|------------------------|-------------|
| "safe to commit", "before commit", "audit my changes", "dirty tree", "pre-commit" | **uncommitted** |
| "last commit", "what I pushed", "post-push", "after commit" | **last** |
| "milestone", "iteration done", "ready to complete", "SPEC matrix", "M2 coverage" | **milestone** |
| "what should I verify?", "where am I in implementation?" | **status** |
| "fix lint/tests" only (no verify keyword) | Route to `@code-repair` — not code-verify |

**Aliases:** `audit`, `check` → **uncommitted** if working tree dirty, else **last** if clean and synced, else ask once; `gate` → **uncommitted** before commit.

**Default:** bare `@code-verify` → **milestone** when `NEXT.md` has active `## Current iteration`; else **uncommitted** if tree dirty; else **last**; if ambiguous after interpretation → ask once.

When mode is explicit (e.g. `@code-verify uncommitted`), skip the interpretation block and record: `**Request:** explicit mode — no interpretation needed`.

---

## Open language interpretation (free requests)

**When:** The user message does **not** contain an explicit mode keyword (`milestone`, `uncommitted`, `last`, `status`, `verify`) — or the keyword appears inside a free-form sentence (e.g. "check if my changes are safe to commit", "audit the last push").

Before running any protocol, emit a **Request interpretation** block:

```markdown
### Request interpretation

**User said:** <raw text or one-line paraphrase>

**Detected mode:** milestone | uncommitted | last | status
**Mapped via:** <keyword match | default inference | git/NEXT state>
**Implementation context examined:**
| Component | Path / source | Why |
|-----------|---------------|-----|
| Agent rules | `.cursorrules` | Test/lint/type commands, protected files, Docker |
| Iteration | `{ITERATION_CARRIER}` § Current iteration | Scope (S2), milestone id |
| Master plan §19 | `{PLANS_ROOT}/full/*-full-plan.md` | FR/NFR trace (milestone mode) |
| SPECs | `{FEATURE_SPEC_ROOT}/<slug>/*-SPEC.md` | R1… rules for touched contexts |
| Standards | `.ai/standards/*CONVENTIONS*`, `*FEATURE_STANDARD*` | Invariants, naming |
| Boundary map | `.ai/standards/*DIRECTORY_MAP*` or `{BOUNDARY_MAP}` | Cross-context edits |
| Concepts | `.ai/concepts/README.md` § Trigger table | MOD-06 (AI-assisted), MOD-01 (boundaries) |
| HANDOFF | `{HANDOFF}` | Waivers, high-risk milestone review |
| Git state | `git status`, diff range | uncommitted / last event |

**Assumption ledger:** <Confirmed | Inference | Unverified> for mode choice and scope
```

**Rules:**

- Emit **once** before the mode protocol; include in the report header (see report formats below).
- Unambiguous mapping (e.g. "before I commit" → **uncommitted**) → label mode **Confirmed**.
- Ambiguous (e.g. "verify my work") → label **Inference**, run **status** or ask once.
- No valid iteration and user asks milestone-level audit → **Inference**: recommend `@code-implementation plan - M{N}` first; may still run **uncommitted** on dirty tree.

**No iteration / informal implementation (code brownfield):** When `{ITERATION_CARRIER}` lacks `## Current iteration` but the tree is dirty → prefer **uncommitted**; cite missing iteration as **Med** gap in report; do not claim milestone **pass** without iteration block.

---

## Shared prerequisites

| # | Read / run | When |
|---|------------|------|
| 1 | `{ITERATION_CARRIER}` (`NEXT.md` §Current iteration) | milestone, scope checks on uncommitted/last |
| 2 | `.cursorrules` §Protected Files, §Secret Scrubbing | all modes with a diff |
| 3 | `git fetch origin` (best effort) | **last** mode, milestone FR traceability |

---

## Shared gates (verification)

Same commands as `code-implementation` task gate (`.ai/skills/code-implementation/skill.md` § Task gate): read `{AGENT_RULES_FILE}` for `REPLACE:TEST_COMMAND`, `REPLACE:LINT_COMMAND`, and `REPLACE:TYPECHECK_COMMAND`.

Run when diff touches application source or tests per `{BOUNDARY_MAP}` / DIRECTORY_MAP (skip with reason if not).

**Honesty:** Commands run against the **current workspace**, not a detached checkout, unless **last** mode used a worktree (optional, see [Last verify](#last-verify-protocol)).

---

## Shared: secrets scan (S1)

On `git diff …` / `git show` for the active range:

- **Fail** if paths match: `credentials/`, `.env`, `.env.*` (except `.env.example`), `*.pem`, `*.p12`, `*.key`, `*.pfx`, `*.p8`, `*id_rsa*`, `*.token`, `*.secret`
- Review patch hunk content for keys, tokens, passwords, PEM material

---

## Shared: scope discipline (S2)

When `NEXT.md` has a valid `## Current iteration` block:

- Collect declared file paths from all task rows (comma-separated in **Files** column).
- Flag any changed path not in that union: `out-of-scope - <reason>`
- Infra fixes (e.g. `docker-compose.yml`) outside iteration → flag **Med**; do not auto-pass

---

## Shared: protected files (S5)

Per `{AGENT_RULES_FILE}` §Protected Files - **fail** if the diff touches any listed path without documented owner permission in HANDOFF or explicit user approval in the session.

Infra paths changed for iteration work still require explicit owner approval - flag **High** in milestone verify; **fail** in **uncommitted** / **last** before commit.

---

## Milestone verify protocol

Deep cross-check of the **active iteration** vs master plan and SPECs. Use before `@code-implementation complete`, when ≥80% of iteration tasks are done, or on user request.

### M0 - Milestone existence gate

Before M1 (evidence gathering):

1. Resolve target milestone:
   a. If user provided `milestone - M{N}`, use that explicit `M{N}`.
   b. Else read `{ITERATION_CARRIER}` `## Current iteration` header `M{N}`.
2. Check the milestone exists:
   a. In `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md` §19 (Approved or Draft), **or**
   b. In `{ITERATION_CARRIER}` `## Current iteration` block (valid per `code-implementation` skill).
3. If neither location records this `M{N}` → **stop** with the [blocked-report shape](#blocked-report-shape):
   - **Required:** `M{N}` defined in master plan §19 or active in `{ITERATION_CARRIER}` `## Current iteration`
   - **Detected:** `M{N}` not present in either source (ghost milestone)
   - **Run first:** `@plan-master show M{N}` (does it exist? alias: `task`) - if not, `@plan-master revise - add M{N}` or correct the milestone number; if it exists in the plan but no iteration block, `@code-implementation plan - M{N}`

### Blocked-report shape

Per [SKILL_DEPENDENCIES.md § Blocked report shape](../SKILL_DEPENDENCIES.md#blocked-report-shape) - header: `## @code-verify <command> - blocked (prerequisite)`.

### M1 - Gather evidence

1. `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md` §19 (milestone), §20–§21 as needed.
2. Relevant SPEC(s) R1… for bounded contexts touched in the iteration.
3. `{PLANS_ROOT}/foundation/YYYYMMDD-04-*.md` §13 ADR register (contexts touched).
4. Changed files on branch: `git diff --name-only <base>...HEAD` (default base: `main` or `origin/main` if exists).

### M2 - Check matrix

| Dimension | Question | Result |
|-----------|----------|--------|
| FR coverage | Every FR for this milestone has ≥1 test or honest gap? | pass / fail / gap |
| SPEC rules | R1… implemented or deferred with owner? | pass / fail / gap |
| ADR alignment | Contradicts Decided ADR? | pass / fail / conflict |
| Scope discipline | Files outside milestone/iteration tasks? | pass / fail |
| Schema | Migrations only (no inline DDL)? | pass / fail / skip |
| Invariants | SPEC/CONVENTIONS invariants on touched code? | pass / fail |
| Security | No PII in logs; no secrets in diff? | pass / fail |
| Test coverage | Happy path + key errors for touched code? | pass / partial / fail |
| Observability | SPEC §9 + observability spec on touched paths? | pass / fail / gap / skip |
| Concept / NFR registry | `Applies=yes` not left `pending`? | pass / fail / gap |
| Coupling / blast | Cross-boundary edits per concept pack rules? | pass / fail / gap / skip |
| AI-assisted safety | MOD-06 output attached when iteration touched application source/tests? | pass / fail / gap - **`skip` forbidden** when code changed; **`human-only`** opt-out requires explicit human declaration |
| Docs alignment | Matches plan-master task text? | pass / drift |

### M3 - Cross-LLM

If a second model is available: focused prompt (milestone objective, tasks, R1…, top 3 risks). Record in `NEXT.md §Cross-LLM verification` when user wants it persisted.

**Single-model sessions:**

| Milestone scope | Result | Requirement |
|-----------------|--------|-------------|
| Early milestones (platform, fixtures, domain stubs) | `skipped - single-model session` | Note in milestone report only |
| Milestones touching **high-risk modules** (per threat model / `.cursorrules`) | **fail** unless waived | Owner must document **human architect review** in `{HANDOFF}` (name + date) or run cross-LLM before **complete** |

Waivers for high-risk milestones do not carry forward to the next high-risk milestone.

### M4 - Milestone report

```markdown
## code-verify milestone - M{N}: {name}

**Date:** {ISO} · **Triggered by:** {reason}
<when open language — insert ### Request interpretation block; else: **Request:** explicit mode>

### Check matrix
| Dimension | Result | Evidence / gap |
|-----------|--------|----------------|

### Gaps
{ordered - severity High/Med/Low}

### Cross-LLM
{result}

### Verdict
**pass** | **pass with gaps** | **fail** - {one sentence}

### Next step
- pass / pass with gaps (waived): `@code-implementation complete` allowed if tasks done + CO1 gates pass
- fail: `@code-repair repair - from milestone` (or `@code-implementation continue` + fix gaps)
```

---

## Uncommitted verify protocol

Diff-only audit of the **working tree** - no master-plan reads.

### U1 - Gather diff

```bash
git status -sb
git diff --stat
git diff --cached --stat
git diff --name-only
git diff --cached --name-only
```

If clean → report `clean` and **stop** (verdict: pass - nothing to audit).

### U2 - S1 secrets, S2 scope, S5 protected files

### U3 - Shared verification gates (if application source/tests touched)

### U4 - Report

```markdown
## code-verify uncommitted

**Date:** {ISO} · **Branch:** {branch} · **Tree:** dirty
<when open language — insert ### Request interpretation block; else: **Request:** explicit mode>

### Diff summary
| Path | Status | In scope? |

### Checks
| Check | Result | Evidence |

### Verdict
**pass** | **fail**

### Next step
- pass: safe to commit (`@session-control close commit`)
- fail: `@code-repair repair - from uncommitted` (or fix manually), then re-run `@code-verify uncommitted`
```

---

## Last verify protocol

Audit the **most recent publish event**: the latest **local commit** or the latest **push** to `@{upstream}`, whichever happened **last** (by reflog timestamp).

### L1 - Resolve last event

```bash
git fetch origin 2>/dev/null || true
git status -sb
UPSTREAM=$(git rev-parse --abbrev-ref @{u} 2>/dev/null || echo "")
HEAD_SHA=$(git rev-parse HEAD)
```

| Condition | Last event | Diff range | Notes |
|-----------|------------|------------|-------|
| No `@{u}` | commit | `HEAD~1..HEAD` | First commit: `git diff --root HEAD` |
| `HEAD` **ahead** of `@{u}` | **commit** | `@{u}..HEAD` | All unpushed commits |
| `HEAD` **behind** `@{u}` | - | - | **fail** - pull/rebase first |
| `HEAD` **==** `@{u}` (synced) | **push** | `HEAD~1..HEAD` | Single tip commit delivered by push |
| Merge commit as `HEAD` | commit or push | `HEAD^1..HEAD` | Use first parent for range |

**Timestamp tie-break** (optional, when ahead 0 but user insists on temporal order):

```bash
git log -1 --format=%ct HEAD
git reflog show -1 --format=%ct "${UPSTREAM}" 2>/dev/null || echo 0
```

If commit timestamp > upstream reflog timestamp → treat as **commit** range `HEAD~1..HEAD`; else **push** range as synced row above.

### L2 - Gather diff for range

```bash
git diff --stat <range>
git diff --name-only <range>
git log -1 --oneline <end-sha>
git show --stat -1 <end-sha>
```

### L3 - S1 secrets on range; S2 scope; S5 protected files

### L4 - Push alignment (informational)

| Check | Result |
|-------|--------|
| Unpushed commits | `git log @{u}..HEAD --oneline` if ahead |
| Matches remote | `HEAD` == `origin/<branch>` after fetch |

### L5 - Shared Docker gates

If working tree **dirty**, note: **tests reflect workspace, not only the resolved range** - recommend clean tree or stash for strict replay.

### L6 - Light matrix (optional)

Only rows relevant to files in range (security, scope, test coverage partial) - **not** full milestone FR sweep.

### L7 - Last report

```markdown
## code-verify last

**Date:** {ISO} · **Last event:** commit | push · **Range:** `{range}` · **Commit:** `{sha}` `{subject}`
<when open language — insert ### Request interpretation block; else: **Request:** explicit mode>

### Push state
{ahead/behind/synced - N unpushed}

### Diff summary
| Path | In scope? |

### Checks
| Secrets | pass/fail |
| Scope | pass/fail |
| Protected files | pass/fail |
| Tests | pass/fail/skip |
| Lint | pass/fail/skip |
| Type | pass/fail/skip |

### Verdict
**pass** | **fail**

### Next step
- pass: commit/push is auditable; continue iteration or `@session-control close`
- fail: `@code-repair repair - from last` (or fix manually), then re-run `@code-verify last`
```

---

## Status protocol

Read-only. No writes to HANDOFF/NEXT unless user asks.

1. `git status -sb` · infer dirty vs clean.
2. `{ITERATION_CARRIER}` — active `## Current iteration`? milestone id?
3. Last `@code-verify` mention in chat if visible.

```markdown
## code-verify status

**Tree:** clean | dirty (<N> files)
**Iteration:** M{N} active | none
**Last event hint:** commit ahead | synced | no upstream

**Suggested verify:** @code-verify uncommitted | last | milestone
**Request:** <explicit status mode — or open-language interpretation if user asked a question>
```

---

## Completion checklist (all modes)

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Mode detected | pass/fail | |
| 2 | Request interpretation (open language) | pass/skip | block in report |
| 3 | Shared reads / git evidence | pass/fail | paths, exit codes |
| 4 | Check matrix or diff checks complete | pass/fail | |
| 5 | Verdict matches evidence | pass/fail | |
| 6 | Next step names exact command | pass/fail | |
| 7 | No implementation edits in verify mode | pass | |

---

## Integration

| Skill | Use |
|-------|-----|
| `code-implementation` | **Auto-invokes `@code-verify uncommitted`** at end of every `continue` batch (see `code-implementation` § Batch-end sweep) - not optional. Also calls **milestone** before **complete** (CO2); task gate runs inline mechanical checks. On sweep **fail** → `@code-repair repair - from uncommitted`. |
| `code-repair` | **Downstream remediator** - on any mode **fail**, recommend `@code-repair repair - from <same mode>` or `repair - custom - …` for free-text fixes. Does not auto-invoke. |
| `plan-verify` / `plan-repair` | **Planning layer** - plan doc gaps are not code-verify scope; use `@plan-verify` then `@plan-repair` |
| `session-control` | **uncommitted** or **last** before `close commit` |
| `concept-run` | Clear MOD rows before milestone **pass** |

Registry: `SKILL_DEPENDENCIES.md` § Self-verify auto-invoke.

---

## Anti-patterns

- Using **milestone** for a single-commit pre-push check → use **last** or **uncommitted**
- Using **uncommitted** when tree is clean → use **last** or report clean
- Claiming tests validated an old commit while tree has extra uncommitted changes (without saying so)
- Skipping secrets scan on **last** because "it was already pushed"
- Full milestone matrix on every task (too heavy - use **uncommitted**)
- Marking MOD-06 **skip** on agent-authored diffs - use **fail** or attach output
- Accepting `Confirmed` assumptions in implementation reports without file or test cite
- Running open-language verify without a **Request interpretation** block
- Claiming milestone **pass** with no `## Current iteration` block (use uncommitted + gap note)
