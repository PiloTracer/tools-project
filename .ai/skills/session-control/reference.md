# session-control - reference

Supplement to `skill.md`. Invocation examples, HANDOFF templates, and edge cases.

---

## Invocation examples

**Canonical forms** - do not require the word `session`:

| Action | Prompt |
|--------|--------|
| Open | `@session-control` **start** |
| Open + goal | `session-control` **start** - bootstrap platform skeleton |
| Close | `@session-control` **close** |
| Close + commit (all safe dirty files) | `session-control` **close** **commit** |
| Close + commit (HANDOFF/NEXT only) | `session-control` **close** **commit** **scoped** |
| Close + commit + push | `session-control` **close** **commit** **push** |
| **Commit only (no close)** | `@session-control` **commit** |
| **Commit + push (no close)** | `session-control` **commit** **push** |
| Load check | `@session-control` **status** |

Legacy aliases still work: `session start`, `session close`, `handoff`, `begin`, `end`.

Prior Cursor skill ids (treat as equivalent prompts): `@session-manager` → **session-control**; `@foundation-plan` → **plan-foundation**; `@full-plan` → **plan-master**; `@implement-code` → **code-implementation**; `@sql-migrations` → **db-migration**.

### Cursor

```
@session-control start
@session-control close
@session-control close commit
@session-control close commit push
@session-control commit
@session-control commit push
```

### Claude Code / opencode / Codex

```
Follow .ai/skills/session-control/skill.md - start.
```

```
Follow .ai/skills/session-control/skill.md - close commit push.
```

### Close modifiers (git)

| Invocation | Commit? | Push? | Commit message in report | Closes session? |
|------------|---------|-------|---------------------------|-----------------|
| `close` | no | no | **always** (draft) | yes |
| `close commit` | yes | no | **always** (used + SHA if ok) | yes |
| `close commit push` | yes | yes | **always** (used + push result) | yes |
| `close push` | yes | yes | same as `close commit push` | yes |
| `commit` | yes | no | **always** (used + SHA if ok) | **no** |
| `commit push` | yes | yes | **always** (used + push result) | **no** |

Default `close` never runs `git commit` or `git push`. User runs git manually from the drafted message if they want.

### GitHub task registry (optional)

If the project has `github_task_registry_enabled` **and** `auto_prefix_enabled`, the app
maintains a lightweight registry file (`.github/task-registry.json`) via the GitHub Contents
API. Whenever a task or ticket is created/updated/deleted, the registry is synced to the linked
GitHub repo. (With only `github_task_registry_enabled`, the query endpoint still works but
returns an empty registry — no entries are pushed.)

The AI SHOULD query the registry to discover the correct task/ticket ref:

```bash
curl -s -H "Authorization: Bearer <JWT>" \
  "${API_BASE_URL:-http://localhost:8300}/v1/projects/{project_id}/github/task-registry"
```

Response format:
```json
{
  "version": 1,
  "updated_at": "2026-06-25T12:00:00Z",
  "tasks": [
    {"ref": "PROJ-456", "title": "Add login form", "status": "todo", "project_id": "..."}
  ],
  "tickets": [
    {"ref": "PROJ-T-23", "title": "Login broken", "status": "open", "project_id": "..."}
  ]
}
```

If the registry is unreachable or no match is found, fall back to HANDOFF/branch/last-commit.
**Never block** — the system works seamlessly without the registry.

**Inbound auto-linking (closes the loop):** when commits are synced from GitHub (manual sync,
background poll, or `/sync-backfill`), the app scans each commit message for `[A-Z]+-(?:T-)?\d+`
refs (e.g. `PROJ-456:` / `PROJ-T-23:`), resolves them to task/ticket rows in the same project,
and writes idempotent `commit_subject_refs` rows. So a commit authored with the ref prefix above
is automatically linked back to its task/ticket — no manual step required. Re-syncs never
duplicate rows (`ON CONFLICT DO NOTHING`); linking failures never break the sync.

