---
name: process-router
description: >-
  Read-only router for process questions. Maps a question to the right skill
  verb, workflow guide, standard, or concept prompt - without duplicating their
  content. Use when lost, asking how something works, or wanting the next
  command for planning, implementation, tests, migrations, SPECs, or concepts.
  Not a catch-all Q&A encyclopedia.
---

# process-router

**Read-only orientation.** Routes operators to canonical sources. **Never** writes HANDOFF, NEXT, code, or SPECs. **Never** embeds normative text from skills/standards - link and quote one line max.

**Pairs with:** `.ai/START_HERE.md` (decision tree), `.ai/docs/guides/workflows/`, registered skills.

**Canonical path:** `.ai/skills/process-router/skill.md` · **Routing index:** `reference.md` · **Human guide:** [`.ai/PROCESS_ROUTER.md`](../../PROCESS_ROUTER.md)

**Hard rules:**

- **Default:** no file writes. Only `route` / `ask` / `help` modes.
- **Source of truth order:** `skill.md` > standard > guide > this router. If router conflicts, follow the skill.
- **Evidence:** cite path + section when recommending a command.
- **Escalate:** if the question needs execution (create SPEC, run migration, start iteration), name the target skill and stop - do not impersonate it.

---

## Parse invocation

| User says | Mode | Action |
|-----------|------|--------|
| `@process-router` **route** - \<question\> | route | [Route protocol](#route-protocol) |
| `@process-router` **ask** - \<question\> | route | alias |
| `@process-router` **help** | help | List modes + 5 example questions |
| `@process-router` - \<question\> (no verb) | route | Treat whole message as question |

**Aliases:** `ask`, `where`, `how` → route.

---

## Step 0 - Pick a mode

| Mode | Action |
|------|--------|
| **route** / **ask** | Classify question → output [Route report](#route-report-format) |
| **help** | Output modes + examples; point to `reference.md` routing table |

---

## Route protocol

1. Read the user question (text after `-` or remainder of message).
2. Classify into one primary bucket. **The authoritative bucket set is the row list in [reference.md](reference.md) § Routing table** - match against it directly (e.g. `orient`, `session`, `plan-foundation`, `implement`, `spec`, `feature-request`, `schema`, `learn`, …). Do **not** maintain a second canonical copy of the bucket list here; if you add a bucket, add the row in `reference.md`.
3. Load **only** the matched row's linked paths (do not read the whole repo).
4. Output the route report. If multiple buckets match, list primary first, secondary one line each.
5. If the question matches **no** bucket, say so and route to `.ai/START_HERE.md` §1 (decision tree) - never invent a skill/path.
6. If the question is ambiguous, ask **once** with ≤3 multiple-choice options drawn from the table.

---

## Route report format

```markdown
## process-router - <short topic>

**Question:** <paraphrase one line>

### Answer (<3 sentences)
<Plain-language direction - no wall of pasted rules>

### Run next
`<exact @skill verb or read order>`

### Canonical sources
| Kind | Path |
|------|------|
| Skill | … |
| Guide | … |
| Standard | … |

### Snippet (optional, ≤5 lines)
<Minimal command block only when it helps copy-paste>
```

---

## Help protocol

Output:

1. One paragraph: **process-router is a signpost, not a worker.** It tells you which skill or doc to open; that skill does the work.
2. Modes: `route`, `ask`, `help`.
3. Five examples (from reference.md).
4. Link: `.ai/START_HERE.md` for "what do I do right now?"

---

## Anti-patterns

- Answering with long pasted excerpts from standards (link instead).
- Running `code-implementation start`, writing SPECs, or updating HANDOFF from this skill.
- Inventing skills or paths not in `reference.md` or `.ai/skills/README.md`.
- Replacing `@session-control status` / `@code-implementation status` when user only needs a one-line snapshot - suggest those first for status questions.

---

## Completion checklist (route mode)

| # | Check | Result |
|---|-------|--------|
| 1 | Question classified | pass/fail |
| 2 | Primary skill or doc named | pass |
| 3 | No file writes | pass |
| 4 | Sources cited with paths | pass |
