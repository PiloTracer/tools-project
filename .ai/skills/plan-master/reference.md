# plan-master - reference

Supplement to `skill.md`. Invocation examples and edge cases.

---

## Invocation examples

| Action | Prompt |
|--------|--------|
| Status | `@plan-master` **status** |
| Continue | `plan-master` **continue** |
| New plan | `@plan-master` **greenfield** |
| Integrity only | `plan-master` **integrity** |
| Revise | `plan-master` **revise** - add integration sandbox milestone |
| With mode | `plan-master greenfield` - **enterprise** |
| Look up a task | `plan-master` **show** M1-T3   *(alias: `task M1-T3`)* |
| All tasks for a milestone | `plan-master` **show** M4   *(alias: `task M4`)* |

### Cursor

```
@plan-master status
@plan-master continue
@plan-master greenfield - ai-native
Read .ai/skills/plan-master/skill.md and run integrity mode.
```

### Claude Code / opencode / Codex

```
Follow .ai/skills/plan-master/skill.md - status. Read-only.
Follow .ai/skills/plan-master/skill.md - continue. Update `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md`.
```

---

## Mode comparison

| | status | continue | greenfield | integrity | revise |
|---|--------|----------|------------|-----------|--------|
| Read plan | yes | yes | create/update | yes | yes |
| Write plan | no | yes | yes | optional fixes | yes |
| Update NEXT | no | if Approved | if Approved | no | if Approved |
| User questionnaires | no | per phase | per phase | no | targeted |
| P5 integrity | report | on phase complete | before Approved | full | delta |

---

## Foundation inputs (adopting repo)

When planning, **prefer cite over rewrite**:

| Topic | Primary evidence |
|-------|------------------|
| Scope | `{PLANS_ROOT}/foundation/*-01-*.md` |
| Integrations | `*-02-*.md`, `.ai/docs/integration/MANIFEST.txt` (if any) |
| Product lanes | `*-03-*.md` (if any) |
| Architecture | `*-04-foundation-architecture.md` |
| Stack | `REPLACE:TECH_STACK_DOC` |
| Layout | `.ai/standards/*-DIRECTORY_MAP.md` |
| Feature SPECs | `{FEATURE_SPEC_ROOT}/<slug>/*-SPEC.md` |
| Threats / data | threat-model, data-classification standards |
| Local infra | compose files, ops proposals under `{PLANS_ROOT}/operations/` |

Derive milestone order from foundation + SPECs in Phase 5 integrity - do not copy a generic list without repo evidence.

---

## Master coverage map

The **coverage profile** consumed by `@plan-master probe` (engine: [`.ai/skills/probe-protocol.md`](../probe-protocol.md)). Probe is the **interactive complement to `integrity`**: it asks the owner to resolve gaps that an automated sweep can flag but not answer. Gate-blocking dimensions (weight 2) marked **★**.

| Dim | Topic | What good looks like | Primary gate link | Records into |
|-----|-------|----------------------|-------------------|--------------|
| **M-D1 ★** | FR → task coverage | Every FR maps to ≥1 `M{N}-T{N}` task | Phase 4 gate / implementation-ready | plan §19 roadmap + trace matrix |
| **M-D2 ★** | Quantified NFRs | Each NFR has a number (p95 latency, uptime %, cost ceiling) not an adjective | Phase 1 gate | plan §3–4 NFRs |
| M-D3 | Sequencing & dependencies | Milestone order justified by repo evidence; hidden deps surfaced | Phase 4 / continuous integrity | plan §19; UNKNOWNS |
| M-D4 | Resource & parallelization | Team size, parallelizable tracks, critical path stated | Phase 4 | ASSUMPTIONS; plan §19 |
| **M-D5 ★** | Risk mitigation ownership | Each high/critical risk has mitigation **and** owner | Phase 5 gate | RISK_REGISTRY |
| M-D6 | Acceptance criteria | Every milestone + high-risk task has testable acceptance criteria | Phase 4 / Phase 6 | plan §19 task records |
| M-D7 | Agent-execution safety | Tasks have file paths, invariants, validation; model tier tagged | Phase 6 gate | plan §24 agent appendix |

