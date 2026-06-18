---
name: plan-repair
description: >-
  Remediate planning gaps from plan-verify, brownfield adoption (no prior formal
  plan-foundation or plan-master), or explicit change requests. Synthesizes and
  aligns .work/ artifacts to the .ai framework from repo evidence; may delegate
  to plan-foundation continue or plan-master revise when formal paths apply.
  Use plan-repair foundation, master, brownfield, or open-language plan fixes.
---

# plan-repair

Remediation layer for **planning documentation**. **Implements plan fixes**; does not replace detection (`plan-verify`) or application code repair (`code-repair`).

**Pairs with:** `plan-verify` (findings + mandatory re-verify), `plan-foundation`, `plan-master`, `code-implementation` (regenerate iteration after master repair), `feature-spec`, `session-control`, `.cursorrules`.

**Canonical path:** `.ai/skills/plan-repair/skill.md` · **Invocation examples:** `reference.md`

**Registry:** [`.ai/skills/SKILL_DEPENDENCIES.md`](../SKILL_DEPENDENCIES.md).

**Hard rules:**

- **Findings in, evidence out** — start from F* rows (verify report, fresh `@plan-verify`, or decomposed user brief). No plan edits without documented findings or an explicit same-message goal.
- **Re-verify mandatory** — after repairs, re-run the **same** `@plan-verify` mode that sourced the findings ([R4](#r4--re-verify-mandatory)).
- **Delegate mutating upstream work** — follow `plan-foundation` / `plan-master` protocols for continue, certify, greenfield, revise; plan-repair **coordinates** and records deltas, it does not invent alternate plan formats.
- **Brownfield allowed** — may **create or align** planning artifacts when `@plan-foundation` / `@plan-master` were **never run formally**; synthesize from README, code, ADRs, ROADMAP, issues. Formal gates (certify, Approved) are **targets**, not blockers for starting repair ([Brownfield repair](#brownfield-repair-protocol)).
- **Synthesis headers** — files created in brownfield mode must include `**Brownfield synthesis YYYY-MM-DD:**` and label inferred content **Inference** until owner confirms.
- **No application code** unless the user explicitly requests implementation in the same message.
- **No secrets** in plan prose; no PII in examples.
- Does **not** own HANDOFF/NEXT bookends unless the user asks (route to `session-control`).
- Every **repair** ends with a **Completion checklist** — `pass` | `fail` | `skip` with evidence.

---

## Parse invocation

Normalize to **mode** + optional **source** or **goal text** (after `-`). ASCII hyphen only.

| User says | Mode | Action |
|-----------|------|--------|
| `@plan-repair` | repair | [Repair protocol](#repair-protocol) — infer target |
| `@plan-repair` **repair** | repair | Same |
| `@plan-repair` **foundation** | repair (foundation) | [Foundation repair](#foundation-repair) |
| `@plan-repair` **repair** - **foundation** - \<goal\> | repair (foundation) | Foundation repair with stated delta |
| `@plan-repair` **master** | repair (master) | [Master repair](#master-repair) |
| `@plan-repair` **repair** - **master** - \<goal\> | repair (master) | Master repair with stated delta |
| `@plan-repair` **repair** - **from** **foundation** | repair (foundation) | Findings from `@plan-verify foundation` |
| `@plan-repair` **repair** - **from** **master** | repair (master) | Findings from `@plan-verify master` |
| `@plan-repair` **repair** - **from** **alignment** | repair (alignment) | Findings from `@plan-verify alignment` |
| `@plan-repair` **repair** - **from** **coverage** | repair (coverage) | Findings from `@plan-verify coverage` |
| `@plan-repair` **repair** - **custom** - \<brief\> | repair | User brief → F* table → targeted layer |
| `@plan-repair` **brownfield** | brownfield | [Brownfield bootstrap](#brownfield-bootstrap) |
| `@plan-repair` **brownfield** - **foundation** | brownfield | Scaffold + foundation artifacts |
| `@plan-repair` **brownfield** - **master** | brownfield | Foundation gate + master plan bootstrap |
| `@plan-repair` **fix** - … | repair | Alias for **repair** |
| `@plan-repair` **status** | status | [Status protocol](#status-protocol) — read-only |

**Open language examples (map to rows above):**

```text
@plan-repair foundation - we will require SSO for all desk users
@plan-repair master - adjust M3 to add observability tasks before domain APIs
@plan-repair - fix foundation so we can certify plan-master-ready
```

**Free request → framework alignment:** When findings are sourced from **open language** (custom brief, goal text after `-`, or implicit layer resolution), run **[R0-free](#r0-free---framework-alignment-free-lang-requests-only)** before triage. This decomposes the free text into a **Framework alignment map** — identifying which `.ai` concepts, standards, SPECs, foundation/master docs, and registries the request implicates. The map feeds F* rows (each gains a `Framework ref` column) and constrains the R2 repair plan to framework-consistent delegate targets.

**Default target when omitted:**

1. Latest **fail** from `@plan-verify` in the last 3 assistant turns → matching **from** mode.
2. Else if user message names **foundation** / **master** / **alignment** / **NEXT** / **full plan** → that layer.
3. Else if `{PLANS_ROOT}/foundation/` incomplete → **foundation**.
4. Else if no `*-full-plan.md` → **master** (if plan-master-ready) else **foundation**.
5. Else if repo has code or legacy docs → **brownfield**.
6. Else ask once: **Q:** Repair foundation, master plan, alignment, or brownfield (full framework align)?

**Brownfield default:** When BF0 = yes (see `plan-verify` § Brownfield detection) and user did not name a layer → `@plan-repair brownfield` (full align pass).

---

## Repair protocol

### R0 - Findings intake (mandatory)

| ID | Source | Severity | Finding | Affected paths | Fix strategy | Framework ref |
|----|--------|----------|---------|----------------|--------------|---------------|
| F1 | plan-verify foundation | fail | … | … | foundation continue / new doc | `—` (verify-sourced) |

`Framework ref` is populated when findings come from **open language** (custom brief, goal text after `-`) or **brownfield** discovery. Sources from `@plan-verify` reports (foundation / master / alignment) may leave it `—` (verify-sourced) since the verify report already frames findings in framework terms. Must cite at least one: standard, concept MOD id, foundation doc id, SPEC path, master plan §, or registry.

**Obtain findings by:**

1. Chat verify report,
2. **Run** `@plan-verify <mode>` now,
3. User goal after `-` (decompose into F* rows),
4. **Brownfield** discovery table (missing artifacts).

### R0-free - Framework alignment (free lang requests only)

**When:** Findings source is **custom** brief, goal text after `-`, or implicit layer resolution (no verifying report in chat). **Skip** when all F* rows come from a `@plan-verify` or `@db-migration verify` report.

Produce a **Framework alignment map** before the F* triage. This decomposes the free text into `.ai` framework components and ensures the repair stays within framework-consistent paths.

```markdown
### Free request → Framework alignment

**Request:** <paraphrase one line>

| Aspect | Framework component | Artifact path | Action |
|--------|---------------------|---------------|--------|
| <quote/phrase from request> | P0 scope | foundation/*-01-*-scope.md | Add/amend scope statement |
| <…> | FEATURE_STANDARD | standards/*FEATURE_STANDARD* | SPEC needed / amend |
| <…> | CONVENTIONS | standards/*CONVENTIONS* | Naming / layout check |
| <…> | threat-model | standards/*threat-model* | Review surface |
| <…> | MOD-06 | .ai/concepts/ai-amplification/ | Trigger if agent authors plan/docs |
| <…> | P4 cross-cutting | standards/*observability-spec* | Observable from day 1? |
| <…> | ADR | .work/decisions/ | Capture decision |
| <…> | Master plan §19 | .work/plans/full/*-full-plan.md | FR / task delta |
```

**Rules:**
- Minimum 1 component row per distinct framework aspect; omit rows with no plausible connection.
- **Inference** rule: when mapping is probabilistic (e.g. "SSO might need a SPEC"), label the row **Inference** and propose it — do not assume it.
- Cross-reference OPEN OWNER ACTIONS in `{HANDOFF}`; freeze the map before filing F* rows.
- Update the map if triage surfaces new framework connections.

**Triage:**

| Disposition | Action |
|-------------|--------|
| **fix-now** | Agent edits plan docs via upstream skill protocols; must cite Framework ref column |
| **owner** | `UNKNOWNS.md` or HANDOFF § Open owner actions; preserve Framework ref |
| **waiver** | HANDOFF or same-message user approval; note Framework ref |
| **redirect** | Code gap → `@code-repair`; session → `@session-control` |

If **>50%** rows are **owner** without documentation-only request → stop and list owner actions.

### R1 - Context load (mandatory)

| # | Path | When |
|---|------|------|
| 1 | `.cursorrules` | always |
| 2 | `{HANDOFF}` | always |
| 3 | `{ITERATION_CARRIER}` | alignment / master touches iteration |
| 4 | `{PLANS_ROOT}/foundation/*` | foundation |
| 5 | `{PLANS_ROOT}/full/*-full-plan.md` | master |
| 6 | `{PLANS_ROOT}/ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md` | always |
| 7 | `.ai/standards/20260519-MASTER_PLAN_STANDARD.md` | master |
| 8 | Relevant SPECs / ADRs | per F* paths |

Short **assumption ledger** when behavior is inferred from code-only brownfield repos.

### R2 - Repair plan (before edits)

≤15 lines: F* order (sorted by Framework ref → priority), delegate commands (`@plan-foundation continue`, `@plan-master revise - …`), files to create, re-verify mode for R4.

**Fix order:** blockers (bootstrap/HANDOFF) → foundation gates → master plan → alignment (NEXT) → registries.

When an **[R0-free](#r0-free---framework-alignment-free-lang-requests-only)** alignment map was produced, cross-check each repair item against the map's **Framework component** column — a repair that touches a standard must cite that standard path; a repair that alters scope must trace to foundation doc 01.

### R3 - Apply fixes (delegate)

| Layer | Primary delegate | When |
|-------|------------------|------|
| Foundation gaps | `@plan-foundation continue` | Partial P0–P6 |
| New product scope in foundation | Update doc 01 + registries; amend SPECs via `@feature-spec amend` | F* cites scope |
| Certify unlock | `@plan-foundation certify plan-master-ready` | After foundation-complete |
| Master delta | `@plan-master revise - <reason>` | Approved or Draft plan exists |
| New master plan | `@plan-master greenfield` or `continue` | No plan / partial Draft |
| Integrity fail | Fix cited contradictions → `@plan-master integrity` | Before certify/approve |
| NEXT drift only | `@code-implementation plan - M{N}` | After master is truth |
| Missing `.work/` skeleton | `@project-bootstrap init` | Brownfield |

**User goal text** (e.g. `foundation - we will require …`) must appear in:

- Foundation doc 01 scope / assumption ledger, **or**
- New/amended SPEC + ADR as appropriate, **or**
- Master plan FR row + §19 tasks after `@plan-master revise`

Record **Correction YYYY-MM-DD:** notes when editing Approved plans (per fix-existing-plans tutorial).

### R4 - Re-verify (mandatory)

| Repair source | Re-run after fixes |
|---------------|-------------------|
| **from foundation** / **foundation** | `@plan-verify foundation` |
| **from master** / **master** | `@plan-verify master` |
| **from alignment** | `@plan-verify alignment` |
| **custom** | Modes named in brief; minimum one `@plan-verify` pass |
| **brownfield** | `@plan-verify foundation` then `@plan-verify master` when applicable |

**Verdict:**

| Verdict | Meaning |
|---------|---------|
| **repaired** | Re-verify **pass** or **pass with gaps** (waivers documented) |
| **partial** | Some F* fixed; re-verify still **fail** |
| **failed** | Could not fix |
| **nothing to repair** | No findings |

### R5 - Repair report (mandatory)

```markdown
## plan-repair - <foundation | master | alignment | brownfield> - <verdict>

**Date:** <ISO>

### Findings
| ID | Disposition | Status | Evidence | Framework ref |
|----|-------------|--------|----------|---------------|

### Framework alignment (if R0-free ran)
<insert R0-free map or link to it>

### Delegated commands run
- `@plan-foundation …` / `@plan-master …` / `@code-implementation plan - M{N}`

### Completion checklist
| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | R0 findings intake | pass/fail | |
| 2 | R0-free alignment map (when free lang) | pass/skip | |
| 3 | R1 context load | pass/fail | |
| 4 | R2 repair plan (cross-checked vs alignment) | pass/fail | |
| 5 | R3 fixes applied; goal text in target artifacts | pass/fail | |
| 6 | R4 re-verify | pass/fail | |
| 7 | No plan ↔ code layer confusion | pass | |

### Remaining / owner
<list or none>

### Next
@plan-verify <mode> | @plan-foundation certify | @plan-master status | @code-implementation plan - M{N}
```

---

## Foundation repair

**Triggers:** `@plan-repair foundation`, `repair - from foundation`, `repair - foundation - <goal>`, brownfield foundation path.

1. Run [R0–R2](#repair-protocol).
2. If `{HANDOFF}` or `.cursorrules` missing → `@project-bootstrap init` first ([blocked report](#blocked-report-shape)).
3. Follow `@plan-foundation continue` for the **first phase not done**; produce missing artifacts (01–04, ADRs, SPECs, standards) per that skill's GATE checklists.
4. Apply **goal text** to doc 01 + sync `ASSUMPTIONS.md` / `RISK_REGISTRY.md` / `UNKNOWNS.md`.
5. At P3+ with contradictions → `@plan-master integrity` on foundation set.
6. When gates satisfied → offer `@plan-foundation certify plan-master-ready` (user may run in same session if asked).
7. [R4](#r4--re-verify-mandatory) → `@plan-verify foundation`.

**Brownfield (code exists, no formal plan-foundation run):**

- Enter [Brownfield repair protocol](#brownfield-repair-protocol) BR3 instead of blocking on empty phases.
- Do **not** force `@plan-foundation greenfield` questionnaire unless user requests it in the same message.

---

## Master repair

**Triggers:** `@plan-repair master`, `repair - master - <goal>`, `repair - from master`.

### MG1 - Plan-master-ready gate

| Condition | Action |
|-----------|--------|
| **plan-master-ready: yes** | Proceed to MG2 |
| **brownfield: yes** (BF0) | Proceed to MG2 via [BR4](#br4---synthesize-master-plan-no-prior-formal-plan-master); record HANDOFF waiver line; **do not** hard-stop |
| **plan-master-ready: no** and **brownfield: no** | Stop:

```markdown
## @plan-repair master - blocked (prerequisite)

**Required:** plan-master-ready: yes
**Detected:** plan-master-ready: no
**Run first:** `@plan-repair foundation` → `@plan-foundation certify plan-master-ready`
```

Or run **`@plan-repair brownfield`** to align without prior formal foundation.

### MG2 - Apply delta

| Situation | Delegate |
|-----------|----------|
| No `*-full-plan.md` | `@plan-master greenfield` **or** brownfield Draft synthesis ([BR4](#br4---synthesize-master-plan-no-prior-formal-plan-master)) |
| Draft partial plan | `@plan-master continue` |
| Approved or Draft update | `@plan-master revise - <goal from user or F*>` |
| Integrity-only failures | Fix cited sections → `@plan-master integrity` |

**Goal text** must flow into revise reason and plan Decision log / traceability matrix.

### MG3 - Post-repair

- If iteration exists and §19 tasks changed → `@code-implementation plan - M{N}`.
- [R4](#r4--re-verify-mandatory) → `@plan-verify master` (+ `@plan-verify alignment` if NEXT active).

---

## Alignment repair

**Triggers:** `repair - from alignment`, verify alignment **fail**.

**Order (minimize thrash — tutorial §6):**

1. Fix `{MASTER_PLAN}` if FR/task ids wrong → [Master repair](#master-repair).
2. Regenerate iteration → `@code-implementation plan - M{N}`.
3. SPEC amendments if behaviour contract wrong → `@feature-spec amend - <slug>`.
4. [R4](#r4--re-verify-mandatory) → `@plan-verify alignment`.

---

## Coverage repair

**Triggers:** `repair - from coverage`, `@plan-verify coverage` **fail** or **pass with gaps**, or user goal to register unmapped app surfaces.

**Objective:** Close gaps between application surfaces and `{FEATURE_SPEC_ROOT}` without inventing parallel registries (`feature.yml`, ad-hoc domain-registry files). Canon: FEATURE_STANDARD SPEC + DIRECTORY_MAP.

### CG0 - Intake

1. Run `@plan-verify coverage` **or** absorb a coverage report from chat (same session).
2. Build F* rows: one per **unmapped** surface (severity **High** for production routes/APIs; **Med** for cross-cutting shell/LMS-style clusters).

### CG1 - Remediate (per gap)

| Step | Action |
|------|--------|
| 1 | Pick kebab-case **slug** (`dashboard-shell`, `courses-lms`, …) — no collision with existing folder |
| 2 | `@feature-spec create - <slug>` — **Draft** SPEC; fill **Implementation map** with inventoried paths; Purpose one paragraph; §2 Out of scope explicit |
| 3 | Update DIRECTORY_MAP bounded-context / path rows to reference the slug |
| 4 | Add slug to `{FEATURE_SPEC_ROOT}/README.md` index (navigation list only — no duplicate path tables) |

**Do not** create `feature.yml` unless the user explicitly requires a legacy consumer; prefer SPEC **§14 Implementation map**.

### CG2 - Optional audit artifact

When user asked to persist the verify run, update `{WORK_ROOT}/reports/YYYYMMDD-code-registry-audit.md` **Resolved** rows for closed gaps.

### CG3 - Post-repair

[R4](#r4--re-verify-mandatory) → `@plan-verify coverage`.

If framework slots were also missing → `@plan-verify brownfield` after coverage **pass**.

---

## Brownfield repair protocol

**Triggers:** `@plan-repair brownfield`, `brownfield - foundation`, `brownfield - master`, BF0 = yes on any repair, or verify **brownfield-gap** / **fail** with brownfield header.

**Purpose:** Bring a **code-first or legacy-doc** repository to the **best possible alignment** with the `.ai` framework **without** requiring a prior formal `@plan-foundation greenfield` or `@plan-master greenfield` run. Formal certify/approve may come **after** alignment.

### BR0 - Brownfield detection

Use the same BF0 rules as `plan-verify` § Brownfield detection. If **brownfield: no** and user invoked `brownfield` only → run standard repair on named layer instead.

### BR1 - Assess (mandatory, no writes)

1. Run `@plan-verify brownfield` **or** execute BF1–BF3 inline (same slot map as plan-verify).
2. Build F* rows from gaps (missing slots, contradictions, substitute-only rows).
3. Present **Repair plan** (R2) listing files to **create** | **align** | **migrate** (legacy → canonical path).

### BR2 - Scaffold (minimal writes)

| Step | Action |
|------|--------|
| 1 | If `.work/` or `.cursorrules` missing → `@project-bootstrap init` with **`overwrite-missing`** (default; never `overwrite-all` without explicit user token) |
| 2 | Create empty registries from `plan-foundation` reference templates if missing |
| 3 | Update `{HANDOFF}` § Repository state with: `Brownfield-aligned: in progress` (date) — **do not** claim `Plan-master-ready` until certify passes |

### BR3 - Synthesize foundation (no greenfield questionnaire)

**Does not require** prior `@plan-foundation greenfield`. Prefer **evidence-backed synthesis** over empty templates.

| Artifact | Create when missing | Synthesis sources (priority order) |
|----------|---------------------|-----------------------------------|
| `foundation/…-01-…-initial-scope.md` | Always if no 01 | README, HANDOFF, product brief |
| `foundation/…-01-…-scope.md` | If no scope doc | initial-scope + issues/epics |
| `foundation/…-04-…` | If no doc 04 | Code tree, ADRs, DIRECTORY_MAP, package layout |
| `02` integration | If external APIs | `.ai/docs/integration/`, code clients |
| `03` adjacency | If multi-product | README roadmap, module boundaries |
| ADRs | If `{DECISIONS_ROOT}` thin | Migrate `docs/adr/*` → `.work/decisions/` or index with links |
| SPECs | If contexts lack SPEC | `@feature-spec create - <slug>` from module + tests (**Inference** rules); or `@plan-verify coverage` → `repair - from coverage` |
| Standards | If missing | Copy from `.ai/standards/` templates; fill **Inference** from linter/tsconfig |
| Registries | If empty | Extract from TODOs, README risks, open issues |

**Execution style:**

- Use `@plan-foundation continue` **only** for phases where interactive answers are still needed; otherwise **write directly** per GATE artifact lists in `plan-foundation/skill.md`, marking synthesized sections.
- At end of foundation synthesis → `@plan-master integrity` on foundation set when ≥2 artifacts exist.
- **Optional formal path** (user may request later): `@plan-foundation certify plan-master-ready` — not required to finish brownfield repair.

### BR4 - Synthesize master plan (no prior formal plan-master)

**Does not require** `Plan-master-ready:` in HANDOFF **before** starting synthesis. **Does require** foundation slots ≥ **partial** (scope + architecture evidence).

| Situation | Action |
|-----------|--------|
| No `*-full-plan.md` | Create `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md` **Draft** using `MASTER_PLAN_STANDARD` + evidence from ROADMAP, milestones, NEXT, code milestones |
| Substitute ROADMAP only | **Migrate** content into §19 task table with `M{N}-T{N}` ids; add FR/NFR stubs traced to README |
| Partial draft plan | `@plan-master continue` **or** direct edit + `@plan-master revise - brownfield alignment YYYY-MM-DD` |
| User goal after `-` | Apply as revise reason once base plan exists |

**PG1 brownfield waiver:** When creating the **first** master plan from synthesis, record in HANDOFF:

```text
Brownfield master synthesis: YYYY-MM-DD — formal plan-master-ready pending @plan-foundation certify
```

Then run `@plan-master greenfield` **only if** user wants full phase questionnaire; otherwise author Draft plan directly from [BR3](#br3---synthesize-foundation-no-greenfield-questionnaire) outputs + ROADMAP.

**implementation-ready:** Never set **yes** in brownfield repair — only **Draft** master until owner approves via plan-master workflow.

### BR5 - Synthesize alignment (NEXT)

| Situation | Action |
|-----------|--------|
| No valid `## Current iteration` | `@code-implementation plan - M{N}` when Approved/Draft plan has §19; else create minimal NEXT with **Recommended next** from synthesized M1 |
| NEXT predates framework | Rewrite block to cite `{MASTER_PLAN}` §19; preserve owner task intent in Notes |
| No milestone ids in legacy NEXT | Map tasks to new `M1-T1…` with trace row in repair report |

### BR6 - Close brownfield pass

1. Update `{HANDOFF}`: `Brownfield-aligned: YYYY-MM-DD` + list remaining formal gaps (certify, Approved).
2. Sync registries from new docs.
3. [R4](#r4--re-verify-mandatory): `@plan-verify brownfield` (required).
4. Verdict **repaired** when verify tier ≥ **brownfield-partial** and no High gaps without waiver.

### BR7 - Brownfield repair report addendum

Append to R5:

```markdown
### Brownfield manifest
| Path | Action | Source |
|------|--------|--------|
| … | created | README §… |

### Formal path remaining
- [ ] @plan-foundation certify plan-master-ready
- [ ] @plan-master continue → Approved
```

---

## Brownfield bootstrap (alias)

`@plan-repair brownfield` = full [Brownfield repair protocol](#brownfield-repair-protocol).

`brownfield - foundation` → BR2–BR3 only, then `@plan-verify foundation` (BF branch).

`brownfield - master` → BR3 (minimal) + BR4, then `@plan-verify master` (BF branch).

---

## Status protocol

Read-only.

```markdown
## plan-repair status

**Brownfield:** yes | no
**Brownfield-aligned:** yes | no | in progress | unknown
**Foundation-complete:** yes | no | unknown (formal)
**Plan-master-ready:** yes | no | unknown (formal)
**Master plan:** <path | substitute | none>
**Suggested repair:** @plan-repair brownfield | foundation | master | brownfield - foundation
```

---

## Integration

| Skill | Relationship |
|-------|----------------|
| `plan-verify` | **Upstream detector** — fail → `@plan-repair repair - from <mode>` |
| `plan-foundation` | **Executor** for foundation continue / certify |
| `plan-master` | **Executor** for greenfield / continue / revise / integrity |
| `code-repair` | **Wrong layer** for plan docs — redirect here |
| `code-implementation` | Regenerates NEXT after master repair |
| `project-bootstrap` | Brownfield `.work/` + `.cursorrules` scaffold |
| `feature-spec` | SPEC amendments when repair touches behaviour contracts |

---

## Blocked report shape

Per [SKILL_DEPENDENCIES.md § Blocked report shape](../SKILL_DEPENDENCIES.md#blocked-report-shape) — header: `## @plan-repair <command> - blocked (prerequisite)`.

---

## Anti-patterns

- **repaired** without `@plan-verify` re-run output
- Editing Approved master plan without `revise` protocol or correction note
- Calling doc 04 "the full plan"
- `@plan-master greenfield` when plan-master-ready is **no**
- Implementation code changes during plan-repair
- Mass backfills or destructive SQL (forbidden per `.cursorrules`)
- Skipping master fix before rewriting NEXT (alignment thrash)
- Requiring `@plan-foundation greenfield` before any brownfield synthesis
- Claiming `Plan-master-ready` or **Approved** without formal certify/approve workflow
- `overwrite-all` bootstrap without explicit user confirmation
