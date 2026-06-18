# Agent OS - process framework for coding agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Last commit](https://img.shields.io/github/last-commit/PiloTracer/.ai)
![Stars](https://img.shields.io/github/stars/PiloTracer/.ai?style=social)

> Your AI coding agent forgets context between sessions, contradicts past decisions, claims tests pass when they fail, and starts coding before the plan exists. **Agent OS fixes that** with a small set of repeatable **skills**, binding **standards**, and a tiny **project-memory** folder.

**Works with:** Cursor, Claude Code, Codex, opencode, and any agent that reads project files.

```bash
bash .ai/templates/bootstrap.sh    # 30-second setup, any repo
```

Then in chat:

```text
@session-control start             # bookend the day
@plan-foundation greenfield        # blueprint → master plan → milestones → code
@session-control close             # update HANDOFF · draft commit message
```

**Lost?** → [`START_HERE.md`](START_HERE.md) · **All commands** → [Skills at a glance](#skills-at-a-glance) · **First time here?** → [How this compares](#how-this-compares)

---

## What you get

- **Skills** - `@session-control`, `@code-implementation`, `@plan-foundation`, … run the playbook (14 skills in total).
- **Standards** - binding contracts (CONVENTIONS, FEATURE_STANDARD, observability, security) keep agent output honest.
- **`.work/`** - the project's memory: plans, SPECs, ADRs, `HANDOFF.md`, `NEXT.md`. Survives session boundaries.
- **Gates** - `plan-master-ready`, `implementation-ready`, milestone verify; skip a step and the agent **stops** with a redirect.

Result: less re-prompting, fewer "where were we?" threads, a loop you can run **start → ship → hand off** every session.

**Fast start on an existing repo?** → [`docs/adoption/minimal-adoption.md`](docs/adoption/minimal-adoption.md) (lite path vs full pipeline).

---

## Path convention (read this once)

Docs often show paths like `.ai/START_HERE.md`. That applies when Agent OS lives **inside** an application repo. When the **git root is this framework repository**, the same files sit at the repo root **without** the `.ai/` prefix.

| Layout | Where Agent OS lives | Example |
|--------|----------------------|---------|
| **Nested** (typical) | `your-app/.ai/` | `.ai/START_HERE.md`, `.ai/skills/` |
| **Self-hosted** (this repo) | git root *is* the tree | `START_HERE.md`, `skills/` |

Bootstrap always runs from the **application repo root** (parent of `.ai/`): `bash .ai/templates/bootstrap.sh`.

**This framework repo:** `.cursorrules` and `DOCS_TECH_STACK.md` at the root intentionally keep unfilled `REPLACE:` tokens - they are templates, not a misconfigured product.

---

## How this compares

| Tool | What it does | Where Agent OS adds value |
|------|--------------|---------------------------|
| `.cursorrules` / `AGENTS.md` | Static rules for one tool | Adds **gated workflow + memory + standards** on top |
| Plain prompts | Per-task instructions | Adds **repeatable skills** with prerequisite gates |
| Linear / Jira | Human-only planning | Plans live **next to code** as Markdown the agent reads |
| GitHub Copilot / inline LLM | Single-turn completion | Cross-session continuity via `.work/HANDOFF.md` + `NEXT.md` |
| Custom system prompts | Per-developer drift | One repo-wide, tool-agnostic contract checked into git |

---

## Bird's-eye - how to use Agent OS

Agent OS is a **gated pipeline**: each stage unlocks the next. Skills enforce the gates; if you skip a step, the agent should **stop** and tell you what to run instead ([`skills/SKILL_DEPENDENCIES.md`](skills/SKILL_DEPENDENCIES.md)).

### Readiness states (do not skip or confuse)

| State | You get there with | What it unlocks |
|-------|-------------------|-----------------|
| *(scaffold)* | `@project-bootstrap init` | Foundation planning, session files |
| **foundation-complete** | `@plan-foundation greenfield` (P0–P6 done) | `@plan-foundation certify` |
| **plan-master-ready** | `@plan-foundation certify plan-master-ready` | `@plan-master greenfield` / `continue` / `revise` |
| **implementation-ready** | `@plan-master status` (master plan **Approved**) | `@code-implementation start` / `continue` (broad coding) |

**plan-master-ready ≠ ready to code everything.** It means the blueprint is solid enough for a master roadmap. Broad implementation needs **implementation-ready** (or an explicit milestone waiver in `.work/context/HANDOFF.md`).

### Full flow (once per project → every day → per milestone)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  ONCE PER PROJECT - planning gates (no application code yet)                 │
└─────────────────────────────────────────────────────────────────────────────┘

  @project-bootstrap init
        │
        │  Creates: .cursorrules · DOCS_TECH_STACK.md · .work/ skeleton
        │  (scaffold only - fill REPLACE: tokens; no planning gates)
        ▼
  @plan-foundation greenfield
        │
        │  Produces: foundation docs 01–04 · ADRs · SPECs · registries
        │  State: foundation-complete
        ▼
  @plan-foundation certify plan-master-ready
        │
        │  Deep consistency check (+ plan-master integrity on foundation)
        │  State: plan-master-ready  (recorded in HANDOFF)
        ▼
  @plan-master greenfield  │  @plan-master continue
        │
        │  Produces: .work/plans/full/*-full-plan.md  (Draft → Approved)
        ▼
  @plan-master status
        │
        │  State: implementation-ready: yes  (only this skill scores it)
        ▼

┌─────────────────────────────────────────────────────────────────────────────┐
│  EVERY SESSION - bookends (planning or coding)                               │
└─────────────────────────────────────────────────────────────────────────────┘

  @session-control start          ← load HANDOFF · NEXT · UNKNOWNS · rules
        │
        │  … your work (planning skills above, or implementation below) …
        ▼
  @session-control close          ← refresh HANDOFF + NEXT; draft commit message
  @session-control close commit   ← optional: stage + commit
  @session-control close commit push

┌─────────────────────────────────────────────────────────────────────────────┐
│  PER MILESTONE M{N} - repeat until the master plan is done                  │
└─────────────────────────────────────────────────────────────────────────────┘

  @code-implementation plan - M{N}
        │  Writes ## Current iteration in .work/plans/NEXT.md from master plan
        ▼
  @code-implementation start
        │  Read SPECs + standards; first task in-progress
        ▼
  @code-implementation continue     ◄──┐
        │  Per task: implement → task gate (tests · lint · type)  │
        │  Schema change? → @db-migration create - …              │
        └────────────────────────────────────────────────────────┘
        ▼
  @code-verify milestone            ← plan + SPEC audit before you claim done
        ▼
  @code-implementation complete     ← archive iteration; update HANDOFF / NEXT
        │
        └──► next M{N+1} or @session-control close

┌─────────────────────────────────────────────────────────────────────────────┐
│  ANYTIME - supporting skills (invoke when the work needs them)               │
└─────────────────────────────────────────────────────────────────────────────┘

  @process-router - <question>      lost? read-only signpost (no file writes)
  @feature-spec create - <slug>     feature SPEC (see Skills at a glance)
  @concept-run list | - MOD-0N      architecture prompts MOD-01…06 (MOD-06 default for agent code)
  @dev-stack                        Docker dev helper script (bin/start.sh)
  @code-verify uncommitted | last   commit hygiene (milestone mode is in the loop above)
```

### One-line cheat path (copy into chat)

```text
@project-bootstrap init
@plan-foundation greenfield → @plan-foundation certify plan-master-ready
@plan-master greenfield → @plan-master status
@session-control start
@code-implementation plan - M1 → start → continue
@code-verify milestone → @code-implementation complete
@session-control close
```

**Jump ahead?** If planning is already done, open at [`§ 3 · Open a coding session`](#3--open-a-coding-session-every-day) below. If you only need setup files, see [First-time setup](#first-time-setup-human-or-agent).

### Skills at a glance

All **14** skills live under [`skills/`](skills/README.md). Invoke as `@<skill-id>` plus a mode (e.g. `@plan-foundation status`).

| Skill | One line | Typical invoke |
|-------|----------|----------------|
| **project-bootstrap** | Scaffold `.work/`, `.cursorrules`, stack doc from templates | `init` · `status` |
| **plan-foundation** | Foundation docs 01–04, ADRs, SPECs, registries; certifies **plan-master-ready** | `greenfield` · `probe` · `status` · `certify plan-master-ready` |
| **plan-master** | Master plan with milestones; certifies **implementation-ready** | `greenfield` · `continue` · `probe` · `status` · `revise` |
| **plan-verify** | Plan audits; **brownfield** align without formal plan-foundation/master | `brownfield` · `foundation` · `master` · `alignment` |
| **plan-repair** | Fix gaps; synthesize `.work/` from code/README/ROADMAP | `brownfield` · `foundation - <goal>` · `master - <goal>` |
| **session-control** | Session bookends; updates HANDOFF + NEXT | `start` · `close` · `status` |
| **code-implementation** | Run one milestone from `NEXT.md`; per-task gates | `plan - M{N}` · `start` · `continue` · `continue - N` · `complete` |
| **code-verify** | Audits (not implementation): milestone, dirty tree, last commit/push | `milestone` · `uncommitted` · `last` |
| **code-repair** | Fix verifier/migration/SPEC findings; re-verify before pass | `repair - from uncommitted` · `repair - custom - …` · `status` |
| **feature-spec** | Triage, author, review, or amend feature SPECs | `intake - <free sentence>` · `create - <slug>` · `review - <path>` · `amend - <slug>` |
| **concept-run** | Run MOD-01…06 architecture/NFR prompts | `list` · `status` · `run - MOD-06` (required for agent-assisted code) |
| **db-migration** | Idempotent numbered SQL scripts (no Alembic chain) | `init` · `create - <description>` · `run` · `status` · `verify` |
| **dev-stack** | Generate or update isolated Docker `bin/start.sh` | `init` · `status` |
| **process-router** | Read-only: “how do I…?” → right skill or guide | `- <question>` · `help` |

Gates between skills: [`skills/SKILL_DEPENDENCIES.md`](skills/SKILL_DEPENDENCIES.md).

---

## First-time setup (human or agent)

Cursor and compatible agents read **`.cursorrules` at the repository root** (sibling to `.ai/` in an application repo, or at this root when Agent OS is the git root).

**Recommended - one command from repo root:**

```bash
bash .ai/templates/bootstrap.sh
```

Or in chat: **`@project-bootstrap init`**

This creates (without overwriting existing files):

- `.cursorrules` from [`templates/cursorrules.template`](templates/cursorrules.template)
- `DOCS_TECH_STACK.md` from [`templates/DOCS_TECH_STACK.md.template`](templates/DOCS_TECH_STACK.md.template)
- `.work/` skeleton (HANDOFF, NEXT, registries, empty plan folders)

Then:

1. Replace every **`REPLACE:`** token in `.cursorrules` ([checklist](templates/README.md)).
2. Customize [`.ai/standards/`](standards/) templates and point `.cursorrules` at your dated filenames.
3. Run **`@plan-foundation greenfield`** (foundation docs 01–04).
4. Keep a **single** rules file - do not add `AGENTS.md` unless your team standardizes on it.

| Situation | What to do |
|-----------|------------|
| **New adoption** | `bootstrap.sh` or `@project-bootstrap init` |
| **Existing `.cursorrules`** | `@project-bootstrap status` - merge manually; do not blind overwrite |

More: [`templates/README.md`](templates/README.md) · skill: [`skills/project-bootstrap/`](skills/project-bootstrap/skill.md)

---

## Lifecycle at a glance (full command sequence)

The bird's-eye flow above is the conceptual map. Below is the **literal command sequence** to copy into chat. For "what each command does" detail, open the skill: `skills/<name>/skill.md`.

```text
# Once per project (planning)
@plan-foundation greenfield
@plan-foundation certify plan-master-ready
@plan-master greenfield
@plan-master status                    # → implementation-ready: yes

# Every day (session)
@session-control start
@code-implementation status

# Per milestone (replace M1 with the active milestone from NEXT.md)
@code-implementation plan - M1
@code-implementation start
@code-implementation continue          # or: continue - 5  /  continue - until blocked

# Schema change mid-task (only when the task touches DB)
@db-migration create - <short description>

# Close milestone
@code-verify milestone
@code-implementation complete

# End session
@session-control close                 # message only
@session-control close commit          # add + commit safe dirty paths
@session-control close commit push     # also push
```

**Detail per command:** `skills/<name>/skill.md` (skill body holds the protocols; `reference.md` holds examples).
**Operator decision tree:** [`START_HERE.md`](START_HERE.md) — answers "what do I invoke right now?".
**Process Q&A:** `@process-router - <question>`.

---

## Quick commands (cheat sheet)

| Moment | Command |
|--------|---------|
| Where am I? | `@session-control status` |
| How do I…? | `@process-router - <question>` |
| Stuck on process | [`START_HERE.md`](START_HERE.md) |
| Dirty tree before commit | `@code-verify uncommitted` |
| After you committed | `@code-verify last` |

---

## Pain → fix

| Pain | Fix |
|------|-----|
| Re-explaining workflows every chat | **Skills** - `@session-control`, `@code-implementation`, … |
| Drifty code style | **Standards** - conventions, SPEC template, directory map |
| Architecture surprises at AI speed | **Concepts** MOD-01…06 - run before big splits |
| Context evaporates overnight | **`.work/`** + session bookends |

---

## How it fits together

```text
  You + agent (@skills)                 Project truth (.work/)
       │                                      │
       │   plan-foundation → plan-master      │  foundation/ · full/
       │   code-implementation → verify       │  features/ · HANDOFF · NEXT
       ▼                                      ▼
  .ai/  skills · standards            .work/  plans · SPECs · ADRs
        concepts · guides                     session + iteration state
       │                                      │
       └──────────── @session-control ────────┘
```

| Layer | Role |
|-------|------|
| **`.ai/`** | *How* we work - skills, standards, concepts, guides (copy to other repos). |
| **`.work/`** | *What* this project decided - plans, SPECs, HANDOFF, NEXT. |
| **`.cursorrules`** | Binding agent rules at the **repo root** ([template](templates/cursorrules.template)). |

Skill prerequisite gates: [`skills/SKILL_DEPENDENCIES.md`](skills/SKILL_DEPENDENCIES.md).

---

## What’s inside `.ai/`

| Folder | Role |
|--------|------|
| [`skills/`](skills/README.md) | Executable playbooks - full registry |
| [`standards/`](standards/) | Engineering contract **templates** (customize per project) |
| [`concepts/`](concepts/README.md) | MOD-01…06 architecture prompts |
| [`docs/guides/workflows/`](docs/guides/workflows/README.md) | Tutorials + artifact matrix |
| [`docs/integration/`](docs/integration/) | Vendor mirror layout + `MANIFEST` template (project adds artifacts) |
| [`templates/`](templates/README.md) | **`cursorrules.template`** - copy to repo root as `.cursorrules`; **`.ai/.cursorrules`** mirrors the template when present (keep in sync) |
| `plans/`, `features/`, … | **Pointers only** → `.work/` |
| [`.quick/`](.quick/README.md) | Copy-paste cheat sheets for common workflows |

---

## Required reads (when work is active)

1. [`START_HERE.md`](START_HERE.md)
2. **`.cursorrules`** (repo root - install via [First-time setup](#first-time-setup--install-cursorrules-human) if missing)
3. `.work/context/HANDOFF.md`
4. `.work/plans/NEXT.md`
5. `.work/plans/foundation/*-01-*-initial-scope.md` when present
6. For code: customize then use your dated standards under `standards/` (templates ship as `20260517-*.md` - rename or copy after replacing `REPLACE:` tokens)

Agent rules file: **`.cursorrules` only** - do not add `AGENTS.md` without owner approval.

---

## Copy to another project

1. Copy the whole **`.ai/`** tree (includes `templates/`).
2. At the **new repo root**, run **`bash .ai/templates/bootstrap.sh`** (or `@project-bootstrap init`).
3. Fill **`REPLACE:`** tokens in `.cursorrules`; customize **standards** under `.ai/standards/`.
4. Follow the [bird's-eye flow](#birds-eye--how-to-use-agent-os): foundation → certify → master plan → status → daily session + milestones.

Template sources: [`templates/work/`](templates/work/). This repo includes a demo [`.work/`](.work/) skeleton when Agent OS is the git root.