**Target:** Coverage ≥ 85% with no ★ dimension below **partial**. **Ledger:** `{PLANS_ROOT}/full/PROBE_LEDGER.md` (same template as foundation).

**Order:** run `@plan-master probe` to fill these gaps, **then** `@plan-master integrity` for the automated contradiction/fitness sweep, **then** `@plan-master status` for implementation-ready.

**Invocation (Cursor):** `@plan-master probe` · `@plan-master probe - until ready` · `@plan-master probe - status`
**Any agent:** `Read .ai/skills/plan-master/skill.md - run probe mode. Use the Master coverage map and .ai/skills/probe-protocol.md engine. Record answers into the plan body + registries; update PROBE_LEDGER.md. Do not set Approved.`

---

## Traceability matrix (minimal example)

Task IDs use the globally unique **`M{N}-T{N}`** format. Shorthand `T{N}` is acceptable only when the milestone context is explicit.

| Goal | FR/NFR | Component | Task ID | Description | Test | Acceptance |
|------|--------|-----------|---------|-------------|------|------------|
| User signup | FR-01 | `identity` | M2-T1 | register flow R1–R3 | `test_signup_*.py` | 201 + email sent |
| Multi-tenant isolation | NFR-03 | `platform` | M3-T2 | tenant middleware | `test_tenant_isolation` | Cross-tenant read fails |

---

## YAML input example (generic)

```yaml
project: REPLACE:PROJECT_NAME
description: One-line product summary
requirements:
  - Core capability 1
  - Core capability 2
non_functional:
  - Availability target
  - Security / compliance constraint
foundation_docs:
  - {HANDOFF}
  - {PLANS_ROOT}/foundation/*-04-foundation-architecture.md
  - REPLACE:TECH_STACK_DOC
constraints:
  - Dev workflow per .cursorrules
  - No secrets in repo
target_users:
  - Primary persona
advanced_mode: standard | enterprise
```

---

## Integration with session-control

| Session event | plan-master action |
|---------------|------------------|
| **start** | Optional: `plan-master status` if master plan exists |
| **close** | If plan phase completed, note in HANDOFF artifact table |
| Planning-only session | No commit unless `close commit` |

---

## Integration with plan-foundation

```
plan-foundation (P0–P6)  →  plan-master-ready
        ↓
Approved master plan (`*-full-plan.md`)
        ↓
@plan-master status        →  implementation-ready
        ↓
feature SPECs + code     →  per FEATURE_STANDARD / code-implementation
```

Run `plan-foundation status` before `plan-master greenfield` on mature repos.

---

## Edge cases

| Situation | Behavior |
|-----------|----------|
| No `*-full-plan.md` | **continue** → suggest **greenfield** |
| Foundation not ready (plan-master-ready: no) | **Stop** - do not draft plan; run `@plan-foundation certify` first (see skill § Prerequisite gate) |
| Plan contradicts ADR | **fail** P5; do not Approve until ADR amended |
| User wants code in same message | Stop plan mode; switch to implementation with SPEC refs |
| Huge traceability matrix | Split to `*-full-plan-trace.md` |
| Only `.ai/` changed | Commit type `docs` on close |

---

## Optional companion skills (future)

| Skill | Purpose |
|-------|---------|
| `plan-foundation` | Domain/foundation (exists) |
| `session-control` | Session bookends (exists) |
| `integrity-review` | Standalone P5 deep dive |
| `execution-orchestrator` | Task batching for agents |

plan-master **includes** P5/P6; companions are optional splits if skills grow too large.

---

## Wrong prompts

| Prompt | Problem | Use instead |
|--------|---------|-------------|
| `plan-master` write apis code | Wrong skill | Implementation + SPEC |
| Skip foundation on mature repo | Reinvents ADRs | Read `{PLANS_ROOT}/foundation/` + ADRs |
| Approve with open high-risk unknowns | Unsafe | Waivers explicit or resolve |
| `greenfield` during status request | Mode violation | `status` only |

---

## Optional slash commands (team convention)

| Command | Maps to |
|---------|---------|
| `/fp status` | status |
| `/fp continue` | continue |
| `/fp greenfield` | greenfield |
| `/fp integrity` | integrity |

Document in project README if adopted.
