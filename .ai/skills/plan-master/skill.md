---
name: plan-master
description: >-
  Create or maintain a complete, implementation-ready software development plan
  with traceability, risk registry, phased execution, and integrity validation.
  Use when the user asks for plan-master, master implementation plan, implementation
  roadmap, execution roadmap, whole-system build plan, or legacy phrases "full plan"
  / "full-plan" skill. Requires foundation artifacts or explicit greenfield input. Never writes application code.
---

# plan-master

Produce a **production-grade, implementation-ready** development plan: architecturally sound, incrementally executable, operationally realistic, and safe for lower-level coding agents.

**Tool-agnostic** (Cursor, Claude Code, opencode, Codex). **Pairs with:** `plan-foundation` (prerequisite for mature repos), `session-control`, `{ITERATION_CARRIER}`, `.cursorrules`, feature SPECs under `{FEATURE_SPEC_ROOT}/`.

**Canonical path:** `.ai/skills/plan-master/skill.md` · **Invocation examples:** `reference.md`

**Hard rules:**

- **Never** write application code, migrations, or docker changes unless the user explicitly requests implementation in the same message.
- **Never** fabricate APIs, framework capabilities, infrastructure, or compliance rules - label **Unverified** and ask.
- **Never** silently skip major ambiguities; record in Unknowns registry and ask or block the gate.
- **Never** duplicate foundation content - **reference** existing ADRs, SPECs, foundation docs under `{PLANS_ROOT}/foundation/`; extend only where gaps exist.
- **Never** edit files marked **archived** or **do not edit** in HANDOFF.
- **Never** paste secrets from `.env`, `credentials/`, or tokens into plans or chat.
- Every mode ends with a **Completion checklist** - each item `pass` | `fail` | `skip` with evidence.
- **Traceability:** no major requirement without a chain: Business goal → Requirement → Architecture component → Execution task → Validation/test → Acceptance criterion.

---

## Relationship to other skills

| Skill | Role | When |
|-------|------|------|
| `plan-foundation` | **Orchestrator:** P0–P6 gates, ADRs, SPECs, HANDOFF, planning registries | Runs first; invokes plan-master for integrity at P3+ and after P6 |
| `plan-master` | **Intelligence layer:** architecture quality, integrity, traceability, master roadmap | After foundation exists or with explicit YAML input |
| `session-control` | Session bookends | Optional on start/close of planning sessions |
| Feature SPECs | Per-feature **what** | Referenced by execution tasks; not replaced by plan-master |

**Shared registries** (maintained by plan-foundation; extended by plan-master - do not duplicate):

- `{PLANS_ROOT}/ASSUMPTIONS.md`
- `{PLANS_ROOT}/RISK_REGISTRY.md`
- `{PLANS_ROOT}/UNKNOWNS.md`

If **plan-master-ready** is **no**, stop - run `@plan-foundation certify` first. plan-master **greenfield** requires plan-foundation certification (P0–P6 + integrity on foundation artifacts).

**implementation-ready** is certified by **this skill** (status mode) after the master plan is **Approved** - do not conflate with **plan-master-ready** (plan-foundation certifies that).

**Registry:** Full matrix - [`.ai/skills/SKILL_DEPENDENCIES.md`](../SKILL_DEPENDENCIES.md).

**Symmetric verify/repair:** `@plan-verify master` orchestrates this skill's **status** + **integrity**; gaps → `@plan-repair master` or `@plan-master revise - <reason>`.

---

## Prerequisite gate (mutating modes)

Run **before** **greenfield**, **continue**, or **revise** (not before **status**, **show** *(alias: `task`)*, or **integrity** when plan-foundation invoked integrity on foundation artifacts only).

### PG1 - Plan-master-ready

