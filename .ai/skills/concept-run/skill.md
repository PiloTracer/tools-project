---
name: concept-run
description: >-
  Run architecture concept prompts (MOD-01 through MOD-06) per the trigger table.
  Use when opening a SPEC §15, planning an iteration registry, AI-assisted PR
  review, boundary-crossing diffs, or verify pending concept rows. Attaches
  structured output to PR, NEXT.md task Notes, or SPEC/ADR as specified.
---

# concept-run

Execute **concept pack** procedures under `.ai/concepts/<name>/prompt.md`. Registry and triggers: `.ai/concepts/README.md` § Trigger table.

**Read-only on prompts** (never edit `prompt.md`). **May update** iteration registry rows in `NEXT.md` or SPEC §15 when user invoked run in an active iteration context.

**Pairs with:** `feature-spec` (§15), `code-implementation` (iteration registry), `code-verify` (milestone matrix).

**Hard rules:**

- **Evidence tags** on every quantitative claim: `measured` | `estimated` | `assumption` | `unknown`.
- **Run the prompt procedure** - do not summarize from memory.
- **Output shape** must match each `prompt.md` § Output section.
- **Default when unsure:** MOD-01 (coupling-audit) - lightest prompt.
- **MOD-06 required** for every `@code-implementation` session that touches code - **AI-assisted: yes** by default in Cursor/agent sessions; only explicit **`human-only`** (same message) opts out.

---

## Parse invocation

| User says | Mode | Action |
|-----------|------|--------|
| `@concept-run` **list** | list | Trigger table summary (read-only) |
| `@concept-run` **status** | status | Pending concept rows in NEXT § Current iteration |
| `@concept-run` **run** - MOD-0N | run | Execute one prompt |
| `@concept-run` - MOD-0N | run | alias |
| `@concept-run` **run-all** - pending | run-all | All iteration rows with Applies=yes, Status=pending |

**Ids:** MOD-01 … MOD-06 - map to folders in `.ai/concepts/README.md` § Concept index.

---

## Step 0 - Pick a mode

| Mode | Action |
|------|--------|
| **list** | [List protocol](#list-protocol) |
| **status** | [Status protocol](#status-protocol) |
| **run** | [Run protocol](#run-protocol) |
| **run-all** | Run each pending applicable concept; stop on block recommendation |

---

## List protocol

1. Read `.ai/concepts/README.md` § Trigger table.
2. Output compact table: **If you are about to…** | **MOD id** | **Output goes to** | **Required?**
3. Point to `@process-router` for "which one do I need?" without a specific MOD id.

---

## Status protocol

1. Read `NEXT.md` § `### Concept / NFR registry (this iteration)` if present.
2. List rows where `Applies` ≠ n/a and `Status` = pending.
3. If no iteration block, report "no active iteration registry" and suggest `@concept-run list`.

---

## Run protocol

1. Resolve MOD id → folder (e.g. MOD-06 → `ai-amplification/`).
2. Read `README.md` (context) + `prompt.md` (procedure) in full.
3. Gather **Inputs** listed in that prompt (diff summary, boundary map, test commands, etc.). Ask once if a required input is missing.
4. Follow procedure steps; produce output in the **required sections** from `prompt.md`.
5. **Attach output** per trigger table:
   - PR description, or
   - `NEXT.md` task `Notes` column, or
   - SPEC §9 / ADR appendix (as row specifies).
6. Update iteration registry `Status` → `done YYYY-MM-DD` or `gap - <reason>` when run from an iteration context.
7. Output run report:

```markdown
## concept-run - MOD-0N (<name>)

**Trigger:** <why this prompt applied>
**Evidence tags used:** …

### Prompt output
<paste structured output from prompt.md>

### Attached to
<path: PR | NEXT task | SPEC §…>

### Recommendation
proceed | conditions | block - per prompt Recommendation section
```

---

## Concept index (quick)

| Id | Folder |
|----|--------|
| MOD-01 | `coupling-audit/` |
| MOD-02 | `network-cost/` |
| MOD-03 | `cost-model/` |
| MOD-04 | `ops-headcount/` |
| MOD-05 | `modularity-vs-distribution/` |
| MOD-06 | `ai-amplification/` |

---

## Integration with code-verify milestone

When `@code-verify milestone` runs, any iteration row with `Applies=yes` and `Status=pending` must be cleared via **run** or explicitly marked `gap` with owner.

---

## Anti-patterns

- Skipping MOD-06 on agent/Cursor-authored diffs (default **AI-assisted: yes**).
- Self-classifying agent output as non-AI to bypass MOD-06.
- Presenting `assumption` as `measured`.
- Editing concept `prompt.md` files during a run.
- Running MOD-03 without a `$` line when adding billable units.

---

## Completion checklist (run mode)

| # | Check | Result |
|---|-------|--------|
| 1 | prompt.md read and followed | pass |
| 2 | Output shape matches prompt | pass |
| 3 | Evidence tags present | pass |
| 4 | Output attached to correct artifact | pass |
