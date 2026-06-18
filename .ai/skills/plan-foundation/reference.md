# plan-foundation - reference

Supplement to `skill.md`. **How to invoke**, **verify**, and **certify plan-master-ready**.

**Anti-drift reminder:** `{PLANS_ROOT}/foundation/` (docs 01–04) = **foundation inputs**. `*-full-plan.md` = **master plan** (plan-master skill only). Never call doc 04 "the full plan" - say **architecture foundation** or **foundation doc 04**. Doc 01 heading: `Architecture directions (non-prescriptive - architecture foundation in doc 04)`. See [Terminology](skill.md#terminology-required--prevents-confusion-with-plan-master).

---

## Readiness states (do not confuse)

| State | Question | Who certifies | Unlocks |
|-------|----------|---------------|---------|
| **foundation-complete** | Do P0–P6 artifacts and gates pass? | plan-foundation **status** | Continue fixing foundation |
| **plan-master-ready** | Is foundation semantically mature enough for a master plan? | plan-foundation **certify** + `plan-master integrity` | `@plan-master greenfield` / `continue` |
| **implementation-ready** | Is the Approved master plan safe to execute broadly? | **plan-master** **status** only | Multi-milestone implementation |

---

## How to invoke (quick reference)

| Goal | Prompt (Cursor) | Mode |
|------|-----------------|------|
| Snapshot (foundation only) | `@plan-foundation` status | status |
| Ready for master plan? | `@plan-foundation` status - plan-master-ready? | status |
| Certify for plan-master | `@plan-foundation` certify plan-master-ready | certify |
| Resume incomplete gate | `@plan-foundation` continue | continue |
| New project from scratch | `@plan-foundation` greenfield - \<idea\> | greenfield |
| Ready to code? (broad) | `@plan-master` status - implementation-ready? | **plan-master** (not plan-foundation) |

**Explicit file path (any agent):**

```
Read .ai/skills/plan-foundation/skill.md - run status mode. Read-only.
```

```
Read .ai/skills/plan-foundation/skill.md - run certify mode. Update HANDOFF if plan-master-ready passes.
```

### Claude Code / opencode / Codex

```
Follow .ai/skills/plan-foundation/skill.md in status mode.
Report foundation-complete and plan-master-ready with evidence. Redirect implementation-ready questions to plan-master.
Do not create files unless certify mode and HANDOFF update requested.
```

```
Follow .ai/skills/plan-foundation/skill.md in certify mode.
Run plan-master integrity on foundation artifacts, then evaluate S4 criteria.
```

---

## Verification playbook

### Step 1 - Foundation status (always start here)

```
@plan-foundation status
```

**Agent must:**

1. Read `skill.md` Step 0 → **status**
2. Read S2 artifacts: HANDOFF, NEXT, foundation doc 04, registries, `*-full-plan.md` if present
3. Evaluate P0–P6 per gate completion model (not file-exists-only)
4. Report: **foundation-complete**, **plan-master-ready** only (if user asked implementation-ready → redirect to plan-master)

**Pass:** Report lists evidence paths per phase.  
**Fail:** Missing reads or only glob counts without integrity.

---

### Step 2 - Semantic integrity (before plan-master-ready)

When foundation-complete is **yes** but plan-master-ready is **not evaluated** or **no**:

```
@plan-master integrity
```

Or inline during certify:

```
@plan-foundation certify plan-master-ready
```

(plan-foundation orchestrates; plan-master supplies integrity rules.)

**Pass:** `plan-master integrity` → **pass** or **pass with waivers** in HANDOFF.  
**Fail:** Contradictions ADR ↔ SPEC ↔ foundation doc 04 → fix via `@plan-foundation continue`.

---

### Step 3 - Certify plan-master-ready

```
@plan-foundation certify plan-master-ready
```

**Agent must:**

1. Confirm all [S4 criteria](skill.md#s4--plan-master-readiness) (10 rows) with pass/fail + evidence
2. Require `plan-master integrity` result on **foundation** artifacts
3. On **yes**: write `Plan-master-ready: <date>` in HANDOFF §Repository state
4. Recommend next: `@plan-master greenfield` (no master plan yet) or `@plan-master continue` (draft exists)

**Do not** run `@plan-master greenfield` if certification is **no**.

---

### Step 4 - Master implementation plan (plan-master skill)

After **plan-master-ready: yes**:

```
@plan-master greenfield
```

or

```
@plan-master continue
```

**Produces:** `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md` ([master plan artifact](skill.md#master-plan-artifact))

**Pass:** Plan file exists with 25 mandatory sections; registries linked, not duplicated.  
**Not yet implementation-ready** until Status: **Approved**.

---

### Step 5 - Implementation-ready check (plan-master skill - not plan-foundation)

After master plan exists:

```
@plan-master status - implementation-ready?
```

**Agent must:** Evaluate master plan Approved + validation gates (plan-master skill). plan-foundation does **not** score this.

**Pass:** plan-master reports implementation-ready **yes** with evidence.

---

## Example - post-foundation sequence

| Check | Typical next step |
|-------|-------------------|
| foundation-complete | **no** → `@plan-foundation greenfield` or `continue` |
| plan-master-ready | **no** → `@plan-foundation certify plan-master-ready` |
| Master plan missing | `@plan-master greenfield` |
| implementation-ready | `@plan-master status` (authoritative) |

```
1. @plan-foundation status
2. @plan-foundation certify plan-master-ready
3. @plan-master greenfield
4. (owner reviews) → master plan Approved
5. @plan-master status
6. @session-control start → @code-implementation plan - M1
```

---

## Mode comparison

| Mode | Writes files | Runs plan-master integrity | Updates HANDOFF |
|------|--------------|--------------------------|-----------------|
| status | no | reports last result | no |
| certify | HANDOFF only if pass | **yes** (required) | yes on pass |
| continue | yes (artifacts) | at P3+ gates | yes on gate |
| greenfield | yes (P0→P6) | at P3+ gates | yes on gate |

---

## Integration with plan-master

| plan-foundation event | plan-master action |
|----------------------|------------------|
| GATE p3, p4, p5 | integrity subset |
| **certify** / GATE p6 | **integrity** on foundation (required) |
| plan-master-ready **yes** | **greenfield** or **continue** |
| Master plan Approved | **plan-master** **status** → implementation-ready |
| ADR ↔ SPEC contradiction | **integrity** |

---

## Planning registry templates

Create at **P0** (empty) or use seeded files in mature repos.

### ASSUMPTIONS.md

```markdown
# ASSUMPTIONS - planning registry
**Updated:** YYYY-MM-DD

| ID | Assumption | Label | Source | Notes |
|----|------------|-------|--------|-------|
| A1 | … | Confirmed \| Inference \| Unverified | path/ADR | |

## Rejected
| ID | Assumption | Reason |
```

### RISK_REGISTRY.md

```markdown
# RISK_REGISTRY - planning registry
| ID | Risk | Category | Likelihood | Impact | Mitigation | Status | Owner |
```

### UNKNOWNS.md

```markdown
# UNKNOWNS - planning registry
| ID | Question / blocker | Blocks | Owner | Status |
```

---

## P0 initial scope (product-intent capture)

**Owner skill:** `@plan-foundation` **greenfield** (Phase 0 - Capture). There is **no** `code-foundation` skill.

**Canonical path:** `{PLANS_ROOT}/foundation/YYYYMMDD-01-<project-slug>-initial-scope.md` (foundation doc 01).

**Not the seed:** `{PROMPTS_ROOT}/initial.md` - user-owned scratch; skills **must not** read or create unless the user explicitly names that path.

### Greenfield creates (minimum)

```markdown
# <Project Name> - Initial exploration and scope

## Audience and document purpose
…

## Assumption ledger

### Founder intent (verbatim - P0 capture)
<paste raw product idea from user>

### Confirmed facts (repository evidence)
…

## Architecture directions (non-prescriptive - architecture foundation in doc 04)
…
```

P1 expands doc 01; P1 also produces docs 02–04. Doc 01 is the **mini/preliminary plan** - not a prompt file.

---

## Glob patterns (artifact detection only)

Use for **foundation-complete** artifact presence - **not** for plan-master-ready (requires semantic checks).

| Phase | Glob | Min count |
|-------|------|-----------|
| P1 scope | `{PLANS_ROOT}/foundation/*-01-*.md` | 1 |
| P1 architecture | `{PLANS_ROOT}/foundation/*-04-*.md` | 1 |
| P2 ADRs | `{DECISIONS_ROOT}/20*.md` | ≥4 excluding README |
| P3 conventions | `.ai/standards/*CONVENTIONS*.md` | 1 |
| P3 features | `{FEATURE_SPEC_ROOT}/*/20*-SPEC.md` | ≥1 |
| P4 stack | `REPLACE:TECH_STACK_DOC` | 1 |
| P5 compose | `docker-compose.yml` OR `*docker-compose-proposal*` | 1 |
| P6 ops | `README.md`, `HANDOFF.md`, `NEXT.md` | 3 |
| Registries | `ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md` | 3 |
| Master plan | `{PLANS_ROOT}/full/*-full-plan.md` | 0 until plan-master runs |

---

## Common blockers

| Blocker | Affects | Where |
|---------|---------|-------|
| Gate passed on file exists only | plan-master-ready | Re-run gate + shared integrity |
| No `plan-master integrity` run | plan-master-ready | `@plan-master integrity` |
| Master plan missing | implementation-ready | `@plan-master greenfield` |
| Master plan Draft | implementation-ready | Owner review → Approved |
| Open compliance / legal ADR | implementation-ready only (optional waiver for M1) | HANDOFF, UNKNOWNS |
| Docker not approved | foundation P5 | continue P5 |

---

## Wrong prompts

| Prompt | Problem | Use instead |
|--------|---------|-------------|
| `@plan-master greenfield` before certify | Master plan on weak foundation | `@plan-foundation certify` first |
| "@plan-foundation implementation-ready?" | Wrong skill | `@plan-foundation status` then `@plan-master status` |
| "foundation status" + write domain SPEC | Mixed modes | status, then continue |
| "start foundation" with full HANDOFF | Re-runs P0 | continue |
| Glob-only check | False pass | status + certify |

---

## Optional slash commands

| Command | Mode |
|---------|------|
| `/foundation status` | status |
| `/foundation certify` | certify |
| `/foundation continue` | continue |
| `/foundation start` | greenfield |

---

## Traceability quick check (P3+)

- [ ] Purpose → foundation scope (doc 01)
- [ ] ADRs referenced in SPEC
- [ ] R1… in test plan
- [ ] Row in plan-master trace matrix (when master plan exists)

---

## Gate pass vs semantic pass

| Wrong | Right |
|-------|-------|
| Files on disk → plan-master-ready | certify + S4 + integrity |
| HANDOFF complete, empty UNKNOWNS | Deferred ADRs in UNKNOWNS |
| P6 done → implementation-ready | P6 → plan-master-ready → plan-master → Approved → implementation-ready |

---

## Foundation coverage map

The **coverage profile** consumed by `@plan-foundation probe` (engine: [`.ai/skills/probe-protocol.md`](../probe-protocol.md)). Each dimension lists "what good looks like" and the [S4](skill.md#s4--plan-master-readiness) criteria it unblocks. Gate-blocking dimensions (weight 2 in the Coverage Score) are marked **★**.

| Dim | Topic | What good looks like | Primary S4 link | Records into |
|-----|-------|----------------------|-----------------|--------------|
| **D1 ★** | Product intent & success | Founder intent verbatim + measurable success criteria | S4-7 (traceability from goal) | doc 01 §Founder intent |
| D2 | Audience / personas | Named personas or user types; primary journeys | S4-9 (UX/UI direction) | doc 01 §Audience; personas-v1 |
| **D3 ★** | Scope in / out | Explicit in-scope and out-of-scope for v1 | S4-1 (foundation-complete) | doc 01 §Scope |
| D4 | Functional capabilities | Core capabilities enumerated; map to bounded contexts | S4-3 (high-risk SPECs) | doc 01; SPEC drafts |
| **D5 ★** | NFRs | Quantified perf/availability/security/privacy/i18n/a11y/cost targets | S4-8 (architecture fitness) | doc 04; observability/threat-model |
| D6 | Integrations & ext deps | External APIs/files identified + mirrored (MANIFEST) | S4-8 (fitness) | doc 02; MANIFEST |
| D7 | Data model & sensitivity | Key entities + PII/data-classification | S4-8 (security/fitness) | data-classification standard |
| D8 | Constraints | Budget, timeline, team size, ops model, hosting limits | S4-2 (core ADRs) | ASSUMPTIONS; doc 01 |
| **D9 ★** | Deploy / hosting / tenancy | Hosting, tenancy model, deploy/rollback path decided | S4-2, S4-4 (ADRs + map) | ADRs; doc 04 |
| **D10 ★** | Risks & assumptions | Top risks have mitigation+owner; assumptions labeled | S4-5 (registries) | RISK_REGISTRY; ASSUMPTIONS |

**Target:** Coverage ≥ 85% with no ★ dimension below **partial**. **Ledger:** `{PLANS_ROOT}/foundation/PROBE_LEDGER.md` (template: `templates/work/plans/foundation/PROBE_LEDGER.md.template`).

**Invocation (Cursor):** `@plan-foundation probe` · `@plan-foundation probe - until ready` · `@plan-foundation probe - status`
**Any agent:** `Read .ai/skills/plan-foundation/skill.md - run probe mode. Use the Foundation coverage map and .ai/skills/probe-protocol.md engine. Record answers into doc 01 + registries; update PROBE_LEDGER.md.`

---

## Greenfield walkthrough - INTERACTION and IF templates

Used by `@plan-foundation greenfield`. Skill body holds **Phase headers, Artifacts, and GATE checklists** (binding); this section holds the **questionnaires** (scaffolding the agent reads when running greenfield).

### Interaction block format

```markdown
## INTERACTION: <id>
**Q:** <question>
**Type:** single_select | multi_select | free_text | confirm
**Options:** (omit for free_text/confirm)
- `value` | Label | Why this matters
**Default:** <value>  (optional)
**Skip if:** <file or ADR exists>  (optional)
```

Branch with `## IF: <id> = <value>`.

### Owner decision questionnaires (any phase)

When a product choice blocks SPECs (UX mode, vertical, compliance wording):

1. Create `{PROMPTS_ROOT}/decision_<NNN>_<slug>.md` with questions + space for owner answers.
2. Create `{DECISIONS_ROOT}/YYYYMMDD-<NNN>-<slug>-proposed.md`.
3. After owner fills the prompt → **Decided** ADR + `{FEATURE_SPEC_ROOT}/<slug>/YYYYMMDD-SPEC-amendment-NN.md`.
4. **Archive the prompt** - add "do not edit"; never delete owner answers.

### Phase 0 - Capture (interactions)

#### INTERACTION: p0-name

**Q:** What is this project called? (Used in README, HANDOFF, and .cursorrules.)
**Type:** free_text
**Skip if:** README or HANDOFF already names the project and user did not ask to rename

### Phase 1 - Exploration (interactions)

#### INTERACTION: p1-integrations

**Q:** External integrations in v1?
**Type:** multi_select
**Options:**
- `rest-api` | REST API | External HTTPS service
- `gov-api` | Government / regulatory API | Tax, customs, e-invoicing
- `payment` | Payment gateway | Stripe, acquirer, etc.
- `file-exchange` | File exchange | XSD, EDI, CSV import/export
- `none` | None | No external deps in v1

#### IF: p1-integrations includes gov-api or file-exchange

Mirror vendor artifacts under `.ai/docs/integration/<vendor>-<version>/` + `MANIFEST.txt` (URL, path, SHA-256, date).

#### INTERACTION: p1-adjacent

**Q:** Adjacent modules users will eventually need?
**Type:** multi_select
**Options:**
- `inventory` | Inventory | Stock, warehouses
- `accounting` | Accounting | GL, journal entries
- `crm` | CRM | Customer management
- `pos` | POS | Hardware, quick-sale
- `reporting` | BI/Reporting | Dashboards, exports
- `ecommerce` | E-commerce | Online store sync
- `none` | None | v1 is self-contained

### Phase 2 - ADRs (interactions)

#### INTERACTION: p2-backend

**Q:** Backend stack?
**Type:** single_select
**Options:**
- `python-fastapi` | Python + FastAPI
- `ts-node` | TypeScript + Node.js
- `go` | Go
- `rust` | Rust
- `csharp` | C# + .NET
**Default:** python-fastapi

#### INTERACTION: p2-frontend

**Q:** Frontend?
**Type:** single_select
**Options:**
- `nextjs` | Next.js + React
- `react-vite` | React + Vite
- `vue` | Vue/Nuxt
- `svelte` | SvelteKit
- `none` | API/CLI only
**Default:** nextjs

#### INTERACTION: p2-hosting

**Q:** Hosting?
**Type:** single_select
**Options:**
- `aws` | AWS
- `gcp` | Google Cloud
- `fly` | Fly.io
- `railway` | Railway
- `vps` | VPS / bare metal
**Default:** aws

#### INTERACTION: p2-tenancy

**Q:** Multi-tenant?
**Type:** single_select
**Options:**
- `schema-per-tenant` | Schema-per-tenant
- `row-level` | Row-level (RLS)
- `single-tenant` | Single-tenant deployments
**Default:** schema-per-tenant for SaaS; single-tenant for on-prem products

#### INTERACTION: p2-locales

**Q:** UI/document languages?
**Type:** multi_select
**Options:** `en`, `es`, `zh`, `ru`, `pt`
**Default:** en

### Phase 5 - Infrastructure (interactions)

#### INTERACTION: p5-local-dev

**Q:** Local dev setup?
**Type:** single_select
**Options:** `docker-compose` | `bare` | `devcontainer`
**Default:** docker-compose

#### INTERACTION: p5-sandbox

**Q:** Sandbox runbook for external API onboarding?
**Type:** single_select
**Options:** `yes` | `no`
**Default:** yes if p1-integrations != none

#### INTERACTION: p5-approve-compose

**Q:** Review the docker compose proposal. Approve and create `docker-compose.yml`, `Dockerfile.*`, `.env.example`?
**Type:** confirm
**Depends on:** p5-local-dev = docker-compose
**Affects:** docker-compose.yml, Dockerfile.api, Dockerfile.dashboard, .env.example, HANDOFF.md, NEXT.md

#### IF: p5-approve-compose = yes

Create the files per the proposal. Update HANDOFF and NEXT to reflect approval.

### Phase 6 - Operations (interactions)

#### INTERACTION: p6-done

**Q:** Foundation P0–P6 is complete and **plan-master-ready** is certified. Proceed to **plan-master** for the master implementation plan (`{PLANS_ROOT}/full/YYYYMMDD-full-plan.md`)?
**Type:** confirm
**Skip if:** plan-master-ready is **no** - list blockers; use **continue** instead

**On confirm:**

1. Set HANDOFF: foundation gate snapshot complete; **Plan-master-ready: \<date\>**.
2. Invoke: `@plan-master greenfield` (or `continue` if `*-full-plan.md` exists).
3. After master plan exists: user runs `@plan-master status` for **implementation-ready** (not plan-foundation).
4. M1 skeleton (NEXT.md) may start when **plan-master-ready: yes** even if master plan is Draft - document waiver if skipping plan-master.
