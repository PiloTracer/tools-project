---
name: plan-foundation
description: >-
  Orchestrate foundation planning (P0–P6) and certify plan-master-ready. Use for
  foundation status, continue, greenfield, or certify. Does not author the master
  implementation plan or certify implementation-ready - that is plan-master.
---

# plan-foundation

**Workflow orchestrator** for project foundation - from idea through **plan-master-ready** certification. Stops there; **plan-master** owns the master roadmap and **implementation-ready**. Tool-agnostic (Cursor, Claude Code, opencode, Codex). Project-agnostic: paths use `.ai/` as the documentation root; adapt backend folder name (`apis/`, `src/`, `server/`) per ADR. **Product-intent capture** lives in **P0** of this skill: greenfield creates the **P0 initial scope** mini-plan at `{PLANS_ROOT}/foundation/YYYYMMDD-01-<slug>-initial-scope.md` (foundation doc 01). There is **no** separate `project-init` or `code-foundation` skill in this registry.

**Hard rule - `{PROMPTS_ROOT}/initial.md`:** User-owned scratch only. This skill **must not** read or create it unless the user **explicitly** names that path in the same invocation.

**Canonical path:** `.ai/skills/plan-foundation/skill.md` (this file). **Invocation examples:** `reference.md`.

---

## Role charter (anti-drift)

**This skill's job ends at `plan-master-ready`.** It does **not** produce or replace the master implementation plan.

| In scope (plan-foundation) | Out of scope (use plan-master or implementation) |
|----------------------------|--------------------------------------------------|
| P0–P6 gates, HANDOFF, NEXT, registries | `*-full-plan.md` authoring |
| `{PLANS_ROOT}/foundation/` docs 01–04 | Milestones M1…, agent task decomposition |
| ADRs, SPECs, CONVENTIONS, directory map | **implementation-ready** certification |
| Certify **plan-master-ready** | Expanding doc 04 into a 25-section execution roadmap |
| Invoke `plan-master integrity` on foundation artifacts | Duplicating plan-master mandatory sections inside foundation files |

**Drift signals (stop and redirect):**

- User asks for "full implementation plan", "roadmap", or "milestones" during foundation work → recommend `@plan-master` after certify.
- Agent merges foundation docs 01–04 into one mega-doc "to finish planning" → **forbidden**; inputs stay separate; plan-master produces the unified roadmap.
- Agent treats `{PLANS_ROOT}/foundation/04` as "the full plan" because the word *plan* appears in the title → **wrong**; doc 04 is **architecture foundation** (proposal), not `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md`.
- Agent scores **implementation-ready** in foundation status → redirect to `@plan-master status`.

---

## Foundation documentation - goals and boundaries

**Canonical folder:** `{PLANS_ROOT}/foundation/` (plan-foundation **P1** output).

These documents are **inputs** to plan-master. They are **not** the plan-master artifact and **must not** be written as if they were.

| Doc | Goal | Must contain | Must NOT become |
|-----|------|--------------|-----------------|
| **01** scope | Unambiguous product scope, audience, assumption ledger, risks | In/out scope, adaptation notes | Full FR/NFR numbered list for whole system (plan-master §3–4) |
| **02** integration | Verified external facts (URLs, APIs, XSDs, OAuth) | Evidence, MANIFEST alignment | Implementation tasks or sandbox run steps (runbook stays in `{PLANS_ROOT}/operations/`) |
| **03** adjacency | Optional product lanes, phased ERP seams, v1 out-of-scope | Integration seams, deferred modules | Execution milestone schedule |
| **04** architecture | Bounded contexts, stack, repo layout, decisions §13, foundation gate §14 | Proposal status, cross-links to 01–03 | **Incremental execution roadmap** (plan-master §19); agent task lists (§24) |

**Cross-cutting foundation outputs (other paths, same phase):**

| Artifact | Goal |
|----------|------|
| `{DECISIONS_ROOT}/` | Record **Decided** architectural choices |
| `{FEATURE_SPEC_ROOT}/*/SPEC` | Per-context **what** (rules R1…, test plan) - not **when/order** |
| `REPLACE:TECH_STACK_DOC` | Pinned stack versions |
| `{PLANS_ROOT}/ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md` | Persistent planning memory (linked by plan-master) |
| `{HANDOFF}`, `{ITERATION_CARRIER}` | Session continuity; NEXT = **one** tactical next action only |

**Explicit non-goals of foundation documentation:**

- Not a single unified implementation plan (that is `*-full-plan.md`).
- Not approved for broad multi-milestone execution until plan-master **Approved**.
- Not a substitute for feature SPECs or ADRs.
- Doc 04 may say "foundation ready" or "gate to start code" - that is **foundation-complete / plan-master-ready** language, **not** implementation-ready.

**When foundation docs are "done":** P1 gate passes + shared integrity - then pursue **plan-master-ready** certification, then `@plan-master greenfield`.

### Terminology (required - prevents confusion with plan-master)

| Avoid in speech and markdown | Use instead |
|------------------------------|-------------|
| "full plan" meaning doc 04 | **architecture foundation** or **foundation doc 04** |
| "the full plan" without a path | Clarify: **architecture foundation** vs **master implementation plan** |
| `*-full-plan.md` | **master implementation plan** (plan-master skill output only) |

**Canonical doc 01 heading (use on greenfield and when fixing legacy text):**

