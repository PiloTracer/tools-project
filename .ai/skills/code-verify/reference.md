# code-verify - reference

Supplement to `skill.md`.

---

## Invocation

```
@code-verify                    # default: milestone if iteration active, else uncommitted/last
@code-verify milestone          # full plan + SPEC matrix (legacy: @code-implementation verify)
@code-verify uncommitted        # working tree diff only
@code-verify last               # last commit OR last push (whichever was later)
@code-verify status             # read-only: suggest which mode to run
```

Open language (agent maps to mode + emits Request interpretation):

```text
@code-verify - are my changes safe to commit?
@code-verify - audit what I just pushed
@code-verify - check milestone M2 against the SPEC before I complete
@code-verify - what should I verify right now?
```

Legacy (still valid - agents should route here):

```
@code-implementation verify
@code-implementation verify uncommitted
```

---

## Mode picker

| Situation | Mode | Skill |
|-----------|------|-------|
| Before `@code-implementation complete` | **milestone** | `code-verify` |
| After each task (blocking) | **task gate** (inline) | `code-implementation` |
| Dirty tree, about to commit | **uncommitted** | `code-verify` |
| Just committed or just pushed | **last** | `code-verify` |
| Clean tree, synced with remote | **last** (audits tip commit as last push) | `code-verify` |
| Ahead of origin | **last** (audits unpushed commits as last commit event) | `code-verify` |

---

## Typical flow

```
@code-implementation continue     # implement task
@code-verify uncommitted          # optional: before commit
@session-control close commit     # user commits
@code-verify last                 # audit what was committed/pushed
… repeat …
@code-verify milestone            # ≥80% tasks or before complete
@code-implementation complete
```

---

## Last-event resolution (summary)

```
fetch origin
if behind upstream → FAIL (pull first)
if ahead of upstream → last event = commit → diff @{u}..HEAD
if synced with upstream → last event = push → diff HEAD~1..HEAD
```

Tests always run in Docker against the **current** checkout unless you add an optional worktree step for strict SHA replay.

---

## Cross-LLM by milestone (single-model sessions)

| Milestone scope | Behavior when no second model | Block complete? |
|-----------------|--------------------------------|-----------------|
| Early milestones (platform, fixtures, domain stubs per master plan) | `skipped - single-model session` | No |
| **Milestones touching high-risk modules** (threat model / `.cursorrules`) | **fail** unless owner records a **human architect review** in `{HANDOFF}` (name + date) | **Yes** until waiver recorded |

Waivers do not carry forward to the next high-risk milestone.

---

## AI-assisted default (MOD-06)

| Situation | MOD-06 row result |
|-----------|--------------------|
| Cursor/agent session with code changes in application source/tests, no output attached | **fail** - `skip` is forbidden |
| Cursor/agent session, MOD-06 output attached (PR, task `Notes`, iteration registry) | **pass** |
| Human declared **`human-only`** in the same message authoring the edits | **n/a** with quoted human declaration as evidence |

The default is **AI-assisted: yes** in any agent session. Agents must not self-classify their own diffs as non-AI to clear the row.
