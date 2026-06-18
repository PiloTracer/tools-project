---
name: plan-verify
description: >-
  Verification layer for planning artifacts: foundation (P0–P6), master plan,
  NEXT vs full-plan alignment, code-to-SPEC registry coverage, and brownfield
  framework alignment when plan-foundation or plan-master were never run formally.
  Orchestrates upstream status/integrity when present; otherwise assesses repo
  evidence against .ai slots. Use plan-verify foundation, master, alignment,
  coverage, brownfield, or open language.
---

# plan-verify

Verification layer for **planning documentation** — not application code. **Does not author** foundation docs or master plans; **does not** replace `plan-foundation` / `plan-master` mutating modes.

**Pairs with:** `plan-foundation` (foundation status + gate evidence), `plan-master` (master status + integrity), `plan-repair` (remediation after fail), `code-verify` (implementation layer — orthogonal), `.cursorrules` Completion Gate (evidence-first).

**Canonical path:** `.ai/skills/plan-verify/skill.md` · **Invocation examples:** `reference.md`

**Registry:** [`.ai/skills/SKILL_DEPENDENCIES.md`](../SKILL_DEPENDENCIES.md).

**Hard rules:**

- **Evidence-first** — cite file paths and quoted headings; never claim **pass** without running the checks in this skill or attaching upstream skill output from the same session.
- **Read-only** — no writes to `{HANDOFF}`, `{ITERATION_CARRIER}`, foundation docs, or `*-full-plan.md` unless the user explicitly asks to persist a verify result in HANDOFF.
- **Delegate, do not duplicate** — invoke upstream skills by **following** their `skill.md` protocols (same agent turn); do not reimplement certify, revise, or greenfield logic inline.
- **Layer discipline** — foundation verify must **not** score **implementation-ready** (redirect to `@plan-master status`). Master verify must **not** certify **plan-master-ready** (redirect to `@plan-foundation certify`).
- **Brownfield-first** — when [Brownfield detection](#brownfield-detection-bf0) is **yes**, use [Brownfield verify](#brownfield-verify-protocol) (or the BF branch inside the requested mode). Do **not** hard-stop solely because `@plan-foundation` / `@plan-master` were never run; assess **framework alignment** from repo evidence.
- Every mode ends with a **Completion checklist** — each item `pass` | `fail` | `skip` with evidence.

---

## Parse invocation

Normalize to **mode** + optional scope. Use ASCII hyphen **`-`** between tokens.

| User says | Mode | Action |
|-----------|------|--------|
| `@plan-verify` **foundation** | foundation | [Foundation verify](#foundation-verify-protocol) |
| `@plan-verify` **master** | master | [Master verify](#master-verify-protocol) |
| `@plan-verify` **alignment** | alignment | [Alignment verify](#alignment-verify-protocol) — NEXT vs `{MASTER_PLAN}` |
| `@plan-verify` **drift** | alignment | Alias for **alignment** |
| `@plan-verify` **status** | status | [Status protocol](#status-protocol) — read-only summary |
| `@plan-verify` **brownfield** | brownfield | [Brownfield verify](#brownfield-verify-protocol) — full framework alignment pass |
| `@plan-verify` **coverage** | coverage | [Coverage verify](#coverage-verify-protocol) — app surfaces vs SPECs / DIRECTORY_MAP |
| `@plan-verify` **registry** | coverage | Alias for **coverage** |
| `@plan-verify` **verify** | *(infer)* | See **Default** below |
| `plan-verify` **audit** **foundation** | foundation | Alias |
| `plan-verify` **check** **master** | master | Alias |
| Open language: "verify foundation planning", "audit master plan" | *(infer)* | Map keywords → mode; ask once if ambiguous |

**Default (bare `@plan-verify`):**

1. If `{ITERATION_CARRIER}` has valid `## Current iteration` → **alignment** (then offer **foundation** / **master** if user wants full stack).
2. Else if `{PLANS_ROOT}/full/*-full-plan.md` exists → **master**, then abbreviated **foundation** snapshot in report.
3. Else if `{PLANS_ROOT}/foundation/` has any doc → **foundation**.
4. Else if application source or product docs exist → **brownfield**.
5. Else → **foundation** (empty repo; bootstrap hints).

**Aliases:** `audit`, `check` → same mode inference as bare `@plan-verify`.

Open language → **brownfield** when user says: existing repo, legacy, never ran plan-foundation, adopt Agent OS, align to `.ai` framework, brownfield.

Open language → **coverage** when user says: unmapped surfaces, code-to-plan parity, feature catalog gap, 100% cataloged, map routers/pages to features, undocumented app surfaces.

### Open language interpretation (free requests)

**When:** The user message does **not** contain an explicit mode keyword (`foundation`, `master`, `alignment`, `brownfield`, `status`, `drift`) — or the keyword is embedded in a free-form sentence (e.g. "verify foundation planning", "audit master plan", "is our plan ready?").

Before running any protocol, emit a **Request interpretation** block that maps the open language to framework terms:

```markdown
### Request interpretation

**User said:** <raw text or paraphrase one line>

**Detected mode:** foundation | master | alignment | brownfield | status
**Mapped via:** <keyword match | default inference | user disambiguation>
**Framework components examined:**
| Component | Path | Why |
|-----------|------|-----|
| P0–P6 foundation docs | `{PLANS_ROOT}/foundation/*` | Mode: foundation |
| Plan-master status + integrity | `{PLANS_ROOT}/full/*-full-plan.md` | Mode: master |
| SPECs | `{FEATURE_SPEC_ROOT}/` | Per touched contexts |
| … | … | … |

**Assumption ledger:** <Confirmed | Inference | Unverified> for any ambiguous mapping
```

**Rules:**
- Emit the interpretation block **once** before the mode-specific protocol runs.
- When a keyword match is unambiguous (e.g. "audit master plan" → mode `master`), state **Confirmed**.
- When the mapping is probabilistic or the user question is vague, label **Inference** and ask once to confirm the detected mode before proceeding.
- Include the interpretation block in the report header (see report formats below).

When mode is explicit (e.g. `@plan-verify foundation`, `@plan-verify master`), skip the interpretation block and record: `**Request:** explicit mode — no interpretation needed`.

---

## Brownfield detection (BF0)

Run at the start of **every** mode. Record **brownfield: yes | no** in the report header.

**brownfield: yes** when **any** of:

| Signal | Evidence |
|--------|----------|
| No formal foundation run | `{HANDOFF}` lacks `Plan-master-ready:` **and** foundation doc 01–04 missing or stub-only |
| No formal master plan | No `{PLANS_ROOT}/full/*-full-plan.md` **or** plan is clearly pre-framework (no `M{N}-T{N}` ids, wrong layout) |
| Code-first repo | Application source tree exists (`REPLACE:APP_ROOT` or obvious `src/`, `apis/`, `backend/`) |
| User invoked brownfield | Message contains `brownfield`, `legacy`, `existing repo`, `never ran plan-foundation`, `align framework` |
| Legacy planning only | `ROADMAP.md`, `docs/planning/`, GitHub milestones, or README-only scope **without** `.work/plans/foundation/` |

**brownfield: no** when HANDOFF records `Plan-master-ready: <date>` **and** foundation 01–04 + registries exist per `plan-foundation` status.

**When brownfield: yes** — still run the requested mode, but follow the **BF branch** in that protocol (or use dedicated **brownfield** mode for all layers at once).

---

## Framework alignment map (brownfield)

Score each **canonical slot** against what exists on disk. Do not require formal P0–P6 completion to run checks.

| Slot | Canonical path (under repo root) | Acceptable brownfield substitutes (cite path) |
|------|----------------------------------|-----------------------------------------------|
| Agent rules | `.cursorrules` | Missing → gap (bootstrap) |
| HANDOFF | `.work/context/HANDOFF.md` | Missing → gap |
| P0 / scope capture | `.work/plans/foundation/*-01-*-initial-scope.md` | README § product, `docs/vision.md`, top of HANDOFF |
| Scope doc 01 | `.work/plans/foundation/*-01-*-scope.md` | Same + issue labels / epic docs |
| Architecture foundation 04 | `.work/plans/foundation/*-04-*` | ADR index, `docs/architecture.md`, DIRECTORY_MAP + code tree |
| ADRs | `.work/decisions/` | `docs/adr/`, inline README decisions |
| SPECs | `.work/features/*/…-SPEC.md` | Domain README, test names, module docstrings (infer **Inference**) |
| Standards | `.ai/standards/*CONVENTIONS*`, `*FEATURE_STANDARD*`, `*DIRECTORY_MAP*` | Repo conventions doc; infer from linter config |
| Registries | `.work/plans/ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md` | TODO/FIXME scan, issue tracker, empty template = gap |
| Master plan | `.work/plans/full/*-full-plan.md` | `ROADMAP.md`, milestone issues, dense NEXT only |
| Iteration | `.work/plans/NEXT.md` | Kanban export, sprint doc (partial credit) |
| Stack | `REPLACE:TECH_STACK_DOC` | `package.json`, `pyproject.toml`, `go.mod`, Dockerfile |

**Coverage score:** `present` | `substitute` | `partial` | `missing` per slot. **Framework alignment %** = (present + substitute) / total slots (round down; label **Estimate**).

---

## Brownfield verify protocol

**Triggers:** `@plan-verify brownfield`, or **BF0 = yes** on any mode.

**Objective:** Best-effort read-only assessment of how well the repo matches the `.ai` planning model **without** requiring prior `@plan-foundation greenfield` or `@plan-master greenfield`.

### BF1 - Repo discovery (mandatory)

1. Inventory per [Framework alignment map](#framework-alignment-map-brownfield).
2. Read: `README.md`, `{HANDOFF}` (if any), app tree (2 levels), `{DECISIONS_ROOT}/`, `{FEATURE_SPEC_ROOT}/`, existing plans under `{PLANS_ROOT}/`.
3. Build **assumption ledger**: label each inferred fact **Confirmed** (file cite) | **Inference** | **Unverified**.

### BF2 - Layer assessments (run all that apply)

| Layer | When | Action |
|-------|------|--------|
| Foundation | Always in brownfield | [Foundation verify](#foundation-verify-protocol) **BF branch** — matrix uses substitutes; skip F1 integrity **fail** on missing docs → record `integrity: skip - no foundation set to audit` |
| Master | Master plan or substitute exists | [Master verify](#master-verify-protocol) **BF branch** — conformance vs `MASTER_PLAN_STANDARD` on substitute or partial plan |
| Alignment | NEXT or sprint doc exists | [Alignment verify](#alignment-verify-protocol) **BF branch** — compare NEXT to best available roadmap (master plan **or** substitute) |

### BF3 - Formal readiness (report only — do not certify)

| Label | Meaning |
|-------|---------|
| **formal-foundation-complete** | Would be **yes** per `plan-foundation` gates (rare in brownfield) |
| **formal-plan-master-ready** | HANDOFF certify date or equivalent |
| **brownfield-aligned** | ≥70% framework slots `present` or `substitute`; no High-severity contradictions |
| **brownfield-partial** | 40–69% coverage or major substitutes only |
| **brownfield-gap** | <40% or blocking contradictions |

### BF4 - Brownfield report (mandatory)

```markdown
## plan-verify brownfield - <Project>

**Date:** <ISO> · **Brownfield:** yes
**Framework alignment:** <N>% (Estimate) · **Tier:** brownfield-aligned | brownfield-partial | brownfield-gap

### Request interpretation
<when open language — insert interpretation block; otherwise: explicit brownfield mode>

### Slot coverage
| Slot | Status | Source path | Notes |
|------|--------|-------------|-------|

### Formal readiness (not certified here)
- formal-foundation-complete: yes | no
- formal-plan-master-ready: yes | no
- brownfield-aligned: yes | no

### Layer verdicts
- Foundation: pass | pass with gaps | fail | skip
- Master: …
- Alignment: …

### High-priority gaps
<ordered>

### Verdict
**aligned-best-effort** | **pass with gaps** | **fail**

### Next step
@plan-repair brownfield | @plan-repair brownfield - foundation | @project-bootstrap init (overwrite-missing)
```

**Verdict rules (brownfield):**

- **aligned-best-effort** — brownfield-aligned **yes**; safe to proceed with documented waivers; recommend `@plan-repair brownfield` to close gaps without full greenfield questionnaire.
- **pass with gaps** — usable substitutes; formal certify still pending.
- **fail** — contradictions, missing `.work/` skeleton, or no product truth (cannot infer scope).

---

## Shared prerequisites

| # | Read | When |
|---|------|------|
| 1 | `.cursorrules` placeholder map (`{PLANS_ROOT}`, `{HANDOFF}`, …) | all modes |
| 2 | `{HANDOFF}` | all modes |
| 3 | `{PLANS_ROOT}/ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md` | foundation, master |
| 4 | `.ai/standards/20260519-MASTER_PLAN_STANDARD.md` | master (section contract) |
| 5 | `.ai/docs/guides/workflows/20260518-tutorial-fix-existing-plans.md` | alignment |

---

## Foundation verify protocol

Cross-check **foundation layer** readiness: P0–P6 gates, registries, traceability, and semantic integrity on foundation artifacts.

### Foundation verify — brownfield branch (BF)

When **BF0 = yes**:

1. Run [BF1](#bf1---repo-discovery-mandatory) slot inventory for foundation rows only.
2. **Skip** hard fail when `plan-foundation status` would show all **not started** — instead score each P0–P6 row: **present** | **substitute** | **partial** | **missing** with substitute path.
3. Run `plan-master integrity` only if ≥2 foundation artifacts exist (01, 04, ADR, or SPEC); else **integrity: skip**.
4. Verdict may be **pass with gaps** or **aligned-best-effort** when substitutes cover scope + architecture; list **formal-foundation-complete: no** explicitly.
5. **Next step** defaults to `@plan-repair brownfield - foundation` (not `@plan-foundation greenfield` unless user wants full questionnaire).

### F0 - Invoke upstream status (mandatory)

Follow `.ai/skills/plan-foundation/skill.md` § **Status protocol** (S1–S6). Produce or absorb the standard **Foundation status** report.

Record in your working notes (do not conflate labels):

- **foundation-complete:** yes | no
- **plan-master-ready:** yes | no | not evaluated
- Phase table P0–P6 with evidence paths

### F1 - Integrity on foundation artifacts (mandatory)

Follow `.ai/skills/plan-master/skill.md` § **integrity** mode on **foundation set only** (docs 01–04, ADRs, SPECs, registries — no `*-full-plan.md` required).

Record: **integrity:** pass | pass with waivers | fail

### F2 - Foundation check matrix

| Dimension | Question | Result |
|-----------|----------|--------|
| P0 capture | P0 initial scope + `.cursorrules` + registries exist? | pass / fail / gap |
| P1 exploration | Docs 01–04 present; doc 04 is architecture foundation not master plan? | pass / fail / gap |
| P2 ADRs | Core ADRs Decided or deferred with UNKNOWNS? | pass / fail / gap |
| P3 SPECs | CONVENTIONS + FEATURE_STANDARD + DIRECTORY_MAP + ≥1 SPEC with R1…? | pass / fail / gap |
| P4 cross-cutting | Threat model, observability, stack doc when UI/security in scope? | pass / fail / skip |
| P5 infra | Proposal or HANDOFF waiver for compose? | pass / fail / skip |
| P6 ops | HANDOFF + NEXT + README gates? | pass / fail / gap |
| Registries | ASSUMPTIONS / RISK / UNKNOWNS reviewed, not empty shells? | pass / fail |
| Traceability | Scope ↔ ADR ↔ SPEC spot-check for touched contexts? | pass / fail / gap |
| Terminology | Doc 04 not called "the full plan" in artifacts? | pass / fail |
| Integrity (F1) | plan-master integrity on foundation? | pass / fail / waived |
| Probe coverage | If `{PLANS_ROOT}/foundation/PROBE_LEDGER.md` exists: `bash .ai/scripts/readiness-verify.sh` passes? Coverage % vs target; ★ gaps? | pass / gap / n/a |

### F3 - Foundation verify report (mandatory)

```markdown
## plan-verify foundation - <Project>

**Date:** <ISO> · **Mode:** foundation (read-only)

### Request interpretation
<when open language — insert interpretation block; otherwise: explicit foundation mode>

### Upstream
- **plan-foundation status:** embedded / cited above
- **plan-master integrity (foundation):** pass | pass with waivers | fail

### Check matrix
| Dimension | Result | Evidence / gap |
|-----------|--------|----------------|

### Readiness (report only — do not certify here)
- **foundation-complete:** yes | no
- **plan-master-ready:** yes | no
- **Probe coverage:** NN% (target 85%) · ledger honest: yes/fail | no ledger - if understanding is thin, run `@plan-foundation probe`

### Gaps
<ordered - severity High / Med / Low>

### Verdict
**pass** | **pass with gaps** | **fail** - <one sentence>

### Next step
- pass / pass with gaps (waived): `@plan-foundation certify plan-master-ready` or `@plan-master greenfield` if already certified
- fail: `@plan-repair repair - from foundation` or `@plan-repair foundation - <goal>`
```

---

## Master verify protocol

Cross-check **master implementation plan** and **implementation-ready** prerequisites (report only — scoring follows plan-master status rules).

### Master verify — brownfield branch (BF)

When **BF0 = yes**:

1. If no `*-full-plan.md` but substitute exists (ROADMAP, milestones) → run **M3** against substitute; label **master artifact: substitute** with path.
2. If only NEXT/sprint doc → **master: partial**; alignment BF branch carries execution truth.
3. Do **not** emit blocked prerequisite solely for missing `Plan-master-ready:` — report **formal-plan-master-ready: no** and **Next:** `@plan-repair brownfield - master`.
4. **implementation-ready** must remain **no** unless an Approved `*-full-plan.md` exists (no brownfield waiver for broad execution).

### M0 - Prerequisite snapshot

If **plan-master-ready: no** in HANDOFF / foundation status:

- **brownfield: no** → verdict **fail** with **Run first:** `@plan-foundation certify plan-master-ready`.
- **brownfield: yes** → continue; report formal gate open; use [Master verify — brownfield branch](#master-verify--brownfield-branch-bf).

### M1 - Invoke upstream status (mandatory)

Follow `.ai/skills/plan-master/skill.md` § **Status protocol**. Record:

- Plan artifact path
- **Plan status:** Draft | Approved | …
- **implementation-ready:** yes | no (from plan-master — cite, do not re-score differently)
- Phase progress P0–P6 inside plan workflow

### M2 - Integrity on master plan (mandatory)

Follow `.ai/skills/plan-master/skill.md` § **integrity** when `*-full-plan.md` exists; if missing → **fail** with **Run first:** `@plan-master greenfield` or `@plan-repair master - create master plan from foundation`.

Record: **integrity:** pass | pass with waivers | fail

### M3 - Standard conformance (when plan exists)

Against `.ai/standards/20260519-MASTER_PLAN_STANDARD.md`:

| Dimension | Question | Result |
|-----------|----------|--------|
| Header metadata | Status, version, dates present? | pass / fail |
| §19 roadmap | Milestones M1… with task ids `M{N}-T{N}`? | pass / fail / gap |
| §20–§21 | Global acceptance + validation gates? | pass / fail / gap |
| Traceability | FR/NFR ids in tasks exist in plan body? Run `bash .ai/scripts/traceability-verify.sh` (every FR maps to a task M{N}-T{N})? | pass / fail / gap |
| Registries | Links to ASSUMPTIONS/RISK/UNKNOWNS — no duplicate forks? | pass / fail |
| Approved gate | Approved required for implementation-ready? | pass / fail / waived |
| Probe coverage | If `{PLANS_ROOT}/full/PROBE_LEDGER.md` exists: `bash .ai/scripts/readiness-verify.sh` passes? Coverage % vs target; ★ gaps? | pass / gap / n/a |

### M4 - Master verify report (mandatory)

```markdown
## plan-verify master - <Project>

**Date:** <ISO> · **Mode:** master (read-only)

### Request interpretation
<when open language — insert interpretation block; otherwise: explicit master mode>

### Upstream
- **plan-master status:** cited above
- **plan-master integrity:** pass | pass with waivers | fail

### Check matrix
| Dimension | Result | Evidence / gap |
|-----------|--------|----------------|

### Readiness (from plan-master — do not contradict)
- **implementation-ready:** yes | no
- **Probe coverage:** NN% (target 85%) · ledger honest: yes/fail | no ledger - if NFRs/FRs/risks are thin, run `@plan-master probe` → `@plan-master integrity`

### Gaps
<ordered>

### Verdict
**pass** | **pass with gaps** | **fail**

### Next step
- fail: `@plan-repair repair - from master` or `@plan-repair master - <goal>` or `@plan-master revise - <reason>`
- pass + not Approved: `@plan-master continue` or owner approval workflow
```

---

## Alignment verify protocol

Detect drift between **tactical** (`{ITERATION_CARRIER}`) and **strategic** (`{MASTER_PLAN}`) layers per `20260518-tutorial-fix-existing-plans.md`.

### Alignment verify — brownfield branch (BF)

When **BF0 = yes**:

- If no `## Current iteration` but sprint doc / NEXT without block → **partial**; recommend `@plan-repair brownfield` or `@code-implementation plan - M{N}` after master substitute exists.
- If no `{MASTER_PLAN}` but ROADMAP / milestones → compare NEXT tasks to substitute; flag id mismatches as **Med** gaps (not automatic **fail**).
- Verdict **aligned-best-effort** allowed when NEXT is internally consistent with best available roadmap substitute.

### A0 - Existence gate

| Required | If missing (brownfield: no) | If missing (brownfield: yes) |
|----------|----------------------------|------------------------------|
| Valid `## Current iteration` in `{ITERATION_CARRIER}` | **fail** — `@code-implementation plan - M{N}` | **partial** — BF branch |
| `{MASTER_PLAN}` (latest `*-full-plan.md`) | **fail** — `@plan-master greenfield` or `@plan-repair master - …` | Use substitute per [BF branch](#alignment-verify--brownfield-branch-bf) |

### A1 - Alignment checks

| Check | Pass if |
|-------|---------|
| Milestone ref | Iteration header `M{N}` exists in plan §19 (or HANDOFF-documented section id) |
| Task ids | Iteration task ids match plan §19 exactly |
| FR/NFR | Iteration traces cite ids that exist in plan FR/NFR tables |
| Acceptance scope | Iteration acceptance is milestone-local, not whole-plan dump |
| Concept registry | Iteration registry matches SPEC §15 for touched features |
| Files column | Every task row has path or `TBD` + blocker |

### A2 - Alignment report

```markdown
## plan-verify alignment - M{N}: <name>

**Date:** <ISO> · **Plan:** <path> · **Iteration:** {ITERATION_CARRIER}

### Request interpretation
<when open language — insert interpretation block; otherwise: explicit alignment mode>

### Checks
| Check | Result | Evidence |

### Gaps
<ordered>

### Verdict
**pass** | **pass with gaps** | **fail**

### Next step
- Master wrong: `@plan-repair master - <reason>` or `@plan-master revise - <reason>`
- NEXT wrong only: `@code-implementation plan - M{N}` (after master is source of truth)
- Both: fix master first (tutorial §6 order)
```

---

## Coverage verify protocol

**Triggers:** `@plan-verify coverage`, `@plan-verify registry`, or open language about **unmapped app surfaces** / **code-to-registry parity**.

**Objective:** Read-only inventory of **deployable application surfaces** (routes, pages, controllers, standalone utilities under `{APP}`) vs **registry artifacts** (`{FEATURE_SPEC_ROOT}/<slug>/*-SPEC.md` **Implementation map**, `{BOUNDARY_MAP}` / DIRECTORY_MAP rows). Ensures agents can locate code from `.work/` without ad-hoc tree walks.

**Not in scope:** Full behavioural SPEC review (use `@feature-spec review`); iteration task scope (use `@code-verify milestone`); framework self-check (use `bash scripts/framework-verify.sh` from Agent OS repo root).

**Legacy artifacts:** Project-specific `feature.yml` or domain-registry markdown files are **not** framework canon. Treat them as **substitutes** during inventory; migrate paths into SPEC **Implementation map** (FEATURE_STANDARD) when repairing.

### C0 - Prerequisites

| # | Read | When |
|---|------|------|
| 1 | `{AGENT_RULES_FILE}` — `REPLACE:APP_ROOT`, `REPLACE:FRONTEND_ROOT`, boundary placeholders | always |
| 2 | `.ai/standards/*DIRECTORY_MAP*` (or `{BOUNDARY_MAP}`) | always |
| 3 | `{FEATURE_SPEC_ROOT}/README.md` + each `*/…-SPEC.md` (Implementation map + Purpose) | always |
| 4 | Application tree under `{APP}` (2–3 levels; route entrypoints) | always |

If no application source exists → **skip** with verdict **pass** (nothing to map); suggest `@plan-verify foundation`.

### C1 - Surface inventory (mandatory)

Build a **surface list** — one row per independently routable or operable unit:

| Surface kind | Typical evidence (adapt per stack) |
|--------------|-----------------------------------|
| HTTP API routers / controllers | FastAPI `APIRouter`, Express routers, Nest modules |
| UI routes / pages | Next.js `pages/` or `app/`, React Router route files |
| BFF / API routes | `pages/api/`, server actions with distinct URLs |
| Workers / jobs | Celery tasks, queue consumers with dedicated modules |
| Standalone utilities | Scripts under `{APP}` invoked in production (not one-off `scripts/` dev tools unless documented in HANDOFF) |

**Exclude:** `tests/`, `migrations/`, generated code, vendor mirrors under `.ai/docs/integration/`, pure config.

Label each row **Confirmed** (file cite) | **Inference** (heuristic grouping).

### C2 - Registry mapping (mandatory)

For each surface, resolve **mapped slug** using this order:

1. SPEC **## Implementation map** (§14) path table (FEATURE_STANDARD) — **Confirmed**
2. DIRECTORY_MAP bounded-context / path row — **Confirmed** or **Inference**
3. SPEC Purpose / §6 APIs naming the surface — **Inference**
4. No match → **unmapped**

### C3 - Coverage matrix

| Surface | Mapped slug | Evidence | Status |
|---------|-------------|----------|--------|
| … | `<slug>` \| — | path + SPEC § | mapped \| unmapped \| waived |

**Waivers:** Only when HANDOFF or same-message user documents intentional orphan (e.g. deprecated module pending removal). Cite waiver id.

**Coverage %:** `mapped + waived` / total surfaces (round down; label **Estimate**).

### C4 - Coverage report (mandatory)

```markdown
## plan-verify coverage - <Project>

**Date:** <ISO> · **Mode:** coverage (read-only)
**Surfaces inventoried:** <N> · **Coverage:** <N>% (Estimate)

### Request interpretation
<when open language — insert block; else: explicit coverage mode>

### Unmapped surfaces
| Surface | Suggested slug | Notes |
|---------|----------------|-------|

### Waivers
<list or "none">

### Registry snapshot
| Slug | SPEC path | Has Implementation map? |
|------|-----------|-------------------------|

### Verdict
**pass** | **pass with gaps** | **fail**

### Next step
- gaps: `@plan-repair repair - from coverage` (or `@plan-repair brownfield` when framework slots also missing)
- pass: optional `bash scripts/framework-verify.sh` when validating Agent OS install
```

**Verdict rules:**

- **pass** — 100% mapped or only documented waivers; DIRECTORY_MAP references every bounded context with a SPEC.
- **pass with gaps** — ≤3 unmapped non-critical surfaces (shell fragments, dev-only) with repair plan obvious.
- **fail** — any unmapped production route/API/page cluster, or >10% unmapped without waivers.

### C5 - Optional persistence

When user asks to **record** the audit in the same message, write `{WORK_ROOT}/reports/YYYYMMDD-code-registry-audit.md` (summary + unmapped table only). Otherwise report in chat only — verify stays read-only.

---

## Status protocol

Read-only. No artifact writes.

1. Quick `foundation` matrix (abbreviated) if foundation paths exist.
2. Quick `master` snapshot if `*-full-plan.md` exists.
3. Note active iteration in `{ITERATION_CARRIER}`.

```markdown
## plan-verify status

**Request interpretation:** <when open language — insert; otherwise: explicit status mode>

**Brownfield:** yes | no
**Framework alignment:** <N>% | unknown
**Foundation-complete:** yes | no | unknown (formal)
**Plan-master-ready:** yes | no | unknown (formal)
**Brownfield-aligned:** yes | no | unknown
**Master plan:** <path | substitute | none> · **Status:** Draft | Approved | …
**Implementation-ready:** yes | no | unknown
**Active iteration:** M{N} | none

**Suggested verify:** @plan-verify brownfield | foundation | master | alignment | coverage
```

---

## Integration

| Skill | Relationship |
|-------|----------------|
| `plan-foundation` | **Upstream** for foundation status; plan-verify **orchestrates**, does not replace |
| `plan-master` | **Upstream** for master status + integrity |
| `plan-repair` | **Downstream** on **fail** — `@plan-repair repair - from foundation` \| `from master` \| `from alignment` \| `from coverage` |
| `feature-spec` | **Downstream** for new slugs when coverage finds unmapped surfaces |
| `code-verify` | **Orthogonal** — code vs plan; run both before broad release |
| `code-repair` | Wrong layer for plan gaps — redirect to `plan-repair` |
| `code-implementation` | Regenerates iteration block after master/plan repair |

---

## Completion checklist (all modes)

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Mode detected | pass/fail | |
| 2 | Shared reads completed | pass/fail | paths |
| 3 | Upstream skill protocols run | pass/fail | |
| 4 | Check matrix filled | pass/fail | |
| 5 | Verdict matches evidence | pass/fail | |
| 6 | Next step names exact command | pass/fail | |
| 7 | No application code written | pass | |
| 8 | Layer labels not conflated | pass/fail | |
| 9 | Request interpretation emitted (when open language) | pass/skip | |

---

## Anti-patterns

- Claiming **pass** without running integrity or citing upstream output
- Certifying **plan-master-ready** or **implementation-ready** inside plan-verify (use upstream skills)
- Using **alignment** when no iteration block exists — use **master** or **foundation** first
- Fixing docs during verify without user asking — use **plan-repair**
- Full foundation greenfield questionnaire during a **status** request
- Hard-stopping brownfield repos solely for missing formal certify (use BF branch + `@plan-repair brownfield`)
- Claiming **implementation-ready** or **plan-master-ready** from brownfield alignment alone
- Running open-language verify without emitting a **Request interpretation** block (see [Open language interpretation](#open-language-interpretation-free-requests))
- Claiming **100% cataloged** from framework slot alignment alone — run **coverage** when the question is code locate-ability
- Introducing parallel registries (`feature.yml`, per-repo domain-registry files) instead of SPEC **Implementation map** + DIRECTORY_MAP