```markdown
## Architecture directions (non-prescriptive - architecture foundation in doc 04)
```

**Canonical doc 01 reference to doc 04 (recommended next artifacts list):**

```markdown
**Architecture foundation (doc 04):** `{PLANS_ROOT}/foundation/YYYYMMDD-04-foundation-architecture.md` - … **Not** the master implementation plan (`*-full-plan.md`).
```

Agents **MUST** use this terminology in status/certify reports when pointing at `{PLANS_ROOT}/foundation/04`. Never call doc 04 "the full plan."

---

## Relationship to plan-master

| Responsibility | Skill |
|----------------|-------|
| Gate progression, repo artifacts, ADR workflows, status/continue/greenfield | **plan-foundation** (this skill) |
| Architecture quality, integrity verification, anti-hallucination, scalability/ops realism, execution decomposition quality | **plan-master** |

`plan-foundation` **orchestrates** the planning lifecycle and repository artifacts.

`plan-master` **governs** planning intelligence: when deep architecture validation, risk analysis, UX/UI strategy depth, implementation decomposition, or AI-agent execution guidance is required, the agent **MUST** read and apply `plan-master/skill.md` (at minimum its [Continuous integrity rules](../plan-master/skill.md#continuous-integrity-rules), [Hallucination prevention](../plan-master/skill.md#hallucination-prevention), and Phase 5 integrity protocol).

**Three readiness states** (foundation owns the first two; plan-master owns the third):

| State | Meaning | Certified by |
|-------|---------|--------------|
| **foundation-complete** | P0–P6 artifact/gate checklists pass | plan-foundation status |
| **plan-master-ready** | Foundation mature enough for master strategic plan | plan-foundation + `plan-master integrity` |
| **implementation-ready** | Master plan validated; safe for broad implementation | **plan-master** status (after Approved `*-full-plan.md`) - **not** plan-foundation |

**When to invoke plan-master during foundation:**

| Trigger | plan-master mode |
|---------|----------------|
| Completing GATE p3, p4, p5, or p6 | **integrity** (subset) or inline checklist |
| Contradictions between ADR and SPEC | **integrity** |
| Before certifying **plan-master-ready** | **integrity** (required) |
| After **plan-master-ready** certified | **greenfield** or **continue** (master plan artifact) |
| **implementation-ready** (user asks) | Redirect to `@plan-master status` - out of plan-foundation scope |
| User asks for roadmap / milestones | **continue** or **status** |

Do not duplicate plan-master content in foundation artifacts - **reference** and **link** traceability rows.

---

## Planning lifecycle (shared with plan-master)

Stages and owners are the three readiness states above, then **Code** (FEATURE_STANDARD + SPECs → application source). Per-stage outputs live in each Phase section and [Master plan artifact](#master-plan-artifact); registries are listed in [Planning registries](#planning-registries-canonical-artifacts).

**Shared terminology:** Phase (P0–P6 foundation) vs Phase (0–6 plan-master) - always prefix **foundation P*** or **plan-master P*** in reports. Never conflate **plan-master-ready** with **implementation-ready**.

---

## Master plan artifact

Produced by **plan-master** after foundation is **plan-master-ready**:

```text
{PLANS_ROOT}/full/YYYYMMDD-full-plan.md
```

Optional sibling for large projects:

```text
{PLANS_ROOT}/full/YYYYMMDD-full-plan-trace.md
```

| Property | Rule |
|----------|------|
| **Owner skill** | plan-master (create/revise); plan-foundation references it |
| **Status** | Draft → Under review → **Approved** → Superseded |
| **Canonical role** | Whole-system implementation roadmap (milestones, NFRs, agent tasks) |
| **When required for implementation-ready** | Status must be **Approved** (or explicit owner waiver in HANDOFF) |
| **Registries** | Links to `ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md` - no duplicate lists |

plan-foundation **does not** author the master plan and **does not** certify implementation-ready. It **certifies plan-master-ready** so plan-master can run; plan-master **certifies implementation-ready** when the master plan is Approved.

---

## Planning registries (canonical artifacts)

Create at **foundation P0** (empty templates) and maintain through P6. plan-master **reads and extends** these; do not fork duplicate registries inside the master plan (link instead).

| File | Purpose |
|------|---------|
| `{PLANS_ROOT}/ASSUMPTIONS.md` | Confirmed / inferred / rejected / unresolved assumptions (A1…) |
| `{PLANS_ROOT}/RISK_REGISTRY.md` | Architectural, operational, security, scalability, compliance, agent risks (R1…) |
| `{PLANS_ROOT}/UNKNOWNS.md` | Open questions, blocked decisions, deferred concerns (U1…) |

**Rules:**

- Every new assumption during an INTERACTION → append to ASSUMPTIONS with label **Confirmed** | **Inference** | **Unverified**.
- Every identified risk → RISK_REGISTRY with mitigation or **accepted** + owner.
- Every unanswered blocker → UNKNOWNS with owner and **blocks** (gate id or ADR).
- On gate complete → review all three files; resolve or waive explicitly in HANDOFF.

Exploration doc 01 **Assumption ledger** remains the phase-1 capture; sync summaries into `ASSUMPTIONS.md` at GATE p1.

---

## Traceability requirement

Maintain traceability across foundation artifacts:

```text
Business goal → Requirement (FR/NFR or foundation scope)
    → ADR → SPEC (R1… rules) → Implementation task (NEXT / plan-master)
    → Validation/test → Acceptance criterion
```

**Rules:**

- No major requirement in foundation doc 01 or a SPEC **Purpose** without at least one traceability row (in SPEC, plan-master matrix, or HANDOFF table).
- ADRs must reference the requirement or goal they decide.
- SPECs must list **ADRs referenced** and numbered rules (R1…) testable in the test plan.
- At GATE p3+: spot-check traceability; at P6: plan-master integrity must confirm coverage or document waivers.

---

## Gate completion model

A phase is **done** only when **all** are true:

1. Required **artifacts exist** (paths on disk).
2. **[Shared gate integrity](#shared-gate-integrity-every-gate)** checklist passes.
3. **Registries** reviewed (ASSUMPTIONS, RISK_REGISTRY, UNKNOWNS).
4. No **unresolved architectural contradictions** between ADR, foundation doc 04, and SPECs (or waivers in HANDOFF).
5. For P3+: **architecture fitness** subset evaluated (see below).

**Forbidden:** marking a gate `done` because a file exists without semantic review.

---

## Shared gate integrity (every gate)

Append to **every** GATE checklist below:

- [ ] Integrity validation performed (plan-master rules or `plan-master integrity` mode for P3+)
- [ ] `ASSUMPTIONS.md` reviewed; new items labeled
- [ ] `UNKNOWNS.md` updated; blockers explicit
- [ ] `RISK_REGISTRY.md` updated for risks introduced this phase
- [ ] No unresolved contradictions (ADR ↔ SPEC ↔ foundation doc 04)
- [ ] Traceability spot-check for requirements touched this phase

---

## Hallucination prevention

Agents **MUST**:

- Distinguish **Confirmed** (file cite), **Inference**, **Unverified**, **Estimate**.
- Avoid inventing undocumented APIs, framework capabilities, or compliance rules.
- Mark speculative decisions in ASSUMPTIONS and Decision log (ADR).
- Request clarification when uncertain; do not fake certainty.
- Verify critical technical claims against `REPLACE:TECH_STACK_DOC`, ADRs, `.ai/docs/integration/`, or official vendor docs.

Prefer proven stack pins and operational simplicity over speculative designs.

---

## Architecture fitness review

At **GATE p3, p4, p5, p6** (and when foundation doc 04 changes), evaluate and record in RISK_REGISTRY or HANDOFF:

| Dimension | Question |
|-----------|----------|
| Scalability | Bottlenecks, growth assumptions realistic? |
| Maintainability | Bounded contexts, clear ownership? |
| Operational complexity | Runbooks, deploy path, on-call surface? |
| Coupling | Forbidden cross-context imports avoided? |
| SPOFs | Single points of failure identified? |
| Extensibility | Feature flags / adjacency lanes documented? |
| Deployment realism | Compose/proposal matches `REPLACE:TECH_STACK_DOC`? |
| Observability | Metrics/traces named for new contexts? |
| Rollback | Migrations, feature flags, deploy order? |
| Security | Threat model + data classification alignment? |

Use plan-master Phase 2/5 depth when the gate is **fail** or **partial**.

---

## UX/UI validation

When `p2-frontend` ≠ `none` or personas exist:

- [ ] Personas or UX principles documented
- [ ] Critical journeys named (counter/desk/owner as applicable)
- [ ] Cognitive load, discoverability, consistency considered
- [ ] Accessibility and responsiveness stated (stack TODO → UNKNOWNS)
- [ ] Error, loading, empty states addressed in SPECs or peripherals SPEC
- [ ] Onboarding and power-user paths noted for ADR 012-style products

Defer deep UX strategy to **plan-master** Phase 3; foundation ensures SPECs and personas are not empty shells.

---

## AI-agent execution optimization

Foundation artifacts **MUST** support downstream coding agents:

- SPECs: numbered rules (R1…), test plan, explicit in/out scope
- DIRECTORY_MAP: folder layout matches bounded contexts
- CONVENTIONS: binding before first merge
- NEXT.md: **one** clear recommended next action
- Tasks in plan-master (post-P6): bounded scope, file paths, acceptance criteria

**Critical paths** (regulated domain, signing, KMS, tenancy): recommend cross-model review in HANDOFF or RISK_REGISTRY.

---

## Cross-model verification

For **Decided** ADRs on stack, tenancy, regulated/signing paths, KMS, or interaction mode:

- Recommend independent review (second model or human) before treating as immutable.
- Record review outcome in ADR or ASSUMPTIONS (**Confirmed** after review).
- At P6: list ADRs that were **not** cross-reviewed as **Unverified** risk if compliance-critical.

---

## Step 0 - Pick a mode (always first)

Detect from the user message. If ambiguous, ask once:

| Mode | User intent (examples) | Action |
|------|------------------------|--------|
| **status** | "foundation status", "plan-master-ready?", "foundation-complete?" | [Status protocol](#status-protocol) - read-only; **foundation-complete** + **plan-master-ready** only |
| **continue** | "continue foundation", "what's next", "resume planning" | [Continue protocol](#continue-protocol) - detect phase → next gate |
| **greenfield** | new project, empty repo, "start foundation" | [Greenfield protocol](#greenfield-protocol) - P0→P6 |
| **probe** | "probe the project", "ask me questions", "fill the gaps", "make sure you understand", "what else do you need to know?" | [Probe protocol](#probe-protocol) - adaptive coverage loop; read+write planning artifacts only |
| **certify** | "certify plan-master-ready", "verify foundation for plan-master" | Run [Plan-master readiness](#s4--plan-master-readiness); update HANDOFF if pass |

**Do not** run greenfield INTERACTIONs when the user asked for **status** only.

**Registry:** Full matrix - [`.ai/skills/SKILL_DEPENDENCIES.md`](../SKILL_DEPENDENCIES.md).

**Symmetric verify/repair:** `@plan-verify foundation` orchestrates this skill's **status** + `@plan-master integrity` on foundation artifacts; gaps → `@plan-repair foundation` or `@plan-foundation continue`.

---

## Prerequisite gate

| Mode | Gate |
|------|------|
| **greenfield** | [GF0](#gf0--bootstrap-artifacts) |
| **probe** | [GF0](#gf0--bootstrap-artifacts) (needs `{HANDOFF}` + doc 01 to record into); else suggest **greenfield** |
| **certify** | [CF0](#cf0--foundation-complete) |
| **continue** | Foundation started (≥1 foundation doc or HANDOFF notes P0); else suggest **greenfield** |
| **status** | - (read-only) |

### GF0 - Bootstrap artifacts

Before P0 INTERACTIONs:

1. If `{HANDOFF}` missing → **stop** with the [blocked-report shape](#blocked-report-shape):
   - **Required:** `{HANDOFF}` exists
   - **Detected:** `.work/context/HANDOFF.md` missing
   - **Run first:** `@project-bootstrap init` (or `@session-control` minimal HANDOFF only if user refuses bootstrap in the same message)
2. If `.cursorrules` missing at repo root → **stop** with the same shape:
   - **Required:** `.cursorrules` at repo root
   - **Detected:** missing
   - **Run first:** `@project-bootstrap init`
3. If `REPLACE:` tokens remain in `.cursorrules` → warn; foundation may proceed but record unfilled tokens in the greenfield report.

### CF0 - Foundation-complete

Before **certify**:

1. Evaluate [Foundation-complete (artifact check)](#s3b--foundation-complete-artifact-check).
2. If **foundation-complete: no** → **stop** with the [blocked-report shape](#blocked-report-shape):
   - **Required:** `foundation-complete: yes` (P0–P6 gates closed)
   - **Detected:** `foundation-complete: no` - failing phase/gate list from status
   - **Run first:** `@plan-foundation continue` (finish the failing phase, then re-invoke `certify`)

### Blocked-report shape

Per [SKILL_DEPENDENCIES.md § Blocked report shape](../SKILL_DEPENDENCIES.md#blocked-report-shape) - header: `## @plan-foundation <command> - blocked (prerequisite)`.

---

## Status protocol

### S1 - Resolve project identity

1. Read `README.md` (first `#` heading or project name in intro).
2. Else read `{HANDOFF}` (title or "Repository state").
3. Else read `.cursorrules` (Identity section).
4. If none exist: ask once - **"What is this project called?"** - then use that label in the report only (do not invent files).

### S2 - Read session artifacts (if present)

| File | Purpose |
|------|---------|
| `{HANDOFF}` | Session boundary, explicit unknowns, gate snapshot |
| `{ITERATION_CARRIER}` | Backlog, recommended next, owner blockers |
| `{DECISIONS_ROOT}/README.md` | ADR index |
| `REPLACE:TECH_STACK_DOC` | Stack pins + TODOs |
| `{PLANS_ROOT}/foundation/*-04-*.md` | §13 decisions + §14 foundation gate |
| `{PLANS_ROOT}/ASSUMPTIONS.md` | Assumption governance |
| `{PLANS_ROOT}/RISK_REGISTRY.md` | Risk lifecycle |
| `{PLANS_ROOT}/UNKNOWNS.md` | Open questions and blockers |
| `{PLANS_ROOT}/full/*-full-plan.md` | If present: note path only; **do not** evaluate implementation-ready in foundation status |

### S3 - Evaluate phases (evidence-based)

For each phase, set: **done** | **partial** | **not started**. Use the [Gate completion model](#gate-completion-model) and phase GATE sections. Cite paths as evidence. Mark inferences as **Unverified**. A phase is **not** `done` if [shared gate integrity](#shared-gate-integrity-every-gate) failed.

| Phase | Name | Typical evidence |
|-------|------|------------------|
| P0 | Capture | **P0 initial scope** mini-plan (`{PLANS_ROOT}/foundation/*-01-*-initial-scope.md`), `.cursorrules`, planning registries |
| P1 | Foundation discovery | `{PLANS_ROOT}/foundation/` docs 01–04; optional `02` + `MANIFEST.txt` |
| P2 | ADRs | `{DECISIONS_ROOT}/README.md`, `YYYYMMDD-001` … (core four decided) |
| P3 | Specifications | `CONVENTIONS`, `FEATURE_STANDARD`, `DIRECTORY_MAP`, `{FEATURE_SPEC_ROOT}/*/SPEC` |
| P4 | Cross-cutting | `REPLACE:TECH_STACK_DOC`, threat-model, data-classification, observability, api-style-guide |
| P5 | Infrastructure | docker-compose **proposal** or committed compose; sandbox runbook if external API |
| P6 | Operations | `README.md`, `HANDOFF.md`, `NEXT.md`, `.gitignore` |

**Stage label** (summary for humans):

| Stage | Condition |
|-------|-----------|
| **Not started** | P0 not done |
| **Exploring** | P0–P1 done; P2 incomplete |
| **Deciding** | P2 partial; stack/tenancy ADRs open |
| **Specifying** | P2 core done; P3–P4 in progress |
| **Planning complete** | P0–P6 gates pass; **no** `apis/` / app source |
| **Plan-master ready** | [Plan-master readiness](#s4--plan-master-readiness) **yes** |
| **Implementation started** | Application source tree exists |

### S3b - Foundation-complete (artifact check)

**foundation-complete: yes** when P0–P6 gates pass per [Gate completion model](#gate-completion-model) (file + integrity per phase).

This is **necessary but not sufficient** for plan-master or implementation. Always report **foundation-complete** separately from **plan-master-ready**.

### S4 - Plan-master readiness

Answer **plan-master-ready: yes** only when **all** are true:

1. **foundation-complete: yes** (P0–P6 gates done per gate completion model).
2. Core ADRs **Decided** (stack, hosting, tenancy - project defines "core"; deferred ADRs documented in `UNKNOWNS.md`).
3. Highest-risk bounded context(s) have SPECs with numbered rules (project defines - e.g. payments, compliance).
4. Directory map exists and aligns with foundation doc 04 bounded contexts.
5. Registries populated and reviewed: `ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md`.
6. No **unresolved architectural contradictions** (ADR ↔ foundation doc 04 ↔ SPECs), or waivers in HANDOFF.
7. **Traceability spot-check** passes for requirements touched in foundation (see [Traceability requirement](#traceability-requirement)).
8. **[Architecture fitness review](#architecture-fitness-review)** passes for P3–P6 scope (record in HANDOFF or RISK_REGISTRY).
9. **UX/UI direction** sufficient when UI in scope ([UX/UI validation](#uxui-validation)).
10. **`plan-master integrity`** on **foundation artifacts** returns **pass** or **pass with waivers** documented in HANDOFF (run via plan-master skill; plan-foundation records result).

If any fail → **plan-master-ready: no** + list blockers + recommend **continue** foundation (not plan-master greenfield yet).

**On pass:** Record in HANDOFF §Repository state: `Plan-master-ready: <date>`. Recommend `@plan-master greenfield` or `continue`.

**Anti-pattern:** Running `@plan-master greenfield` when plan-master-ready is **no**.

### S5 - Out of scope: implementation-ready

**Do not** evaluate or certify **implementation-ready** in plan-foundation modes (status, certify, continue, greenfield).

If the user asks "implementation-ready?" or "ready to code?":

1. If **plan-master-ready: no** → answer foundation blockers first.
2. If no `*-full-plan.md` → recommend `@plan-master greenfield` after certify.
3. If master plan exists → redirect: `@plan-master status` (implementation-ready is defined in plan-master skill).

**M1 skeleton** (tactical): may proceed when **plan-master-ready: yes** per NEXT.md and HANDOFF waivers - not the same as implementation-ready.

### S6 - Status report format (mandatory)

```markdown
## Foundation status - <Project Name>

**As of:** <date> · **Mode:** status (read-only)

### Summary
- **Stage:** <stage label>
- **Foundation-complete:** yes | no
- **Plan-master-ready:** yes | no | not evaluated
- **Recommended next:** <continue foundation | certify | @plan-master greenfield>

### Implementation-ready (redirect only - do not score here)
- Master plan: <missing | path - use @plan-master status for Approved/implementation-ready>

### Phase progress
| Phase | Status | Evidence |
|-------|--------|----------|
| P0 … P6 | done/partial/not started | paths |

### Open ADRs / decisions
- <list from decisions/README or HANDOFF>

### Owner blockers
- <from NEXT.md / HANDOFF>

### Risks / unverified
- <from RISK_REGISTRY.md / UNKNOWNS.md>

### Registry snapshot
- Assumptions: <count unresolved>
- Risks: <count open>
- Unknowns: <count blocking>

### Integrity (plan-master)
- Last run: <date or not run> · Result: pass | fail | waived
- **Invoke:** `@plan-master integrity` (Cursor) or "Follow .ai/skills/plan-master/skill.md - integrity mode" (opencode/Codex)
```

**Rules:** Do not modify files in status mode unless the user asks. Do not edit prompts marked **archived** or "do not edit".

---

## Continue protocol

1. Run **Status protocol** S1–S3 (short form - no full report unless user wants it).
2. Find the **first phase** not `done`.
3. If **partial**: complete that phase's **GATE** checklist (artifacts + [shared gate integrity](#shared-gate-integrity-every-gate)); produce missing artifacts.
4. Present the next **INTERACTION** only for unanswered questions in that phase (skip if answers exist in ADRs, foundation docs, or archived decision prompts).
5. Update registries (`ASSUMPTIONS`, `RISK_REGISTRY`, `UNKNOWNS`) when assumptions, risks, or unknowns change.
6. At GATE p3+ → apply [Architecture fitness review](#architecture-fitness-review); run `plan-master integrity` if contradictions found.
**Invoke as:** `@plan-master integrity` (Cursor) or "Follow .ai/skills/plan-master/skill.md - integrity mode" (opencode/Codex). Returns integrity score: pass | pass with waivers | fail.
7. Update `HANDOFF.md` and `NEXT.md` when a gate **passes** completion model (not merely when files are written).
8. At P6 done → evaluate [Plan-master readiness](#s4--plan-master-readiness) → offer `p6-done` confirm only if **plan-master-ready** (or list blockers).
9. After **plan-master-ready**: recommend `@plan-master greenfield` | `continue` - do not author master plan in plan-foundation.
10. After master plan exists → tell user to run `@plan-master status` for implementation-ready (not plan-foundation).
11. Do not write broad multi-milestone implementation without **plan-master** Approved master plan (or HANDOFF waiver).

---

## Probe protocol

Adaptive, gap-driven interrogation that **guarantees foundation understanding** before certification. Engine: **[`.ai/skills/probe-protocol.md`](../probe-protocol.md)** (the loop, scoring, ledger, and ease-of-use rules live there - do not restate them). This section supplies the foundation **coverage profile** only.

**Coverage profile (caller contract):**

| Parameter | Value |
|-----------|-------|
| **Coverage map** | [Foundation coverage map](reference.md#foundation-coverage-map) (D1–D10) in `reference.md` |
| **Exit gate** | [S4 - Plan-master readiness](#s4--plan-master-readiness) (each dimension maps to one or more S4 criteria) |
| **Ledger path** | `{PLANS_ROOT}/foundation/PROBE_LEDGER.md` |
| **Target** | Coverage ≥ 85%; no gate-blocking dimension below **partial** |

**Sub-modes:** `probe` (one iteration, then stop) · `probe - until ready` (loop to target, ≤5 questions/batch) · `probe - status` (read-only Coverage + gaps; asks nothing).

**Protocol:**

1. Run [GF0](#gf0--bootstrap-artifacts) - need `{HANDOFF}` and foundation doc 01 to record answers into.
2. **ASSESS:** read foundation docs 01–04, ADRs, the three registries, and `PROBE_LEDGER.md` (create from template if absent). Score D1–D10.
3. Run the engine loop (ASSESS → PRIORITIZE → ASK → RECORD → RE-SCORE → EXIT) from [probe-protocol.md](../probe-protocol.md#the-loop).
4. **RECORD** answers to their canonical home (doc 01, ADR **Proposed** stubs, `ASSUMPTIONS`, `UNKNOWNS`, `RISK_REGISTRY`) - never fork lists; never set ADR **Decided** from a probe answer.
5. Update `PROBE_LEDGER.md`; emit the [probe report](../probe-protocol.md#output-report-every-probe-run).
6. **On target reached:** recommend `@plan-foundation certify plan-master-ready` (probe fills gaps; certify + `plan-master integrity` still own the gate).
7. **Relationship to greenfield:** greenfield's static `INTERACTION` blocks seed D1–D10; probe adds adaptive follow-ups when an answer is vague or a dimension stays **unknown**. Use probe at each GATE to close residual gaps before declaring the gate done.

**Anti-patterns:** see [probe-protocol.md § Anti-patterns](../probe-protocol.md#anti-patterns). In foundation specifically: do **not** use probe to score **implementation-ready** (out of plan-foundation scope - redirect to `@plan-master status`).

---

## Certify protocol (plan-master-ready)

Use when the user asks to **certify**, **verify for plan-master**, or **plan-master-ready**.

0. Run [CF0 - Foundation-complete](#cf0--foundation-complete).
1. Run **Status protocol** S1–S3 (full evaluation).
2. Run `@plan-master integrity` on foundation artifacts (read-only if status-only; update HANDOFF on certify).
3. Evaluate [S4 - Plan-master readiness](#s4--plan-master-readiness) criterion by criterion with evidence.
4. Output certification report:

```markdown
## Plan-master-ready certification - <Project>

**Foundation-complete:** yes | no
**Plan-master-ready:** yes | no

### Criteria (S4)
| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 … 10 | | pass/fail | |

### If yes
- Record in HANDOFF: `Plan-master-ready: <date>`
- Next: `@plan-master greenfield` or `continue`

### If no
- Blockers: <ordered list>
- Next: `@plan-foundation continue` (missing artifacts) or `@plan-foundation probe` (understanding gaps - vague scope, NFRs, constraints)
```

5. Do **not** create `*-full-plan.md` in certify mode - that is **plan-master**'s job.

---

## Greenfield protocol

0. Run [GF0 - Bootstrap artifacts](#gf0--bootstrap-artifacts).
1. **Project name first** - run `p0-name` before any other INTERACTION unless user already gave the name in the same message.
2. Create the **P0 initial scope** mini-plan at `{PLANS_ROOT}/foundation/YYYYMMDD-01-<project-slug>-initial-scope.md` (foundation doc 01). Capture the raw product idea verbatim in a **Founder intent** subsection under **Assumption ledger**; add placeholder sections for audience, scope expansion, and architecture directions (filled in P1). **Do not** write `{PROMPTS_ROOT}/initial.md` - that path is user-owned scratch; skills read doc 01 instead.
3. Create empty planning registries: `ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md` (templates in reference.md).
4. Walk phases P0→P6; at each **GATE**, present checklist + shared integrity; wait for approval before the next phase.
5. Use **Assumption ledger** in foundation doc 01; sync to `ASSUMPTIONS.md` at GATE p1.
6. Apply [Hallucination prevention](#hallucination-prevention) and [Traceability requirement](#traceability-requirement) throughout.
7. Never write broad implementation code until **plan-master** master plan is **Approved** (foundation ends at plan-master-ready).

---

## Greenfield interaction templates (delegated)

Question scaffolding, defaults, and IF branches for `@plan-foundation greenfield` live in **`reference.md` § Greenfield walkthrough**. Skill body holds only **Phase headers, Artifacts, GATE checklists** (binding). When running greenfield, read the reference section once per phase to drive the questionnaire.

---

## Phase 0 - Capture

**Artifacts:**

```
{PLANS_ROOT}/foundation/YYYYMMDD-01-<slug>-initial-scope.md   - P0 mini-plan (greenfield creates; plan-foundation owns)
.cursorrules                     - identity, core principles, protected files
{PLANS_ROOT}/ASSUMPTIONS.md      - created at P0
{PLANS_ROOT}/RISK_REGISTRY.md
{PLANS_ROOT}/UNKNOWNS.md
```

**Greenfield questions:** `p0-name` - see `reference.md` § Phase 0.

### GATE: p0

- [ ] **P0 initial scope** mini-plan at `{PLANS_ROOT}/foundation/*-01-*-initial-scope.md` (founder intent captured verbatim)
- [ ] `.cursorrules` created with project name and evidence-first / no-PII principles
- [ ] Planning registries created (`ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md`)

**Includes:** [Shared gate integrity](#shared-gate-integrity-every-gate)

---

## Phase 1 - Exploration

**Artifacts:**

```
{PLANS_ROOT}/foundation/YYYYMMDD-01-*-scope.md
{PLANS_ROOT}/foundation/YYYYMMDD-02-*-integration.md     ← skip if p1-integrations = none
{PLANS_ROOT}/foundation/YYYYMMDD-03-*-adjacency.md        ← skip if none adjacent
{PLANS_ROOT}/foundation/YYYYMMDD-04-foundation-arch.md
.ai/docs/integration/MANIFEST.txt                       ← skip if no integration mirror
```

Doc 01 sections: Audience, Assumption ledger, Scope, Risks; heading **Architecture directions (non-prescriptive - architecture foundation in doc 04)** per [Terminology](#terminology-required--prevents-confusion-with-plan-master). Doc 04: Bounded contexts, decisions register §13, foundation-ready gate §14 - title may say "plan" but role is **architecture foundation**, not `*-full-plan.md`.

**Greenfield questions:** `p1-integrations`, `p1-adjacent` and IF branch for gov-api / file-exchange - see `reference.md` § Phase 1.

### GATE: p1

- [ ] Scope doc (01) exists; uses **architecture foundation in doc 04** wording (not "full plan in doc 04")
- [ ] Architecture foundation doc (04) exists with bounded contexts + dependency direction
- [ ] 01↔02↔03↔04 cross-linked
- [ ] Integration mirror + manifest (if applicable)
- [ ] Open questions explicit in `UNKNOWNS.md` (synced from doc 01 assumption ledger)
- [ ] Initial risks in `RISK_REGISTRY.md` (scope, integration, compliance)

**Includes:** [Shared gate integrity](#shared-gate-integrity-every-gate)

---

## Phase 2 - ADRs

**Artifacts:**

```
{DECISIONS_ROOT}/README.md
{DECISIONS_ROOT}/YYYYMMDD-001-backend-stack.md
{DECISIONS_ROOT}/YYYYMMDD-002-*.md …
```

ADR: Context → Decision → Consequences → Alternatives → References. Status: `Proposed | Decided | Deferred | Superseded`.

**Greenfield questions:** `p2-backend`, `p2-frontend`, `p2-hosting`, `p2-tenancy`, `p2-locales` - see `reference.md` § Phase 2.

### GATE: p2

- [ ] ADR index current
- [ ] Stack, hosting, tenancy ADRs **Decided**
- [ ] Deferred ADRs document what they block (entries in `UNKNOWNS.md`)
- [ ] Major ADRs trace to business goals / foundation scope

**Includes:** [Shared gate integrity](#shared-gate-integrity-every-gate) · Recommend [Cross-model verification](#cross-model-verification) for Decided ADRs

---

## Phase 3 - Specifications

```
.ai/standards/YYYYMMDD-CONVENTIONS.md
.ai/standards/YYYYMMDD-FEATURE_STANDARD.md
.ai/standards/YYYYMMDD-DIRECTORY_MAP.md
{FEATURE_SPEC_ROOT}/<bounded-context>/YYYYMMDD-SPEC.md
{FEATURE_SPEC_ROOT}/<slug>/YYYYMMDD-SPEC-amendment-NN.md
```

SPEC sections: Purpose · In/Out scope · Domain language · Rules (R1…) · Data model · APIs · Invariants · Errors · Observability · Security · i18n · Test plan · Open questions · Residual verification.

**Rule:** Do not edit merged SPECs; use amendment siblings.

---

### GATE: p3

- [ ] Conventions + feature standard + directory map on disk
- [ ] ≥1 feature SPEC with numbered behavioural rules
- [ ] SPECs for highest-risk bounded context(s) identified in doc 04
- [ ] Traceability: each SPEC lists ADRs + testable R1… rules
- [ ] [Architecture fitness review](#architecture-fitness-review) recorded

**Includes:** [Shared gate integrity](#shared-gate-integrity-every-gate) · Run `plan-master integrity` subset if high-risk / compliance SPEC present

---

## Phase 4 - Cross-cutting

```
REPLACE:TECH_STACK_DOC
.ai/standards/YYYYMMDD-threat-model.md
.ai/standards/YYYYMMDD-data-classification.md
.ai/standards/YYYYMMDD-observability-spec.md
.ai/standards/YYYYMMDD-api-style-guide.md
{PLANS_ROOT}/YYYYMMDD-personas-v1.md               ← if UI (p2-frontend != none)
```

Optional: `{PLANS_ROOT}/operations/YYYYMMDD-cpa-shortlist.md`, `YYYYMMDD-regulatory-changelog-watch.md` when gov-api or heavy compliance.

---

### GATE: p4

- [ ] Tech stack pins versions; TODOs trace to ADRs or `UNKNOWNS.md`
- [ ] Threat model + data classification exist
- [ ] Observability names metrics per context
- [ ] API style guide sufficient to implement HTTP layer
- [ ] [UX/UI validation](#uxui-validation) (if UI in scope)
- [ ] Security/scalability risks updated in `RISK_REGISTRY.md`

**Includes:** [Shared gate integrity](#shared-gate-integrity-every-gate) · [Architecture fitness review](#architecture-fitness-review)

---

## Phase 5 - Infrastructure

**Artifacts:**

```
{PLANS_ROOT}/operations/YYYYMMDD-docker-compose-proposal.md
{PLANS_ROOT}/operations/YYYYMMDD-sandbox-onboarding.md
```

**Rule:** `docker-compose.yml`, `Dockerfile.*`, `.env.example` - create only after explicit owner approval.

**Greenfield questions:** `p5-local-dev`, `p5-sandbox`, `p5-approve-compose` and IF branch - see `reference.md` § Phase 5.

### GATE: p5

- [ ] Docker approved + files created, OR bare-metal documented, OR approval pending in HANDOFF
- [ ] Sandbox runbook if external integration
- [ ] Ports chosen, .env.example committed
- [ ] Operational/deployment risks in `RISK_REGISTRY.md`
- [ ] Deploy/rollback feasibility noted (HANDOFF or proposal)

**Includes:** [Shared gate integrity](#shared-gate-integrity-every-gate) · [Architecture fitness review](#architecture-fitness-review) (deployment realism)

---

## Phase 6 - Operations

```
README.md
{HANDOFF}
{ITERATION_CARRIER}
.gitignore
.claudeignore                    ← recommended for large vendor mirrors
```

---

### GATE: p6 (FINAL)

- [ ] README start-here table
- [ ] HANDOFF fresh-start checklist + gate snapshot
- [ ] NEXT.md single recommended next action
- [ ] Cross-links valid; no secrets/PII/attribution markers
- [ ] Registries current (`ASSUMPTIONS`, `RISK_REGISTRY`, `UNKNOWNS`)
- [ ] [Plan-master readiness](#s4--plan-master-readiness) evaluated - record **plan-master-ready: yes | no** in HANDOFF

**Includes:** [Shared gate integrity](#shared-gate-integrity-every-gate)

**Not at P6:** implementation-ready (requires Approved master plan - evaluate after plan-master).

**Greenfield question:** `p6-done` (confirm) - see `reference.md` § Phase 6.

Foundation orchestration certifies **plan-master-ready**; **plan-master** authors the [master plan artifact](#master-plan-artifact).

---

## Anti-patterns

- Running greenfield INTERACTIONs during a **status** request
- Editing archived decision prompts
- Writing broad implementation before plan-master master plan Approved
- SPEC after code; merged SPEC edits (use amendments)
- Collapsing inference into fact (assumption ledger / ASSUMPTIONS.md)
- TBD without ADR reference or UNKNOWNS entry
- AI attribution markers
- Skipping gates without documenting waiver in HANDOFF
- **File exists = phase done** (without shared integrity + registries)
- Ignoring `plan-master` when completing P3–P6 gates
- Duplicate registries inside plan-master artifact instead of linking `{PLANS_ROOT}/ASSUMPTIONS.md` etc.
- Marking **plan-master-ready** without `plan-master integrity` on foundation artifacts
- Evaluating **implementation-ready** inside plan-foundation status (use plan-master)
- Confusing **foundation-complete** with **plan-master-ready**
- Running `@plan-master greenfield` before **plan-master-ready: yes**
- Expanding `{PLANS_ROOT}/foundation/` into a substitute for `*-full-plan.md`
- Calling foundation doc 04 "the full plan" in reports (say **architecture foundation** or **foundation doc 04**)

---

## Reference: fully bootstrapped project (example)

When foundation is complete on an adopting repo, **status** typically shows:

| Phase | Expected |
|-------|----------|
| P0–P4 | Foundation docs 01–04, ADRs, SPECs, cross-cutting standards customized |
| P5–P6 | Environments / ops gates per your checklist |
| **Foundation-complete** | **yes** |
| **Plan-master-ready** | **yes** after `certify plan-master-ready` + integrity |
| **Master plan** | **Approved** under `{PLANS_ROOT}/full/` |
| **Implementation-ready** | Ask `@plan-master status` |
| **Next step** | `@session-control start` → `@code-implementation plan - M1` |
