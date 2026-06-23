# process-router - operator guide

**Skill location:** [`.ai/skills/process-router/skill.md`](skills/process-router/skill.md) · **Routing table:** [`reference.md`](skills/process-router/reference.md)

**Also in:** [`.ai/START_HERE.md`](START_HERE.md) §2 (resume) and §10 (FAQ)

---

## What it is

`process-router` is a **read-only signpost** - not a worker skill.

It answers: *"Which skill, guide, or standard should I open for this question?"* and gives you the exact `@` command to run next. It does **not** write files, implement code, create SPECs, or run checklists.

> **Don't know which skill to run?** Use `@ai-director - <describe what you want>` and let it route for you. If the work spans `.ai` + `.ai.ui` + `.ai.biz`, use `@x-director - <describe what you want>`.

```text
You ask a question
       ↓
@process-router - <question>
       ↓
"Run @db-migration create - …" + links to skill.md / guide
       ↓
You invoke THAT skill to do the work
```

## What it is not

| | process-router | Execution skills (e.g. code-implementation) |
|---|---|---|
| Writes HANDOFF / NEXT | No | Yes (when closing / completing) |
| Runs tests or gates | No | Yes |
| Creates SPECs or migrations | No | Yes (feature-spec, db-migration) |
| Pastes long rule text | No - links only | Reads and applies standards |

For a **one-paragraph repo snapshot** ("where am I right now?"):

```text
@session-control status  +  .work/context/HANDOFF.md  +  .work/plans/NEXT.md
```

Use `@process-router` for *how-to* questions; use the line above for *where am I*.

---

## How to invoke

```text
@process-router - how do I add a database migration?
@process-router ask - which concept prompt for an AI-assisted PR?
@process-router route - I'm ready to code M1, what do I run first?
@process-router - what's the difference between plan-foundation and plan-master?
@process-router - how do I set up Agent OS in a new repo?
@process-router help
```

The verb is optional - `@process-router - <question>` is enough. Aliases: `ask`, `where`, `how`.

---

## When to use it

| Situation | Use |
|-----------|-----|
| First-time / empty `.work` | `@project-bootstrap init` · `bash templates/bootstrap.sh` |
| Lost in the workflow | `@process-router - I'm lost` |
| How-to for a specific step | `@process-router - how do I fix NEXT.md?` |
| Which concept (MOD) applies | `@process-router - AI-assisted PR, which prompt?` |
| Explain skill boundaries | `@process-router - foundation vs master plan?` |
| Don't know the right skill (free-text) | `@ai-director - <describe what you want>` · `@x-director - <describe what you want>` (cross-framework) |
| Know exactly what's next | `@session-control status` + `.work/context/HANDOFF.md` + `.work/plans/NEXT.md` |

---

## Readiness states (quick reference)

`foundation-complete → plan-master-ready → implementation-ready`. Only `@plan-master status` certifies **implementation-ready**. Full table + gates: [`.ai/skills/SKILL_DEPENDENCIES.md`](skills/SKILL_DEPENDENCIES.md).

---

## Related skills (execution layer)

| Skill | Role |
|-------|------|
| `session-control` | Open/close session; HANDOFF + NEXT |
| `plan-foundation` | Foundation P0–P6; plan-master-ready |
| `plan-master` | Master plan; implementation-ready |
| `code-implementation` | Iteration tasks, task gates, complete |
| `code-verify` | Milestone / uncommitted / last audits |
| `feature-spec` | Author/review SPECs |
| `concept-run` | Run MOD-01…06 prompts |
| `db-migration` | Idempotent SQL scripts |
| `dev-stack` | Local Docker helper |

Full registry: [`.ai/skills/README.md`](skills/README.md)

---

## `.ai/` vs `.work/`

- **`.ai/`** - agnostic skills, standards, concepts, guides (including this doc and `process-router` skill).
- **`.work/`** - project plans, SPECs, ADRs, prompts, HANDOFF (see [`.work/README.md`](.work/README.md) at repo root).

The router links to both layers but never duplicates their content.
