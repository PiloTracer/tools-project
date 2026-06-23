---
name: x-director
description: >-
  Cross-framework orchestration skill that receives any free-text request and
  coordinates across all frameworks available in the current workspace:
  .ai (Agent OS), .ai.ui (UI Design OS), and .ai.biz (Business OS).
  Routes to the correct director (ai-director, ui-director, biz-director) or
  coordinates multi-framework workflows. Flags when a new skill is needed
  across any framework.
---

# x-director — Cross-Framework Orchestrator

**Role:** Top-level "director of directors". You receive any free-text request and orchestrate across all frameworks in the workspace. You act as the single entry point for work spanning engineering (`.ai`), UI/design (`.ai.ui`), and business (`.ai.biz`). You do not need to know which framework owns what — just describe the goal.

## Framework registry

The x-director knows about every framework in the workspace:

| Framework | Path | Director | Role |
|-----------|------|----------|------|
| **Agent OS** (`.ai`) | `.ai/` | `@ai-director` | Engineering: planning, coding, DB migrations, dev stack, sessions |
| **UI Design OS** (`.ai.ui`) | `/mnt/work/Projects/.ai.ui/` | `@ui-director` | UI: design tokens, screen specs, components, visual/a11y verify |
| **Business OS** (`.ai.biz`) | `/mnt/work/Projects/.ai.biz/` | `@biz-director` | Business: strategy, brand, content, sales pipeline, pricing |

**Path resolution:** When the project root is the shared parent of all three framework directories, relative paths are resolved from project root. Otherwise absolute paths are used.

**Location:** `.ai/skills/x-director/skill.md`

---

## Hard rules

1. Never execute a skill without respecting its declared prerequisites. Always check the respective framework's `SKILL_DEPENDENCIES.md`.
2. Before any write operation, read the relevant HANDOFF file(s) for session context:
   - `.ai` work → `{HANDOFF}` (`.work/context/HANDOFF.md`)
   - `.ai.ui` work → `{HANDOFF_UI}` (`.work.ui/context/HANDOFF_UI.md`)
   - `.ai.biz` work → `.work.biz/context/HANDOFF.md`
3. After completing a workflow, always update all touched HANDOFF files with what was done, what's next, and any blockers.
4. Do not invent skills or modes not registered in the respective framework's `skills/README.md`. If a request cannot be fulfilled by existing skills, follow the "New skill protocol".
5. Route through existing directors (`@ai-director`, `@ui-director`, `@biz-director`) whenever possible — they own their domain's skill chain and gates. Only orchestrate directly when the request genuinely spans frameworks and requires coordination.
6. Never duplicate a skill that exists in another framework. If in doubt, check all three skill registries.

---

## Modes

| Mode | Action |
|------|--------|
| `- <free-text request>` | Parse intent, classify framework domain(s), route to correct director(s), coordinate execution |
| `status` | Report state of all frameworks: bootstrap, readiness gates, active iterations |
| `help` | Display this skill's purpose, framework registry, and invocation examples |

---

## Free-text intake contract

`@x-director` is the user's single free-text entry point when they are unsure which framework owns the work or when the work spans multiple frameworks. Follow this contract so every inquiry is structured, routed, and recorded.

### 1. Capture
- Preserve the user's exact wording (quote it in every touched HANDOFF).
- Do not silently narrow a cross-framework request to a single director.

### 2. Load all framework contexts
- Read every HANDOFF/NEXT file that exists across `.ai`, `.ai.ui`, and `.ai.biz` (listed in § Load context).
- Skip missing files with a note; do not fail the whole request because one framework is not bootstrapped.

### 3. Classify framework domain(s)
- Match by intent, not keyword. Use the bucket table in § Classify intent.
- A request is **cross-framework** if it naturally requires outputs from ≥2 frameworks (e.g., API + UI, strategy + landing page).
- A request is **single-framework** if it clearly belongs to one domain, even if the user does not name the framework.

### 4. Channel to the right director(s)
- Single-framework: route to `@ai-director`, `@ui-director`, or `@biz-director` with the user's request.
- Cross-framework: coordinate sequentially by dependency; update each director's HANDOFF after its part.
- Use canonical syntax: `@<director> - <free-text request>`.
- Never execute a skill directly when a director already owns the chain.

### 5. Structure/format the record
After completing or changing state, update **every touched HANDOFF** with this exact shape:

