---
name: session-control
description: >-
  Open or close an AI working session with verified context load, HANDOFF and NEXT
  updates, and optional git commit/push. Also supports standalone commit/push
  without closing (commit task ref, git add + git commit + git push, no
  HANDOFF/NEXT update). Use when the user says session-control start, session-control
  close, @session-control start, close commit, close commit push, commit, or commit push.
  Never commits unless the invocation includes commit. On commit, MUST run
  git add + git commit in the shell for all safe dirty paths (not HANDOFF-only).
---

# session-control

Bookend AI work sessions so the next chat (or human) can resume without guessing. **Tool-agnostic**; **project-agnostic** when `{HANDOFF}` exists.

**Pairs with:** `.cursorrules`, `plan-foundation` skill (optional status on start/close), `{ITERATION_CARRIER}`.

**Registry:** [`.ai/skills/SKILL_DEPENDENCIES.md`](../SKILL_DEPENDENCIES.md).

**Canonical path:** `.ai/skills/session-control/skill.md` · **Invocation examples:** `reference.md`

**Hard rules:**

- **Default close / default commit:** never `git commit` or `git push`. Only when invocation includes **`commit`** and/or **`push`** (see [Parse invocation](#parse-invocation)).
- **`close commit` / `close commit push` / `commit` / `commit push`:** **MUST** run `git add` + `git commit` in the shell (see [C4b](#c4b--git-actions-modifiers-only) / [Commit protocol](#commit-protocol)). A dirty tree after close with only a draft message is **fail**.
- **Always** show the commit message - drafted, used for commit, or `none - working tree clean`.
- **`commit` / `commit push` (standalone):** run git add + commit + push **without** updating HANDOFF or NEXT. Session stays open. Useful for mid-session checkpoints.
- **Never commit with `type:` format when a task ref is known or could reasonably be asked for.** If the user provided a ref, or the branch/HANDOFF/github-registry contains one — use it. If no ref is known but the work clearly belongs to a task, ask the user once. Commits without refs are not linked to tasks/tickets and are invisible in the association UI.
- Never edit files marked **archived** or **do not edit** in HANDOFF.
- Never paste secrets from `.env`, `credentials/`, or tokens into chat or HANDOFF.
- **`{PROMPTS_ROOT}/initial.md` is user-owned.** Do not read or create it on start/close unless the user explicitly names that path in the same invocation.
- Every mode ends with a **Completion checklist** - each item `pass` | `fail` | `skip` with evidence.

### Path resolution (mandatory before any Read)

Resolve from **repository root** (see [`SKILL_DEPENDENCIES.md`](../SKILL_DEPENDENCIES.md) § Work tree path resolution). `{WORK_ROOT}` = **`.work/`** — not the repo root.

| Artifact | Read / write this path |
|----------|-------------------------|
| `{HANDOFF}` | `.work/context/HANDOFF.md` |
| `{ITERATION_CARRIER}` | `.work/plans/NEXT.md` |
| `{PLANS_ROOT}/UNKNOWNS.md` | `.work/plans/UNKNOWNS.md` |

**Never** open `context/HANDOFF.md`, `plans/NEXT.md`, or bare `HANDOFF.md` / `NEXT.md` at repo root — those paths are wrong for Agent OS.

---

## Parse invocation

Normalize the user message to **verb** + optional **modifiers**. The word `session` is **optional** (legacy alias).

| User says | Verb | Git action |
|-----------|------|------------|
| `@session-control` **start** | start | - |
| `session-control` **start** - \<goal\> | start | - |
| `@session-control` **close** | close | draft message only |
| `session-control` **close** | close | draft message only |
| `session-control` **close** **commit** | close | commit all **safe** dirty paths (default scope - [C4b](#c4b--git-actions-modifiers-only)) |
| `session-control` **close** **commit** **scoped** | close | commit only HANDOFF + NEXT + paths listed in close report |
| `session-control` **close** **commit** **push** | close | commit then push |
| `session-control` **close** **push** | close | treat as **commit push** (`push` requires commit) |
| `session-control` **commit** | commit | commit all safe dirty paths (default scope), NO close |
| `session-control` **commit** **push** | commit | commit then push, NO close |
| `@session-control` **status** | status | - |

**Aliases (same verb):** `begin`, `open` → start; `end`, `handoff` → close.

**Goal text:** anything after `-` or on a new line after `start` (not the words `commit`/`push`/`scoped`).

**Commit scope:** default is **full safe tree** (what humans expect from `git add` of their session work). Use **`commit scoped`** only when the user wants bookend files only.

**Standalone commit:** `commit` / `commit push` run the same git steps as `close commit` / `close commit push` but **skip** HANDOFF and NEXT updates. The session remains open.

---

## Step 0 - Pick a mode

| Mode | Triggers | Action |
|------|----------|--------|
| **start** | `start`, optional goal | [Start protocol](#start-protocol) |
| **close** | `close` [commit] [push] | [Close protocol](#close-protocol) |
| **commit** | `commit` [push] | [Commit protocol](#commit-protocol) - git only; no HANDOFF/NEXT writes |
| **status** | `status` | [Status protocol](#status-protocol) - compact snapshot; no HANDOFF writes |

If the user gives a **task goal** with start (e.g. `start - work on payments SPEC`), capture it in the start report and use HANDOFF's conditional reading table.

---

## Start protocol

### S1 - Baseline reads (mandatory)

Read these files **in full** (or confirm missing). Record `pass` only after reading.

| # | File (repo-root path) | Pass criteria |
|---|------|----------------|
| 1 | `.cursorrules` | Can state: identity, 7 core principles, protected files, no-commit rule |
| 2 | `.work/context/HANDOFF.md` | Know: session-critical sections (§Session status through §Open owner actions). The artifact table (§What this cycle produced) and tail sections (§Hygiene, §Doc 04 gate, §Tracked inventory) are reference - skim for relevance, not mandatory for start. |
| 3 | `.work/plans/NEXT.md` | Know: single recommended next action + owner blockers |
| 4 | `.work/plans/UNKNOWNS.md` | Know: every open unknown, its `Blocks` target (task / ADR / milestone), and its `Owner`. Cross-check against HANDOFF §Explicit unknowns and §Open owner actions - stale entries must be noted in the start report. |
| 5 | `.work/plans/foundation/*-01-*-initial-scope.md` **if present** | Know one-sentence product intent **or** record *no doc 01 yet* and rely on README / HANDOFF. **Do not** read `.work/prompts/initial.md` unless the user explicitly names it. |

### S1b - Unblock check (when `.work/plans/NEXT.md` has an active iteration)

If `.work/plans/NEXT.md` contains a `## Current iteration` block with task rows:

1. Scan for tasks with status `blocked`.
2. For each `blocked` task, find the blocker entry in `### Owner blockers` and/or `.work/plans/UNKNOWNS.md` (entries with `blocks: T{N}`).
3. Check if the condition has changed: ADR decided, owner action marked done in HANDOFF §Open owner actions, or dependency completed.
4. If resolved → flip task to `pending`; annotate `unblocked YYYY-MM-DD - <reason>`. If the UNKNOWNS row is also resolved, update its `Status` to `Resolved` with date.
5. If unchanged → leave as `blocked`; surface in the start report `### Open blockers (owner)`.
6. If no iteration block exists → skip.

### S2 - Conditional reads (task-based)

If HANDOFF §"Fresh start" lists extras, or the user named a domain, read those paths before claiming start complete.

| Task touches | Read |
|--------------|------|
| Code / new feature | `.ai/standards/*CONVENTIONS*`, `.ai/standards/*FEATURE_STANDARD*` |
| Stack / infra | `REPLACE:TECH_STACK_DOC` (from `.cursorrules`), `.ai/standards/*DIRECTORY_MAP*` |
| External integration | domain SPEC, `{PLANS_ROOT}/foundation/*-02-*.md`, `.ai/docs/integration/MANIFEST.txt` on demand |
| Foundation planning | `plan-foundation` skill → **status** mode (read-only) |
| Security / new columns | threat-model, data-classification |

### S3 - Environment snapshot (evidence)

Run (or explain why skipped):

```bash
git status -sb
git log -1 --oneline
```

Optional - running services (use first that works):

```bash
docker compose ps 2>/dev/null || podman-compose ps 2>/dev/null || true
```

Record: branch, clean/dirty, last commit, services up/down if checked.

### S4 - Session goal (interaction)

Capture goal from (in order): text after `start -`, else HANDOFF **Recommended pick-up** / repository state, else ask **once**:

**Q:** What is the primary goal for this session? (one line)

Do **not** ask if goal is already clear from invocation or HANDOFF. Store in start report only; do not rewrite HANDOFF unless user asks.

### S4b - Coding goal readiness (when goal implies implementation)

If the session goal mentions coding, M1, implementation, or a feature task:

1. Run `@plan-master status` (read-only) or read HANDOFF for **Implementation-ready** and milestone waivers.
2. If **implementation-ready: no** and no HANDOFF waiver for the named milestone → note in start report under **### Readiness (do not implement yet)** with redirect: `@plan-master status` → approve plan, or add HANDOFF waiver, or `@code-implementation plan - M{N}` only after prerequisites pass.
3. Do **not** invoke `@code-implementation start` from session-control - route the user to that skill after gates pass.

### S4c - GitHub task registry (optional discovery)

The AI MAY query the project's task registry endpoint to discover the current
task/ticket for this session. The endpoint returns an empty registry if the
feature is disabled or no GitHub link is configured — so the query is always
safe to attempt.

```bash
curl -s -H "Authorization: Bearer <JWT>" \
  "${API_BASE_URL:-http://localhost:8300}/v1/projects/{project_id}/github/task-registry"
```

Use `{project_id}` from HANDOFF or the current project context. If
`API_BASE_URL` is not set, default to `http://localhost:8300`.

Match the response against the session goal or branch name:
- If a single entry matches → note it as the active task reference.
- If multiple match → prefer `in_progress` > `todo` > `open`.
- If none match or the endpoint is unreachable → **continue without error**.

The resolved ref (if any) is stored in the start report and used as priority #2 in
commit message ref extraction (see [M4](#m4---commit-message-with-task-ref-always)).

### S5 - Mark session open (HANDOFF)

Update **only** the `## Session status` block at the top of `{HANDOFF}`:

- **Open:** `<YYYY-MM-DD>` - goal: \<user goal or "not specified"\>
- **Updated:** today's date
- Preserve prior "Closed" history in `## What this cycle produced` on **close**, not on start.

If user invoked **status** mode, skip S5 and S6 - use [Status protocol](#status-protocol).

### S6 - Start report (mandatory output)

```markdown
## Session started - <Project Name>

**Date:** <ISO date> · **Branch:** <branch> · **Working tree:** clean | dirty

### Completion checklist
| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | .cursorrules read | pass/fail | |
| 2 | HANDOFF read | pass/fail | |
| 3 | NEXT read | pass/fail | |
| 4 | UNKNOWNS read | pass/fail | |
| 5 | P0 initial scope (foundation doc 01) | pass/skip | `{PLANS_ROOT}/foundation/*-01-*.md` or skip |
| 6 | Conditional reads | pass/skip | <paths> |
| 7 | Git snapshot | pass/skip | <one-liner> |
| 8 | Session goal captured | pass | <goal> |
| 9 | HANDOFF marked Open | pass/skip | |

### You are cleared to work when
All mandatory checks (1–4, 6–8) are **pass**, and row **5** is **pass** (doc 01 read) or **skip** (no doc 01 yet - note in report). If any mandatory **fail**, fix before implementation.

### Pick up here
<quote recommended next from NEXT.md>

### Open blockers (owner)
<from HANDOFF / NEXT>

### Principles reminder (3 bullets max)
<from .cursorrules - not a full paste>
```

---

## Status protocol

Read-only snapshot. **No** HANDOFF/NEXT writes. **No** completion checklist.

1. Read `.work/context/HANDOFF.md` and `.work/plans/NEXT.md`.
2. Run `git status -sb` and `git log -1 --oneline`.
3. Output:

```markdown
## Session status - <Project>

**Session:** Open | Closed - <date> - <goal if Open>
**Branch:** <branch> · **Tree:** clean | dirty
**Pick up:** <one line from NEXT.md>
**Owner blockers:** <short list or none>
```

Optional: one line on dirty files (no full diff). For full context load, use **start**.

---

## Commit protocol

**Execution order:** M1 → M2 → M3 → M4 (draft message with task ref) → M5 (git, if `commit`/`push`) → M6 (report).

Runs git commit and optional push **without** updating HANDOFF or NEXT. Session remains open. Idempotent — re-runnable mid-session.

If M1 secrets **fail**, **stop** — do not run M4 or M5.

### M1 - Working tree audit (same as C1)

Same as [C1](#c1---working-tree-audit-mandatory).

### M2 - Verification gate (same as C2)

Same as [C2](#c2---verification-gate-this-session).

### M3 - Follow-ups

Same as [C3](#c3---follow-ups-required).

### M4 - Commit message with task ref (always)

**Always** produce the commit message block — even when tree is clean (`none - working tree clean`).

Format per `.cursorrules` (plain text, no surrounding quotes).

**Task ref extraction (auto-detect):**
Look for an active task reference in this priority order:

1. **HANDOFF session goal** — if `{HANDOFF}` `## Session status` contains a ref matching `[A-Z]+-[0-9]+` (e.g. `PROJ-456`), use it.
2. **GitHub task registry** (optional) — query the project API (returns empty registry if the feature is disabled or unreachable, so always safe to try):
   ```
   curl -s -H "Authorization: Bearer <JWT>" "${API_BASE_URL:-http://localhost:8300}/v1/projects/{project_id}/github/task-registry"
   ```
   Parse the response, match against HANDOFF goal or branch name to find the best task/ticket. If match found, use its ref. If unreachable, empty, or no match, continue to next priority.
3. **Branch name** — if current branch matches `(feature|fix|chore|docs)/[A-Z]+-[0-9]+` or `[A-Z]+-[0-9]+/`, extract the ref.
4. **Last commit subject** — if `git log -1 --oneline` starts with `[A-Z]+-[0-9]+`, reuse it.
5. **None** — use conventional format without ref.

**Subject format:**
- Ref found: `{REF}: {subject}` (e.g. `PROJ-456: Add login form with email validation`)
- No ref: `type: short description` per existing `.cursorrules` convention

Keep subject ≤72 chars (including ref prefix), imperative mood.

**Body:** optional; wrap ~72 chars; **why**, not file list. Omit if subject is self-contained.

Valid types (when no ref): `feat`, `fix`, `refactor`, `docs`, `chore`, `style`, `test`.

Label in report: **Commit message (draft)** vs **Commit message (used)**.

### M5 - Git actions (modifiers only)

Same as [C4b](#c4b--git-actions-modifiers-only) — default scope, commit via HEREDOC, post-commit verification, push if modifier includes `push`.

**Hard rule - agents MUST execute git:** Typing `@session-control commit` does not commit by itself. The agent **MUST** run shell commands. Checklist item 9 is **fail** if the tree still has unstaged safe changes and no commit SHA was produced.

**Clean tree + `commit` modifier:** skip commit; report `Commit message (used): none - working tree clean`.

### M6 - Commit report (mandatory output)

```markdown
## Commit completed - <Project Name>

**Date:** <ISO date> · **Branch:** <branch>

### Checklist
| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Git audit | pass/fail | clean / N files changed |
| 2 | Secrets safe | pass/fail | |
| 3 | Verification honest | pass/fail | |
| 4 | Follow-ups listed | pass | |
| 5 | Commit message shown | pass | always |
| 6 | Task ref extracted | pass/skip | ref or no ref found |
| 7 | Git commit | pass/fail/skip | modifier `commit`; SHA + `git status` evidence |
| 8 | Full safe tree staged | pass/fail/skip | leftover safe paths listed |
| 9 | Git push (if requested) | pass/fail/skip | modifier `push` |

### Commit message
**Status:** draft | used  
**Message:**

    PROJ-456: subject line here

    Optional body.

**Git:** committed \<sha\> | push \<remote/branch\> result

**Session:** still open — no HANDOFF or NEXT changes.
```

---

## Close protocol

**Execution order:** C1 → C2 → C3 → C4 (draft message) → C5 (HANDOFF) → C6 (NEXT) → C4b (git, if `commit`/`push`) → C7 (optional) → C8 (report).

If C1 secrets **fail**, **stop** - do not run C5, C6, or C4b; report failure in C8.

### C1 - Working tree audit (mandatory)

```bash
git status
git diff --stat
git diff --cached --stat
```

Classify:

| Finding | Action |
|---------|--------|
| Uncommitted changes | Summarize by area; draft commit message(s) |
| Untracked files | Flag if unexpected; remind `.gitignore` / secrets |
| Staged only | Note ready to commit |
| Clean tree | State explicitly |

**Secrets scan (mandatory):** Before summarizing diffs, confirm `git status` does not list paths matching: `credentials/`, `.env`, `.env.*` (except `.env.example`), `*.pem`, `*.p12`, `*.key`, `*.pfx`, `*.p8`, `*id_rsa*`, `*.token`, `*.secret`. If any match → checklist **fail**, **halt close** (no HANDOFF/NEXT/git); tell user to unstage/remove and never commit content.

### C2 - Verification gate (this session)

Per `.cursorrules` Completion Gate - answer honestly:

| Question | Answer |
|----------|--------|
| Code changed this session? | yes / no |
| Tests/lint/build run? | yes / no / n/a |
| All passed? | yes / no / partial |
| What remains unverified? | list |

Do not claim "all good" if tests failed.

**Probe ledger pre-check (only if a `PROBE_LEDGER.md` exists):** run `bash .ai/scripts/readiness-verify.sh`. On **fail** (uncited `confirmed/high`, inflated Coverage %, or `coverage ≥ target` with a gate-blocking dimension still `unknown`), record it under [C3](#c3--follow-ups-required) and recommend `@plan-foundation probe` / `@plan-master probe` - do **not** claim planning is ready.

**Traceability pre-check (only if a master plan exists):** run `bash .ai/scripts/traceability-verify.sh`. On **fail** (an FR maps to no task `M{N}-T{N}`), record under [C3](#c3--follow-ups-required) and recommend `@plan-master revise` / `@plan-repair master` - do **not** claim the plan is implementation-complete.

### C3 - Follow-ups required

Detect and list:

- [ ] Uncommitted work needing commit (or intentional WIP)
- [ ] HANDOFF / NEXT out of date vs actual repo
- [ ] Open ADRs blocking the work touched
- [ ] Owner actions (legal review, vendor approvals, schema packs, etc.)
- [ ] Docker/infra left running (optional note)
- [ ] Temp files under `tmp/` that should be deleted
- [ ] SPECs promised but not written
- [ ] Archived prompts at risk of edit - **warn**

### C4 - Commit message with task ref (always)

**Always** produce the commit message block in the close report - even when the tree is clean (`none - working tree clean`).

Format per `.cursorrules` (plain text, no surrounding quotes).

**Task ref extraction (auto-detect):**
Look for an active task reference in this priority order:

1. **HANDOFF session goal** — if `{HANDOFF}` `## Session status` contains a ref matching `[A-Z]+-[0-9]+` (e.g. `PROJ-456`), use it.
2. **GitHub task registry** (optional) — query the project API (returns empty registry if the feature is disabled or unreachable, so always safe to try):
   ```
   curl -s -H "Authorization: Bearer <JWT>" "${API_BASE_URL:-http://localhost:8300}/v1/projects/{project_id}/github/task-registry"
   ```
   Parse the response, match against HANDOFF goal or branch name to find the best task/ticket. If match found, use its ref. If unreachable, empty, or no match, continue to next priority.
3. **Branch name** — if current branch matches `(feature|fix|chore|docs)/[A-Z]+-[0-9]+` or `[A-Z]+-[0-9]+/`, extract the ref.
4. **Last commit subject** — if `git log -1 --oneline` starts with `[A-Z]+-[0-9]+`, reuse it.
5. **None** — use conventional format without ref.

**Subject format:**
- Ref found: `{REF}: {subject}` (e.g. `PROJ-456: Add login form with email validation`)
- No ref: `type: short description` per existing `.cursorrules` convention

Keep subject ≤72 chars (including ref prefix), imperative mood (`add`, `fix`, not `added`).

- **Body:** optional; wrap ~72 chars; **why**, not file list. Omit if subject is self-contained.

Valid types (when no ref): `feat`, `fix`, `refactor`, `docs`, `chore`, `style`, `test`.

- One message if changes are cohesive; suggest **split** with multiple message blocks if not.
- Label in report: **Commit message (draft)** vs **Commit message (used)**.

### C4b - Git actions (modifiers only)

| Modifier | Action |
|----------|--------|
| *(none)* | Message only. User runs `git commit` themselves. |
| `commit` | Only if C1 secrets **pass**. After C5/C6 (close) **or** after M4 (standalone commit): stage per **default scope** → `git commit` (HEREDOC) → verify tree → record SHA. |
| `commit scoped` | After C5/C6: stage only `{HANDOFF}`, `{ITERATION_CARRIER}`, and paths explicitly tied to this session in the close report. |
| `commit push` | After successful commit: `git push` (current branch). Warn before force-push. |

**Hard rule - agents MUST execute git:** Typing `@session-control close commit` or `@session-control commit` does not commit by itself. The agent **MUST** run shell commands below. Checklist item 6 (close) / item 7 (commit) is **fail** if the tree still has unstaged safe changes and no commit SHA was produced.

**Default commit scope** (when modifier is `commit` or `commit push`, not `scoped`):

1. Run `git status --porcelain` (from C1).
2. Build the stage list = every path with status `M`, `A`, `D`, `R`, `C`, or `??` (untracked) **except** paths matching:
   - Secrets scan patterns (C1) - never add
   - `tmp/`, `.obfuscation/output/` - never add unless user explicitly named them for commit
   - Protected files per `{AGENT_RULES_FILE}` §Protected Files - **do not add**; list in close report as follow-up
3. Stage by top-level area when many files share a prefix (typical):
   ```bash
   git add .ai/ .work/ apis/ dashboard/ bin/ DOCS_TECH_STACK.md README.md
   ```
   Or stage explicit paths from step 2 if the diff is small.
4. **Do not** default to HANDOFF + NEXT only - that is **`commit scoped`**, not default `commit`.
5. If the only remaining dirty paths are excluded (protected / secrets), commit what was staged and report exclusions.

**Commit command shape:**

```bash
git add <paths-from-scope>
git commit -m "$(cat <<'EOF'
<exact message from C4>
EOF
)"
git status -sb
git log -1 --oneline
```

**Post-commit verification (mandatory):**

| Check | pass when |
|-------|-----------|
| Commit created | `git log -1` shows new SHA |
| Staging complete | No remaining `M`/`D`/`??` in safe paths from step 2, **or** report lists each leftover path and why (protected, secrets, intentional WIP) |

**On commit failure:** report hook output; do not claim close complete for git step; HANDOFF/NEXT updates still stand if already written.

**Clean tree + `commit` modifier:** skip commit; report `Commit message (used): none - working tree clean`.

**Never:** `git commit --no-verify`, `git push --force` unless user explicitly requests in the same message.

### C5 - Update HANDOFF (mandatory on close)

Rewrite top sections (keep history table append-only style):

1. **Session status:** `Closed: <date>` - one-line summary of session outcome.
2. **Updated:** today.
3. **Repository state:** current truth (planning vs code, blockers).
4. **Recommended pick-up file:** point to `NEXT.md`.
5. **What this cycle produced:** append rows for new/updated artifacts (no duplicates).
6. **Explicit unknowns:** refresh from session.
7. **Open owner actions:** refresh.
8. **Foundation gate snapshot** (if project uses doc 04 §14): update table.
9. Remove stale "Open" session line; closed sessions must not say "in progress".

Do not delete historical rows in artifact tables; append new entries.

### C6 - Update NEXT.md (mandatory on close)

- Move completed items to **Done** with date.
- Set **one** clear **Recommended next**.
- Refresh **Blocked on owner**.
- Update foundation gate / pre-merge checklist if applicable.

### C7 - Optional: plan-foundation status

If the repo uses plan-foundation conventions, run **status** (read-only) and attach ≤5 lines - foundation-complete + plan-master-ready (not implementation-ready; that is plan-master).

### C8 - Close report (mandatory output)

```markdown
## Session closed - <Project Name>

**Date:** <ISO date> · **Branch:** <branch>

### Completion checklist
| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Git audit | pass/fail | clean / N files changed |
| 2 | Secrets safe | pass/fail | |
| 3 | Verification honest | pass/fail | |
| 4 | Follow-ups listed | pass | |
| 5 | Commit message shown | pass | always |
| 6 | Git commit (if requested) | pass/fail/skip | modifier `commit`; SHA + `git status` evidence |
| 6b | Full safe tree staged (default `commit`) | pass/fail/skip | not `scoped`; leftover safe paths listed |
| 7 | Git push (if requested) | pass/fail/skip | modifier `push` |
| 8 | HANDOFF updated | pass/fail | |
| 9 | NEXT updated | pass/fail | |
| 10 | Foundation status (optional) | pass/skip | |

### Commit message
**Status:** draft | used  
**Task ref:** <ref or none>  
**Message:** (plain text below - always present)

    PROJ-456: subject line here

    Optional body - why, not what.

**Git:** no commit (default) | committed \<sha\> | push \<remote/branch\> result

### Follow-ups before next session
<ordered list>

### Next session should
<one line from NEXT.md>
```

---

## Critical interactions

| When | Ask / do |
|------|----------|
| **Start** | Prior HANDOFF says `Closed` → treat as new session; do not assume prior chat memory |
| **Start** | Missing HANDOFF → offer to run `plan-foundation` greenfield or create minimal HANDOFF |
| **Start** | Dirty tree at start → note in report; ask if continuing WIP or stashing |
| **Start** | HANDOFF already **Open**, new `start -` goal differs | Update Open line with new goal + date; do not silently drop prior goal (note change in start report) |
| **Close** | Large uncommitted diff → suggest commit split |
| **Close** | User says "close without updating HANDOFF" → only allowed if they confirm; mark checklist item `skip` with reason |
| **Close** | Protected files changed → flag for explicit owner review - see `{AGENT_RULES_FILE}` §Protected Files |
| **Close** | `close commit` / `close commit push` → run C4b in shell after HANDOFF/NEXT; stage **default scope**; always echo SHA + post-commit `git status -sb` |
| **Close** | User expected commit but tree still dirty | **fail** item 6/6b; list unstaged paths; do not claim "close commit" succeeded |
| **Close** | `push` without network → report failure; do not claim pushed |
| **Commit** | User says `@session-control commit` or `commit push` | Run [Commit protocol](#commit-protocol); **do not** update HANDOFF or NEXT; session stays open |
| **Commit** | Task ref found in HANDOFF goal or branch | Prepend `{REF}: ` to commit subject automatically |
| **Commit** | No task ref found | Use conventional `type: description` format; no error — ref is optional |

---

## Anti-patterns

- Claiming "context loaded" without reading HANDOFF and NEXT
- Closing session without updating HANDOFF and NEXT
- Committing on plain `close` (without `commit` modifier)
- **`close commit` with only HANDOFF/NEXT staged** while other safe paths remain dirty (use `commit scoped` if intentional)
- **Reporting close commit done without running `git commit`** or without a new SHA
- Omitting the commit message block from the close report
- Putting secrets or PII in HANDOFF
- Editing archived decision prompts during close "cleanup"
- Marking checklist `pass` without evidence
- Continuing close after secrets scan **fail**
- Running C4b before C5/C6 when `close commit` modifier used
- Running **HANDOFF/NEXT updates** on standalone `commit` or `commit push`
- Claiming task ref extraction when HANDOFF / branch / last commit has no match
- Using `commit` when tree is already clean **without** explicitly reporting "none - working tree clean"
- Committing non-`REF:` format when a valid task ref is detectable (missed association opportunity)

---

## Project layout (convention)

**`{WORK_ROOT}` = `.work/`** at repo root (sibling of `.ai/` in consumer repos). Not the git root itself.

```
.work/                          ← {WORK_ROOT}
  context/HANDOFF.md            ← session-control ({HANDOFF})
  plans/NEXT.md                 ← session-control + code-implementation ({ITERATION_CARRIER})
  features/                     ← feature-spec ({FEATURE_SPEC_ROOT})
  prompts/                      ← plan-foundation P0 ({PROMPTS_ROOT})
  decisions/                    ← ADRs ({DECISIONS_ROOT})
.ai/skills/                     ← portable skills only
```

Projects without `.work/context/HANDOFF.md`: see `reference.md` § bootstrap.
