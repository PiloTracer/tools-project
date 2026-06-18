---
title: MASTER_PLAN_STANDARD
status: Binding
owner: plan-master skill
last-updated: 2026-05-19
---

# Master plan artifact standard

Binding contract for the master implementation plan authored by `@plan-master`.
File path (per repo convention): `{PLANS_ROOT}/full/YYYYMMDD-full-plan.md` (latest dated file by prefix is the active plan).

This standard exists so the `plan-master` skill body stays focused on **process** while the **artifact contract** lives where engineering standards are kept (`.ai/standards/`).

---

## 1. Header metadata (required)

Every plan file MUST begin with this block (frontmatter or H1 + bold rows; agnostic to renderer):

```markdown
# <Project> - Full implementation plan

**Status:** Draft | Under review | Approved | Superseded
**Version:** 1.0
**Created:** YYYY-MM-DD
**Advanced mode:** (if any)
**Foundation snapshot:** (plan-foundation stage + implementation-ready yes/no)
**Plan owner:** (role/name or TBD)
```

**`Status` transitions:** Draft → Under review → Approved → Superseded. Only the plan owner (or a delegated reviewer) may set **Approved**. `@plan-master status` reports the current status; it does **not** flip it.

---

## 2. Mandatory H2 sections (in order)

The plan file MUST contain these 25 H2 sections in the order shown. Empty sections are not permitted - either fill or explicitly mark `N/A - <reason>` (no silent omissions).

| # | Section | What it captures |
|---|---------|-------------------|
| 1 | Executive Summary | Goals, scope, milestone count, top risks in 5-10 lines |
| 2 | Project Goals | Business outcomes; success metrics |
| 3 | Functional Requirements | `FR1…` numbered; each links to ≥1 task in §19 |
| 4 | Non-Functional Requirements | `NFR1…` (performance, availability, security, privacy, i18n, accessibility, cost) |
| 5 | Constraints | Hard constraints (budget, deadline, regulatory, tech) |
| 6 | Assumptions | Inline summary; canonical list at `{PLANS_ROOT}/ASSUMPTIONS.md` |
| 7 | Risks | Top risks; canonical at `{PLANS_ROOT}/RISK_REGISTRY.md` |
| 8 | Unknowns / Open Questions | Inline summary; canonical at `{PLANS_ROOT}/UNKNOWNS.md` |
| 9 | Architecture Overview | System diagram, services, boundaries; cite foundation doc 04 |
| 10 | UX/UI Strategy | High-level UX direction; link personas, ADRs |
| 11 | Data Strategy | Database choice, schema strategy, retention, migration path |
| 12 | Security Strategy | Threat model summary; controls; AuthN/Z; secrets; data classification |
| 13 | Infrastructure Strategy | Hosting, environments, networking |
| 14 | Deployment Strategy | CI/CD, rollout, blue/green or rolling |
| 15 | Scalability Strategy | Bottleneck plan; horizontal/vertical; caching, queues |
| 16 | Observability Strategy | Metrics, traces, logs, SLO/SLI; ties to `observability-spec` standard |
| 17 | Testing Strategy | Unit/integration/contract/e2e; coverage targets; CI gates |
| 18 | Operational Strategy | Runbooks, on-call, incident classes, runtime ops |
| 19 | Incremental Execution Roadmap | Milestones `M1…M{N}` with task tables (see §3 below) |
| 20 | Acceptance Criteria (global) | Cross-milestone acceptance |
| 21 | Validation Gates | Per-milestone validation commands |
| 22 | Rollback and Recovery Considerations | Per-milestone rollback strategy; feature flags; migration reversibility |
| 23 | Technical Debt Prevention Strategy | Refactor pressure points; debt ledger policy |
| 24 | AI-Agent Execution Guidance | Constraints, dangerous paths, model-tier hints (`light` \| `standard` \| `strong`) |
| 25 | Long-Term Maintainability Strategy | Ownership, doc upkeep, deprecation policy |

**Appendices (required after §25):**

- **Decision log:** `D1…` rows: date, choice, alternatives rejected.
- **Traceability matrix:** Goal → FR → ADR → SPEC → task → test → acceptance. Large matrices MAY live in `{PLANS_ROOT}/full/YYYYMMDD-full-plan-trace.md` with a link from §19.
- **Registries reference:** link `ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md` (do not fork content inline).

---

## 3. Milestone and task record schema

Every milestone in §19 MUST contain these fields:

| Field | Content |
|-------|---------|
| Objective | One sentence |
| Scope | In / out |
| Dependencies | Prior milestones, ADRs, owner actions |
| Deliverables | Files/modules/SPECs |
| Tasks | Task table (schema below) |
| Acceptance criteria | Measurable |
| Validation steps | Tests, lint, manual checks |
| Rollback considerations | Feature flags, migrations, deploy order |
| Testing requirements | Unit/integration/e2e/sandbox |
| Complexity | S/M/L |
| Operational impact | Deploy, monitor, runbooks |

Every task uses the globally unique ID **`M{N}-T{N}`** (e.g. `M1-T3`):

```markdown
### Tasks - M{N}: {milestone name}

| ID | Description | Files | FR/NFR | Complexity | Status |
|----|-------------|-------|--------|------------|--------|
| M{N}-T1 | … | `REPLACE:APP_ROOT/…` | FR-{N} | S/M/L | pending |
| M{N}-T2 | … | `REPLACE:APP_ROOT/…` | NFR-{N} | S/M/L | pending |
```

**Rules:**

- IDs are globally unique across all milestones. `M2-T1` ≠ `M1-T1`.
- Shorthand `T{N}` is acceptable when the milestone context is unambiguous (e.g. inside an iteration block). Always use full form in the traceability matrix and cross-milestone references.
- Status values: `pending` | `in-progress` | `done YYYY-MM-DD` | `blocked` | `deferred`.
- Each task links to ≥1 FR or NFR. Tasks with no FR/NFR link are flagged at Phase 4 gate.
- `code-implementation` inherits these rows verbatim when building the `## Current iteration` block in `NEXT.md`.

---

## 4. Approval gate

A plan moves to **`Status: Approved`** only when:

1. All 25 H2 sections present and non-empty (or explicit `N/A - <reason>`).
2. Every FR has ≥1 task in §19; every high-risk task has validation in §17 / §21.
3. Plan integrity check passes (`@plan-master integrity` or `Phase 5` gate per the skill).
4. Decision log has entries for every major architectural choice.
5. Foundation snapshot in header reflects current `plan-master-ready` certification date.
6. Owner signs off (or `@plan-master status` confirms criteria met and owner accepts in `{HANDOFF}`).

Until Approved, broad implementation is forbidden unless `{HANDOFF}` records an explicit per-milestone waiver (typical: M1 platform skeleton).

---

## 5. Maintenance

- Plans are versioned by date prefix; do not edit a `Superseded` plan - create a new dated file.
- Amendments to an `Approved` plan: bump `Version`, add a `## Changelog` entry, keep prior file as the historical record.
- `@plan-master revise` is the only canonical mechanism for structural edits to an Approved plan.

---

## References

- Skill that authors and revises plans: [`.ai/skills/plan-master/skill.md`](../skills/plan-master/skill.md).
- Iteration carrier inheriting task rows: `{ITERATION_CARRIER}` (`.work/plans/NEXT.md`).
- Foundation upstream: [`.ai/skills/plan-foundation/skill.md`](../skills/plan-foundation/skill.md).
- Registries: `{PLANS_ROOT}/ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md`.