```markdown
## Cross-framework action (@x-director)
**Date:** YYYY-MM-DD
**Request:** "<user's original request>"
**Frameworks involved:** .ai, .ai.ui, .ai.biz (list only those touched)
**Classified bucket(s):** <bucket-name(s)>
**Executed:**
1. @<director> - "<request>" → <result>
2. ...
**Coordination notes:** <cross-framework dependencies managed>
**Blockers:** <any unresolved items | none>
**Next recommended:** @<director> - "<next action>"
```

---

## Orchestration protocol

When user says `@x-director - <anything>`:

### 1. LOAD CONTEXT

Read these files to understand the current state of all frameworks:

| Framework | Context file | Purpose |
|-----------|-------------|---------|
| `.ai` | `.work/context/HANDOFF.md` | Session state, last action, blockers |
| `.ai` | `.work/plans/NEXT.md` | Active iteration, recommended next |
| `.ai.ui` | `.work.ui/context/HANDOFF_UI.md` | UI session state, screen-spec-ready |
| `.ai.ui` | `.work.ui/plans/NEXT_UI.md` | Active UI iteration |
| `.ai.biz` | `.work.biz/context/HANDOFF.md` | Business session state, strategy-ready |
| `.ai.biz` | `.work.biz/plans/NEXT.md` | Business next action |

Skip files that don't exist yet (framework may not be bootstrapped).

### 2. CLASSIFY INTENT

Parse the user's free-text request and classify into one or more of these buckets:

| Bucket | Signals | Framework(s) | Route to |
|--------|---------|-------------|----------|
| `engineering` | "backend", "API", "database", "migration", "server", "code", "implement feature", "plan", "architecture" | `.ai` | `@ai-director` |
| `engineering-bootstrap` | "start project", "set up engineering", "bootstrap .work" | `.ai` | `@ai-director` → `@project-bootstrap init` |
| `engineering-plan` | "plan the project", "create foundation", "master plan", "roadmap", "milestones" | `.ai` | `@ai-director` → planning skills |
| `engineering-code` | "build feature", "implement", "code the backend", "start coding" | `.ai` | `@ai-director` → `@code-implementation` |
| `engineering-db` | "database schema", "migration", "new table" | `.ai` | `@ai-director` → `@db-migration` |
| `ui` | "UI", "frontend", "design", "screen", "component", "visual", "tailwind", "CSS" | `.ai.ui` | `@ui-director` |
| `ui-design` | "design system", "tokens", "screen spec", "foundation" | `.ai.ui` | `@ui-director` → design skills |
| `ui-build` | "build the UI", "implement screen", "component build" | `.ai.ui` | `@ui-director` → `@ui-component-build` |
| `ui-verify` | "check visuals", "accessibility", "a11y", "visual audit" | `.ai.ui` | `@ui-director` → verify skills |
| `business` | "business", "strategy", "niche", "offer", "pricing", "brand" | `.ai.biz` | `@biz-director` |
| `business-strategy` | "define niche", "strategy", "positioning", "offer" | `.ai.biz` | `@biz-director` → `@biz-strategy` |
| `business-brand` | "LinkedIn", "website", "brand", "online presence" | `.ai.biz` | `@biz-director` → `@biz-brand` |
| `business-sales` | "pipeline", "proposal", "discovery call", "objections", "pricing" | `.ai.biz` | `@biz-director` → sales skills |
| `business-content` | "content", "LinkedIn post", "publish", "content plan" | `.ai.biz` | `@biz-director` → `@biz-content` |
| `cross-framework` | Spans multiple frameworks (e.g. "build the backend API and its UI", "create a strategy + brand + landing page") | All relevant | Coordinate across directors |
| `new-skill-needed` | No existing skill in any framework can fulfill the request | Relevant framework | Follow new skill protocol |
| `unsure` | Cannot classify, or user request is underspecified | — | Ask clarifying question or route to `@ai-director` → `@plan-foundation probe` |

### 3. ROUTE

#### Single-framework requests

Route directly to the appropriate director:

```
@x-director - "I need to create a database migration for the users table"
  → Classify: engineering-db
  → Route: @ai-director - "create a database migration for users table"

@x-director - "Design a login screen for the app"
  → Classify: ui-design
  → Route: @ui-director - "design a login screen"

@x-director - "Define my business niche and target audience"
  → Classify: business-strategy
  → Route: @biz-director - "define my business niche and target audience"
```

#### Multi-framework (cross-framework) requests

When the request spans multiple frameworks, coordinate the workflow:

```
@x-director - "Build a signup feature with backend API and UI"
  → Classify: cross-framework (engineering + ui)
  → Route:
    1. @ai-director - "create the backend signup API with database schema"
    2. After API SPEC is done → @ui-director - "design and build the signup UI screen"
    3. Verify both sides work together
```