**`close commit` / `commit` default scope:** stage all **safe** dirty paths from `git status --porcelain` (typically `git add .ai/ .work/` plus app dirs touched), **not** HANDOFF/NEXT only. Agent **must** run shell `git add` + `git commit` and show SHA + post-commit `git status -sb`. See `skill.md` § C4b.

**Standalone `commit` / `commit push`:** same git behavior as `close commit` / `close commit push` but **skips** HANDOFF and NEXT updates. Session stays open.

### Natural language triggers

| Phrase | Maps to |
|--------|---------|
| `start` / `begin` / `open` | start |
| `close` / `end` / `handoff` | close |
| `close commit` | close + commit |
| `close commit push` | close + commit + push |
| `commit` | commit only (no close) |
| `commit push` | commit + push, no close |
| `status` / am I loaded | status |

### Examples

**Start:**

```
@session-control start - implement platform health route
```

**Close (default - no git write):**

```
@session-control close
```

Expect: HANDOFF/NEXT updated; **Commit message** section with draft text; checklist item 6–7 `skip`.

**Close with commit:**

```
session-control close commit
```

Expect: HANDOFF/NEXT updated; agent runs `git add` for **full safe scope** + `git commit`; report shows SHA and `git status -sb` (clean or explicit leftovers). **Fail** if only bookend files were committed while other safe `.ai/` / `.work/` / code changes remain unstaged.

**Close with commit and push:**

```
session-control close commit push
```

Expect: commit then `git push -u` if needed; report shows push result or error.

**Commit only (no close):**

```
session-control commit
```

Expect: git audit, task ref auto-detected from HANDOFF or branch, commit message drafted with `{REF}:` prefix, `git add` + `git commit` run, session **remains open**. No HANDOFF/NEXT updates.

**Commit and push (no close):**

```
session-control commit push
```

Expect: same as commit, then `git push`. Session stays open.

---

## Mode comparison

| | start | status | close | close commit | close commit push | **commit** | **commit push** |
|---|-------|--------|-------|--------------|-------------------|-----------|----------------|
| Read HANDOFF/NEXT | yes | yes | yes | yes | yes | **no** | **no** |
| Update HANDOFF | Open | no | Closed | Closed | Closed | **no** | **no** |
| Update NEXT | no | no | yes | yes | yes | **no** | **no** |
| `git commit` | no | no | no | yes | yes | **yes** | **yes** |
| `git push` | no | no | no | no | yes | **no** | **yes** |
| Commit message in output | no | no | **always** | **always** | **always** | **always** | **always** |
| Completion checklist | yes | no | yes | yes | yes | **yes** | **yes** |
| Task ref auto-detected | - | - | - | yes | yes | **yes** | **yes** |
| Query GitHub task registry (optional) | yes | no | no | yes | yes | **yes** | **yes** |

---

## HANDOFF - Session status templates

### Open (after start)

```markdown
## Session status

**Open:** 2026-05-18 - goal: bootstrap platform health route

**Updated:** 2026-05-18

Treat prior closed sessions as historical only; see "What this cycle produced" below.
```

### Closed (after close)

```markdown
## Session status

**Closed:** 2026-05-18 - platform skeleton landed; tests not yet run

**Updated:** 2026-05-18

Treat the next chat as a **new session**: do not assume unwritten goals from prior threads unless they appear in this file or linked artifacts.
```

---

## Git commands reference

| Purpose | Command |
|---------|---------|
| Short status | `git status -sb` |
| Close audit | `git status` + `git diff --stat` + `git diff --cached --stat` |
| After commit | `git log -1 --oneline` |
| Split advice | `git diff --name-only` grouped by top-level dir |

| When | Allowed |
|------|---------|
| `close` | audit only |
| `close commit` | `git status --porcelain` → stage safe paths (default: `.ai/`, `.work/`, app dirs) → `git commit` → `git status -sb` |
| `close commit scoped` | `git add` HANDOFF + NEXT (+ session-listed paths only) |
| `close commit push` | above + `git push` |
| `commit` | same as `close commit` but **no** HANDOFF/NEXT update |
| `commit push` | same as `close commit push` but **no** HANDOFF/NEXT update |

