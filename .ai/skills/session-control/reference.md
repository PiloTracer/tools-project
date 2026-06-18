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
| Load check | `@session-control` **status** |

Legacy aliases still work: `session start`, `session close`, `handoff`, `begin`, `end`.

Prior Cursor skill ids (treat as equivalent prompts): `@session-manager` → **session-control**; `@foundation-plan` → **plan-foundation**; `@full-plan` → **plan-master**; `@implement-code` → **code-implementation**; `@sql-migrations` → **db-migration**.

### Cursor

```
@session-control start
@session-control close
@session-control close commit
@session-control close commit push
```

### Claude Code / opencode / Codex

```
Follow .ai/skills/session-control/skill.md - start.
```

```
Follow .ai/skills/session-control/skill.md - close commit push.
```

### Close modifiers (git)

| Invocation | Commit? | Push? | Commit message in report |
|------------|---------|-------|---------------------------|
| `close` | no | no | **always** (draft) |
| `close commit` | yes | no | **always** (used + SHA if ok) |
| `close commit push` | yes | yes | **always** (used + push result) |
| `close push` | yes | yes | same as `close commit push` |

Default `close` never runs `git commit` or `git push`. User runs git manually from the drafted message if they want.

**`close commit` default scope:** stage all **safe** dirty paths from `git status --porcelain` (typically `git add .ai/ .work/` plus app dirs touched), **not** HANDOFF/NEXT only. Agent **must** run shell `git add` + `git commit` and show SHA + post-commit `git status -sb`. See `skill.md` § C4b.

### Natural language triggers

| Phrase | Maps to |
|--------|---------|
| `start` / `begin` / `open` | start |
| `close` / `end` / `handoff` | close |
| `close commit` | close + commit |
| `close commit push` | close + commit + push |
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

---

## Mode comparison

| | start | status | close | close commit | close commit push |
|---|-------|--------|-------|--------------|-------------------|
| Read HANDOFF/NEXT | yes | yes | yes | yes | yes |
| Update HANDOFF | Open | no | Closed | Closed | Closed |
| Update NEXT | no | no | yes | yes | yes |
| `git commit` | no | no | no | yes | yes |
| `git push` | no | no | no | no | yes |
| Commit message in output | no | no | **always** | **always** | **always** |
| Completion checklist | yes | no | yes | yes | yes |

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

Never on default `close`: commit or push.

---

## Commit message rules (summary)

- Subject ≤72 chars, imperative (`docs: update HANDOFF for session close`).
- Body: why, not file list; omit if subject suffices.

## Commit message examples (close mode)

**Docs-only session:**

```
docs: add session-control skill and update HANDOFF

Session bookends for context load and close hygiene; no application code.
```

**Planning + infra:**

```
docs: close planning session - docker compose approved

HANDOFF and NEXT updated; compose files on disk; application source not started.
```

**Feature work (when user commits separately):**

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

Document in project README if adopted.