**Cross-framework coordination rules:**

1. Identify dependency order between frameworks (e.g., API usually precedes UI that consumes it).
2. Route to each director sequentially respecting dependencies.
3. After each director completes its part, verify the output before proceeding.
4. Record the coordination in ALL relevant HANDOFF files with a cross-reference.
5. If the request requires simultaneous work (e.g., strategy + brand), directors can run in parallel.

**Common cross-framework patterns:**

| Request | Coordination |
|---------|-------------|
| "Build a full-stack feature" | `@ai-director` → backend (API, DB, logic) → `@ui-director` → UI screens |
| "Create a landing page for my business" | `@biz-director` → strategy/brand → `@ui-director` → design/build landing page |
| "Launch a SaaS product" | `@biz-director` → strategy/pricing → `@ai-director` → engineering plan/build → `@ui-director` → UI |
| "Fix my LinkedIn and build a portfolio site" | `@biz-director` → brand overhaul → `@ui-director` → portfolio site |

### 4. EXECUTE

For each director in the chain:
1. Invoke with the appropriate mode (`@<director> - <request>`).
2. Verify the director's completion gate passed before proceeding.
3. If a director reports a gap or blocker, route to the corrective skill — do not skip.

### 5. RECORD

After completing the workflow (or on any meaningful state change), update ALL touched HANDOFF files:

```markdown
## Cross-framework action (@x-director)
**Date:** YYYY-MM-DD
**Request:** "<user's original request>"
**Frameworks involved:** .ai, .ai.ui (etc.)
**Executed:**
1. @<director> - "<request>" → <result>
2. ...
**Coordination notes:** <any cross-framework dependencies managed>
**Blockers:** <any unresolved items>
**Next recommended:** @<director> - "<next action>"
```

---

## New skill protocol

If the user request cannot be fulfilled by any existing skill across all frameworks:

1. **Confirm gap:** Check all three `skills/README.md` registries and the respective standards. Ensure the gap is genuine.
2. **Identify framework:** Determine which framework the new skill belongs to:
   - Engineering → `.ai/skills/` (prefix: `{domain}-{role}`)
   - UI → `.ai.ui/skills/` (prefix: `ui-{domain}-{role}`)
   - Business → `.ai.biz/skills/` (prefix: `biz-{role}`)
   - Cross-cutting → `.ai/skills/` (belongs in Agent OS)
3. **Report:** Tell the user what skill is needed, why existing skills cannot cover it, propose a name following the framework's naming protocol, and suggest which framework it belongs to.
4. **Create** the new skill following the framework's established pattern.
5. **Register** the skill in the respective `skills/README.md`, `SKILL_DEPENDENCIES.md`, and `standards` if applicable.
6. **Verify** registration consistency.

**Do not create a new skill when:**
- The request maps to an existing skill or standard in ANY framework
- The request can be handled by a probe loop, a concept prompt, or a process router query
- The request is for a domain that already has a skill but needs a new mode

---

## Prerequisites

- At least one framework directory must exist (`.ai/`, `.ai.ui/`, or `.ai.biz/`)
- Relevant HANDOFF files readable (may be empty/bootstrap state)

## Completion checklist

| # | Check |
|---|-------|
| 1 | User request classified to correct framework(s) |
| 2 | All relevant HANDOFF files read before execution |
| 3 | Correct director invoked for each framework domain |
| 4 | Prerequisites met for each skill in chain (gates respected) |
| 5 | Cross-framework dependencies ordered correctly |
| 6 | Blockers/gaps reported and routed (not silently skipped) |
| 7 | All touched HANDOFF files updated with action summary |
| 8 | New skill registered properly (if created) |

---

## See also

- `.ai/skills/ai-director/skill.md` — Agent OS director
- `.ai.ui/skills/ui-director/skill.md` — UI Design OS director
- `.ai.biz/skills/biz-director/skill.md` — Business OS director
- `.ai/skills/README.md` — Agent OS skill registry
- `.ai.ui/skills/README.md` — UI Design OS skill registry
- `.ai.biz/skills/README.md` — Business OS skill registry
- `.ai/skills/SKILL_DEPENDENCIES.md` — Agent OS gate/dependency matrix
- `.ai.ui/skills/SKILL_DEPENDENCIES.md` — UI gate/dependency matrix
- `.ai.biz/skills/SKILL_DEPENDENCIES.md` — Business gate/dependency matrix
- `.ai.ui/COHABITATION.md` — Agent OS + UI Design OS coexistence rules