Never on default `close`: commit or push. **Standalone `commit` / `commit push`** always runs git.

---

## Commit message rules (summary)

- Subject ≤72 chars, imperative (`docs: update HANDOFF for session close`).
- Body: why, not file list; omit if subject suffices.

## Commit message examples

**Docs-only session (no task ref):**

```
docs: add session-control skill and update HANDOFF

Session bookends for context load and close hygiene; no application code.
```

**Planning + infra (no task ref):**

```
docs: close planning session - docker compose approved

HANDOFF and NEXT updated; compose files on disk; application source not started.
```

**Feature work with task ref (auto-detected from branch `feature/PROJ-456-login-form`):**

```
PROJ-456: Add login form with email validation

- Email regex validation on submit
- Error state styling for invalid input
```

**Feature work without task ref (no match in HANDOFF or branch):**

```
feat: add platform health route and settings scaffold

FastAPI /health with DB ping; pydantic Settings from env per CONVENTIONS.
```

---

## Bootstrap (no HANDOFF yet)

**Path:** handoff lives at **`.work/context/HANDOFF.md`** (not `context/HANDOFF.md` at repo root). See `skill.md` § Path resolution.

If `.work/context/HANDOFF.md` is missing:

1. Tell user HANDOFF is required for session-control.
2. Offer: create minimal HANDOFF from README + `git log` **or** run `plan-foundation` greenfield first.
3. Minimal HANDOFF sections: Session status, Repository state, Recommended pick-up, Fresh start checklist.

Do not invent project history.

---

## Integration with other skills

| Skill | When |
|-------|------|
| `plan-foundation` **status** | Optional on start (know planning stage) or close (gate delta) |
| `plan-foundation` **continue** | User goal is planning-only at session start |
| User commit rule | Overrides any urge to commit on close |

---

## Edge cases

| Situation | Behavior |
|-----------|----------|
| Merge conflict markers in tree | close checklist **fail**; list files |
| Only `.ai/` changed | commit type usually `docs` |
| `credentials/` in `git status` | **fail** secrets check; do not summarize content |
| User closes mid-task | HANDOFF notes "in-flight: …" under Repository state |
| Multiple logical commits | close report suggests 2+ message blocks |
| HANDOFF already Open, new `start -` goal | Set Open line to new goal + today's date; note prior goal in start report |
| HANDOFF says Open but user runs start again (same goal) | Refresh date only; do not duplicate artifact table |
| Git submodules dirty | `git submodule status`; flag dirty subs; audit each if relevant |
| Secrets scan fail | **Halt** close - no HANDOFF/NEXT/commit until resolved |

---

## Wrong prompts

| Prompt | Problem | Use instead |
|--------|---------|-------------|
| `close` expecting auto-commit | Default is draft only | `close commit` |
| `close commit` but tree still dirty | Agent staged HANDOFF-only or skipped shell git | Re-run close; agent must follow C4b default scope |
| `close commit` for bookend files only | Default commits full safe tree | `close commit scoped` |
| `close push` without `commit` | Skill maps to commit+push | `close commit push` |
| `commit` expecting HANDOFF update | Standalone commit skips HANDOFF/NEXT | Use `close commit` instead |
| `commit push` expecting session close | Standalone commit keeps session open | Use `close commit push` instead |
| `start` without reading files | Skill requires evidence | Full start protocol |
| `delete HANDOFF and recreate` | Loses history | Append + update sections |
| `close` with failing tests unmentioned | Violates honesty | Report failures in C2 |
| Omitting commit message from report | Violates skill | Always show ### Commit message |

---

## Optional slash commands (team convention)

| Command | Maps to |
|---------|---------|
| `/sm start` | start |
| `/sm close` | close |
| `/sm close commit` | close commit |
| `/sm close commit push` | close commit push |
| `/sm commit` | commit (no close) |
| `/sm commit push` | commit + push (no close) |

Document in project README if adopted.