1. Read `{HANDOFF}` § Repository state (or gate snapshot) for `Plan-master-ready: <date>` **or** run `@plan-foundation status` and read **Plan-master-ready:** line.
2. If **no** and user did not supply complete structured YAML with `foundation_docs:` **and** explicit same-message confirmation that foundation was completed out-of-band → **stop** with the [blocked-report shape](#blocked-report-shape):

```markdown
## @plan-master <command> - blocked (prerequisite)

**Required:** `plan-master-ready: yes` (from `@plan-foundation certify`)
**Detected:** `plan-master-ready: no`
**Run first:** `@plan-foundation status` → `@plan-foundation continue` → `@plan-foundation certify plan-master-ready` → re-invoke `@plan-master <command>`
```

3. If **yes** → proceed to the mode protocol.

**Anti-pattern:** Drafting or extending `*-full-plan.md` when PG1 fails. Do not use "waivers in Assumptions" to bypass plan-master-ready - only HANDOFF-documented **plan-master-ready** date or certify pass unlocks mutating plan-master modes.

### Blocked-report shape

Per [SKILL_DEPENDENCIES.md § Blocked report shape](../SKILL_DEPENDENCIES.md#blocked-report-shape) - header: `## @plan-master <command> - blocked (prerequisite)`.

### PG2 - Mode-specific (after PG1 passes)

| Mode | Additional check |
|------|------------------|
| **greenfield** | No `*-full-plan.md` **or** user explicitly asked to replace; if Approved plan exists without **revise** → recommend **revise** instead |
| **continue** | Latest `*-full-plan.md` exists (Draft or partial) |
| **probe** | Latest `*-full-plan.md` exists (Draft or partial); if none → run **greenfield** first to create the Draft, then probe |
| **revise** | Latest `*-full-plan.md` exists |
| **integrity** | Foundation artifacts and/or master plan exist for the requested scope |
| **status** / **show** | - (read-only; PG1 not required) |

---

## Parse invocation

Normalize the user message to **verb** + optional **modifiers** + optional **goal text** (after `-`).

| User says | Verb | Notes |
|-----------|------|-------|
| `@plan-master` **status** | status | Read-only: plan exists? phase progress? integrity snapshot |
| `plan-master` **continue** | continue | Resume next incomplete planning phase |
| `plan-master` **greenfield** | greenfield | New plan from YAML/minimal input |
| `plan-master` **probe** | probe | Adaptive plan-completeness interrogation; fills gaps before integrity |
| `plan-master` **integrity** | integrity | Phase 5 only - contradiction and fitness review |
| `plan-master` **revise** - \<reason\> | revise | Update existing plan; bump version note in plan header |
| `plan-master greenfield` - startup \| enterprise \| ai-native \| ultra-scale | greenfield | Apply [Advanced mode](#advanced-modes) |
| `plan-master` **show** M1-T3 | show | Read-only: full record for one task (description, files, FR/NFR, status) |
| `plan-master` **show** M2 | show | Read-only: full task table for milestone M2 |

**Aliases:**
- `master plan`, `implementation roadmap`, `build roadmap`, `whole system plan` → **continue** if plan file exists, else **greenfield**.
- **`task`** is the legacy alias of **`show`** - both work (`@plan-master task M1-T3` ≡ `@plan-master show M1-T3`).

**Goal text:** anything after `-` (not mode keywords).

---

## Step 0 - Pick a mode

| Mode | Action |
|------|--------|
| **status** | [Status protocol](#status-protocol) |
| **continue** | [Continue protocol](#continue-protocol) |
| **greenfield** | [Greenfield protocol](#greenfield-protocol) |
| **probe** | [Probe protocol](#probe-protocol) - adaptive plan-completeness loop; fills human-answerable gaps before `integrity` |
| **integrity** | [Phase 5 - Verification](#phase-5--verification--integrity-validation) report only. Can be invoked standalone (`@plan-master integrity`) or from `plan-foundation` continue P3+/P6. |
| **revise** | Read existing plan → apply delta → re-run Phase 5 subset |
| **show** *(alias: `task`)* | [Show protocol](#show-protocol) - read-only; show task record(s) by `M{N}-T{N}` or milestone |

Do not run greenfield questionnaires when the user asked for **status**, **integrity**, or **show** only.

---

## Initial input (greenfield or supplement)

Accept structured YAML in chat or a file path (e.g. `{PLANS_ROOT}/plan-master-input.yaml`):

```yaml
project:
description:
requirements: []          # functional
non_functional: []        # optional; skill will expand if omitted
foundation_docs: []       # paths: HANDOFF, {PLANS_ROOT}/foundation/*-04-*.md, DOCS_TECH_STACK, etc.
constraints: []
target_users: []
additional_notes:
advanced_mode:            # optional: startup | enterprise | ai-native | ultra-scale
```

If YAML is missing, derive from `README.md`, **P0 initial scope** (`{PLANS_ROOT}/foundation/*-01-*-initial-scope.md`), `{HANDOFF}`, and foundation artifacts.

---

## Registries

**Canonical files** (created by `plan-foundation` P0; updated by both skills):

| File | IDs | Purpose |
|------|-----|---------|
| `{PLANS_ROOT}/ASSUMPTIONS.md` | A1… | Confirmed / inferred / rejected / unresolved |
| `{PLANS_ROOT}/RISK_REGISTRY.md` | R1… | Architectural, ops, security, compliance, agent risks |
| `{PLANS_ROOT}/UNKNOWNS.md` | U1… | Open questions; owner; blocks gate/ADR |

Inside the master plan artifact, maintain **append-only**:

| Section | Purpose |
|---------|---------|
| **Decision log** | D1…; date; choice; alternatives rejected |
| **Traceability matrix** | Goal → req → ADR → SPEC → task → test → acceptance |

Link to canonical registries; do not fork duplicate assumption/risk/unknown lists in the plan body.

---

## Planning workflow (Phases 0–6)

Execute in order. At **each phase gate**, run [Continuous integrity rules](#continuous-integrity-rules) before proceeding.

---

### Phase 0 - Foundation discovery

**Objective:** Understand the project before proposing architecture.

**Mandatory reads (when present):** `{HANDOFF}`, `{ITERATION_CARRIER}`, foundation docs 01 + 04, `REPLACE:TECH_STACK_DOC`, ADR index + relevant ADRs, `.ai/standards/*CONVENTIONS*` + `*FEATURE_STANDARD*`, risk-critical SPECs. Skip absent files; do **not** read `{PROMPTS_ROOT}/initial.md` unless user names it.

**Actions:** summarize product intent (one paragraph); extract existing decisions (flag conflicts, do not re-decide); detect hidden assumptions, regulatory surface; build initial risk + clarification questionnaire.

**Outputs:** project understanding summary, key assumptions (registry seeded), critical uncertainties, initial risk assessment, blocker questions for owner.

**Grill when vague:** scale/traffic, budget, ops model, security, compliance, deployment, offline/real-time, integrations, maintainability.

**Gate P0:** User confirms understanding summary OR explicit waiver to proceed with listed unknowns.

---

### Phase 1 - High-level strategic plan

**Objective:** Macro direction aligned with business goals.

**Must include** (maps to MASTER_PLAN_STANDARD §2 rows 1–8): product vision + measurable success criteria, FR1…, NFR1… (performance, availability, security, privacy, i18n, accessibility, cost), personas (link existing), UX principles (high level), technical constraints (from ADRs + stack), security model summary, scalability/deployment/reliability/ops expectations, AI usage boundaries.

**Must define:** architecture style, primary technologies, service/bounded-context boundaries, data flow, integration strategy, infrastructure strategy.

**Each major choice:** rationale, alternatives, rejection reasoning → Decision log appendix.

**Gate P1:** No FR1… without traceability stub; NFRs cover regulated/compliance path if applicable.

---

### Phase 2 - Architecture design

**Objective:** Professional-grade architecture consistent with foundation architecture doc and ADRs.

**Must include** (gap-fill only, reference existing specs; maps to STANDARD §2 rows 9–16): system diagram (mermaid/ASCII), service/context decomposition, domain boundaries + allowed dependencies, database/API/authZ-N strategies, observability/logging/errors, failure recovery + rate limiting + jobs + events, deployment/CI-CD/env/secrets/config, multi-tenancy/extensibility/versioning.

**Must identify:** bottlenecks, SPOFs, scaling risks, maintenance risks, operational complexity.

**Gate P2:** Architecture fitness check - aligned with directory map; no forbidden cross-context imports.

---

### Phase 3 - UX/UI planning

**Objective:** Implementation-oriented UX guidance (maps to STANDARD §2 row 10).

**Must include:** UX philosophy, navigation/IA, layout/responsive/accessibility standards, consistency rules + empty/error/loading states, onboarding + power-user efficiency (link interaction ADR + personas).

**Avoid:** unnecessary complexity, hidden critical paths.

**Gate P3:** Critical user journeys mapped to FR ids; regulated flows show locale/legal field rules where required.

---

### Phase 4 - Incremental execution planning

**Objective:** Convert architecture into executable milestones with task tables conforming to [MASTER_PLAN_STANDARD § 3](../../standards/20260519-MASTER_PLAN_STANDARD.md).

**Per milestone:** apply the 11-field milestone schema from the standard and the `M{N}-T{N}` task table.

**Optimize:** parallelization, minimal coupling, progressive validation.

**Sync:** Update `{ITERATION_CARRIER}` **Recommended next** to `M1-T1` (first task of M1) when plan is **Approved**.

**Gate P4:** Every FR1… maps to ≥1 task (`M{N}-T{N}`); every high-risk task has validation in Phase 5 table. Machine-check with `bash .ai/scripts/traceability-verify.sh` (FR→task coverage; orphan FR → gate fail).

---

### Phase 5 - Verification and integrity validation

**Objective:** Detect flaws before implementation at scale.

**Run:** contradiction analysis (plan vs ADRs vs SPECs); dependency consistency; scope alignment with P0 initial scope + foundation scope doc; architecture fitness, scalability, security, ops readiness, maintainability; AI hallucination risk review (unverified claims, invented APIs).

**Outputs:** risk registry updated, mitigations, unresolved concerns, integrity score = **pass** | **pass with waivers** | **fail**.

**Gate P5:** **fail** blocks `Status: Approved`; waivers need owner line in Decision log (per STANDARD §4 approval gate).

---

### Phase 6 - AI-agent execution optimization

**Objective:** Make the plan safe for autonomous/semi-autonomous agents (maps to STANDARD §2 row 24).

**Must:** decompose into agent-friendly tasks with explicit file paths + constraints; state architectural invariants (cite CONVENTIONS + SPECs); define per-task validation; flag dangerous assumptions.

**Should:** tag tasks `model:tier` (light | standard | strong); recommend cross-model review for regulated / signing / KMS paths.

**Gate P6:** Agent execution appendix present; session-control **start** checklist referenced for implementers.

---

## Mandatory sections (artifact contract)

The plan file structure - 25 H2 sections, header metadata, milestone schema, task record schema, approval gate - is defined in **[`.ai/standards/20260519-MASTER_PLAN_STANDARD.md`](../../standards/20260519-MASTER_PLAN_STANDARD.md)**. Do not restate the contract here.

When authoring or revising a plan, this skill is responsible for:

1. **Conforming** the artifact to that standard (every gate below references it).
2. **Refusing to mark Approved** until the standard's § 4 approval gate is satisfied.
3. **Reporting drift** if an existing plan file deviates from the standard's section list.

---

## Continuous integrity rules

After every major phase, answer **yes/no** with evidence:

| Question | If no → |
|----------|---------|
| Architecture aligned with project goals? | Revise Phase 1–2 |
| Unverified assumptions remain? | Add to Unknowns; ask or waive |
| Unnecessary complexity introduced? | Simplify; log decision |
| Scalability risks identified? | Risk registry |
| Operational risks identified? | Risk registry |
| Security concerns addressed? | Phase 2/12 update |
| Agents can execute tasks safely? | Phase 6 decomposition |
| Requirements traceable to tasks? | Fix matrix |
| Hidden dependencies? | Phase 4 update |
| Unresolved ambiguities? | Block gate or waiver |

---

## Hallucination prevention

- Label: **Confirmed** (file path + snippet or test command + exit code), **Inference**, **Unverified**, **Estimate**.
- **Confirmed without cite** → downgrade to **Inference** in review; do not ship code on uncited Confirmed claims.
- Prefer proven stack from `REPLACE:TECH_STACK_DOC` and ADRs.
- For external integration: cite `.ai/docs/integration/` + `MANIFEST.txt` when present; do not invent endpoints.
- Request clarification when uncertain; do not invent XSD fields or annex rules.

---

## Advanced modes

Apply **one** mode (default: balanced).

| Mode | Optimize for |
|------|----------------|
| **startup** | Speed, low cost, rapid iteration; accept more manual ops |
| **enterprise** | Compliance, auditability, governance, formal gates |
| **ai-native** | Agent orchestration, task granularity, cross-validation |
| **ultra-scale** | Throughput, distribution, failure domains |

Document mode tradeoffs in Decision log.

---

## Status protocol

1. Resolve project name (README → HANDOFF → `.cursorrules`).
2. Confirm **plan-master-ready** in HANDOFF (or run `@plan-foundation certify` first).
3. Find latest `{PLANS_ROOT}/full/*-full-plan.md` (by date prefix).
4. Read plan header + Execution Roadmap + Registries.
5. Evaluate [Implementation-ready](#implementation-ready) (this skill owns this gate).
6. Output [Status report format](#status-report-format).

### Implementation-ready

Answer **implementation-ready: yes** only when **all** are true:

1. **plan-master-ready** still valid (HANDOFF date; re-run foundation certify if foundation changed).
2. Master plan `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md` exists with **Status: Approved** (or owner waiver in HANDOFF).
3. Plan integrity **pass** or documented waivers.
4. Global acceptance criteria and validation gates (plan §20–21) reviewed.
5. No owner blockers in HANDOFF/NEXT that gate **broad** multi-milestone execution (project may document M1-only waivers).

If master plan **missing** → **implementation-ready: no** - run **greenfield**. If **Draft** → **no** until Approved.

**Not the same as:** M1 platform skeleton when foundation certified plan-master-ready and NEXT recommends it.

### Status report format

```markdown
## Plan-master status - <Project>

**As of:** <date> · **Mode:** status (read-only)

### Summary
- **Plan-master-ready (foundation):** yes | no - from HANDOFF; if no, stop
- **Plan artifact:** <path or none>
- **Plan status:** Draft | Approved | …
- **Implementation-ready:** yes | no - **scored here only**
- **Integrity (last run):** pass | fail | not run
- **Recommended next:** <approve plan | continue plan | begin M1 per roadmap>

### Phase progress
| Phase | Status | Evidence |
|-------|--------|----------|
| P0 … P6 | done/partial/not started | section headings / gates |

### Traceability coverage
- FR count / traced %
- Gaps: <list>

### Top risks and unknowns
- <from plan registries>

### Owner blockers
- <from NEXT.md / HANDOFF>

### Completion checklist
| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Mode detected | pass | status |
| 2 | Foundation/plan read | pass/fail | paths |
| … | | | |
```

---

## Continue protocol

0. Run [Prerequisite gate](#prerequisite-gate-mutating-modes) **PG1** (and **PG2** continue row).
1. Run abbreviated **status**.
2. Find **first phase** not `done`.
3. Complete that phase per workflow; update plan artifact.
4. Run integrity subset for completed phase.
5. If **Phase 5** complete (integrity **pass** or documented waivers) and user approved → set plan **Approved**; sync **one** line to `NEXT.md` recommended next.
6. Output completion checklist report.

---

## Greenfield protocol

0. Run [Prerequisite gate](#prerequisite-gate-mutating-modes) **PG1** (and **PG2** greenfield row).
1. Collect [Initial input](#initial-input-greenfield-or-supplement).
2. Create `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md` with header **Draft**.
3. Walk P0→P6; present **one phase INTERACTION** at a time when owner input required.
4. Do not mark **Approved** until P5 **pass** (or documented waivers).
5. Update HANDOFF **Repository state** only if user asks or `session-control` **close** runs.

---

## Probe protocol

The **interactive front-end to `integrity`**: where `integrity` *detects* contradictions automatically, `probe` *asks the owner* to resolve human-answerable gaps (vague NFR targets, unmapped FRs, ownerless mitigations) and records the answers into the plan + registries. Run **probe first, then integrity**. Engine: **[`.ai/skills/probe-protocol.md`](../probe-protocol.md)** (loop, scoring, ledger - not restated here).

**Coverage profile (caller contract):**

| Parameter | Value |
|-----------|-------|
| **Coverage map** | [Master coverage map](reference.md#master-coverage-map) (M-D1…M-D7) in `reference.md` |
| **Exit gate** | [Implementation-ready](#implementation-ready) (+ Phase 5 integrity **pass**) |
| **Ledger path** | `{PLANS_ROOT}/full/PROBE_LEDGER.md` |
| **Target** | Coverage ≥ 85%; no gate-blocking dimension below **partial** |

**Sub-modes:** `probe` (one iteration) · `probe - until ready` (loop to target, ≤5 questions/batch) · `probe - status` (read-only).

**Protocol:**

0. Run [Prerequisite gate](#prerequisite-gate-mutating-modes) **PG1** (and **PG2** probe row - a Draft/partial `*-full-plan.md` must exist; else run **greenfield** first).
1. **ASSESS:** read the plan body (Execution Roadmap, Traceability matrix, NFRs), the three registries, and `PROBE_LEDGER.md`. Score M-D1…M-D7.
2. Run the engine loop ([probe-protocol.md § The loop](../probe-protocol.md#the-loop)).
3. **RECORD** answers into the **plan body** (quantified NFRs, added tasks, acceptance criteria) and the canonical registries (`ASSUMPTIONS`, `UNKNOWNS`, `RISK_REGISTRY`) - never fork lists.
4. Update `PROBE_LEDGER.md`; emit the [probe report](../probe-protocol.md#output-report-every-probe-run).
5. **On target reached:** recommend `@plan-master integrity` (automated sweep) → then `@plan-master status` for **implementation-ready**. probe does **not** set `Approved`.

**Anti-patterns:** see [probe-protocol.md § Anti-patterns](../probe-protocol.md#anti-patterns). In master specifically: do **not** mark the plan **Approved** or skip `integrity` because probe reached target - probe gathers input; integrity + the § 4 approval gate still decide Approved.

---

## Revise protocol

0. Run [Prerequisite gate](#prerequisite-gate-mutating-modes) **PG1** (and **PG2** revise row).
1. Read latest `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md` and the user's stated reason (after `-`).
2. Apply delta; bump version note in plan header; re-run Phase 5 integrity subset.
3. Do not set **Approved** until P5 **pass** (or documented waivers).
4. Output completion checklist.

---

## Completion checklist (all modes)

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Mode detected correctly | pass/fail | |
| 2 | Foundation artifacts read (or YAML input) | pass/skip | paths |
| 3 | Registries maintained | pass/fail | |
| 4 | Traceability chain present | pass/fail | matrix |
| 5 | 25 mandatory sections present (final) | pass/fail/skip | status only |
| 6 | Phase gate satisfied | pass/fail/skip | |
| 7 | No secrets/PII in output | pass/fail | |
| 8 | No application code written | pass | |
| 9 | Integrity (P5) if completing plan | pass/fail/skip | |
| 10 | NEXT.md synced (if Approved) | pass/skip | |

---

## Anti-patterns

- Replacing feature SPECs with a monolithic plan paragraph
- Skipping Phase 5 to save time
- Tasks without file paths or acceptance criteria
- Duplicate ADR decisions with different conclusions
- Marking Approved with open unknowns blocking high-risk work (without waiver)
- Running **greenfield** / **continue** / **revise** when **plan-master-ready: no** (see § Prerequisite gate)
- Editing archived decision prompts during plan cleanup
- Claiming plan complete without checklist evidence

---

## Show protocol

*(Legacy alias: `task`. Both invocations resolve here.)*

Read-only. No writes to plan or HANDOFF.

**Trigger:** `@plan-master show M{N}-T{N}` · `@plan-master show M{N}` · (legacy) `@plan-master task …`

1. Locate `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md` (latest by date prefix).
2. Navigate to §19 Incremental Execution Roadmap → milestone M{N}.
3. If a task ID was given (`M{N}-T{N}`): return that task's full record.
4. If only a milestone was given (`M{N}`): return the full task table for that milestone.
5. Output:

```markdown
## plan-master show - {M{N}-T{N} | M{N} all tasks}

**Plan:** {path} · **Milestone:** M{N} - {name}

| ID | Description | Files | FR/NFR | Complexity | Status |
|----|-------------|-------|--------|------------|--------|
| M{N}-T{N} | … | … | … | … | … |

**Acceptance criteria** (task-level):
- …

**Governing SPEC rules:**
- R{N}: … (from `{FEATURE_SPEC_ROOT}/<context>/SPEC`)
```

6. If the task ID does not exist in the plan → say so explicitly; do not invent content.
7. If the plan does not exist → recommend `@plan-master greenfield`.

---

## Strategic recommendations (include in plan output)

The plan SHOULD recommend:

- Periodic architecture reviews (quarterly or per milestone)
- Cross-model verification for high-risk / security tasks
- Milestone audits before merge to `main`
- Implementation retrospectives
- Security review before production integration credentials
- Load testing before scale-up
- Staged deployments and progressive hardening
