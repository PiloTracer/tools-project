# Workflow guides - operator index (portable)

**Purpose:** Human- and agent-friendly **process** documentation. Normative sections use **`{PLACEHOLDERS}`** - fill once via [Path bootstrap](20260518-tutorial-path-bootstrap.md).

**Filename rules:** Use **`YYYYMMDD-tutorial-<slug>.md`** for operator-facing **step-by-step** docs. Use **`YYYYMMDD-guide-<slug>.md`** for **reference** or internal-style docs (template layers, NFR cross-cuts, planning-methodology companions to skills). **[README.md](README.md)** in this directory holds the **canonical artifact matrix** (planning vs implementation phases, skills, application paths). **This file** is the curriculum and principles companion.

---

## Development process file matrix

The **canonical artifact matrix** - paths that participate in **planning** or **implementation**, including each registered skill’s **`skill.md`** and **`reference.md`**, standards, plans, SPECs, application trees, and protected operations files - lives in **[README.md](README.md#planning-and-implementation-artifact-matrix)**. Open that section for **Status** and **Phase** legends and the full table.

---

## Curriculum map (recommended order)

### A - Orientation

| Step | Guide |
|------|--------|
| 0 | [Path bootstrap (fill placeholders)](20260518-tutorial-path-bootstrap.md) |
| 1 | [End-to-end workflow (layers + rollout)](20260518-guide-end-to-end-workflow.md) |
| 2 | [Full workflow walk-through (example)](20260518-tutorial-full-workflow.md) |
| 3 | [Testing and test suite in the workflow](20260518-guide-testing-and-test-suite-in-workflow.md) |

### B - Planning (strategic)

| Step | Guide |
|------|--------|
| 4 | [Foundation plan (`plan-foundation`)](20260518-guide-plan-foundation.md) |
| 5 | [Master / full plan (`plan-master`)](20260518-guide-plan-master-full.md) |
| 6 | [Fix drift across NEXT + full plan](20260518-tutorial-fix-existing-plans.md) |

### C - Tactical queue (`{ITERATION_CARRIER}`)

| Step | Guide |
|------|--------|
| 7 | [Generate / define NEXT iteration block (`@code-implementation plan`)](20260518-tutorial-next-generate-new.md) |
| 9 | [Fix a broken NEXT.md](20260518-tutorial-next-fix.md) |

### D - Delivery loop (skills + tests)

| Step | Guide |
|------|--------|
| 10 | [Multiple iterations: start → continue → verify → complete](20260518-tutorial-implement-multiple-iterations.md) |
| 11 | [Verify, audit, test in development](20260518-tutorial-verify-audit-test-development.md) |

### E - Quality requests (tests as work items)

| Step | Guide |
|------|--------|
| 12 | [Request a new test](20260518-tutorial-request-new-test.md) |
| 13 | [Request tests for a feature / module](20260518-tutorial-request-test-feature-module.md) |

### F - Cross-cutting NFR

| Guide | Use when |
|-------|----------|
| [Boundary map how-to](20260518-guide-boundary-map-howto.md) | Coupling / import boundaries |
| [Observability and traceability](20260518-guide-observability-traceability-in-workflow.md) | Logs, traces, metrics, verify row |

---

## Principles

- **Template-first:** `{CONCEPTS_ROOT}`, `{ITERATION_CARRIER}`, `{MASTER_PLAN}`, … not hard-coded paths in normative prose.  
- **Evidence tags:** `measured` | `estimated` | `assumption` | `unknown` for numbers in plans.  
- **Feature-centric:** SPECs own behaviour + test plan; skills own orchestration; concepts own architecture NFR prompts.

**Naming:** **`YYYYMMDD-tutorial-<slug>.md`** for operator procedures; **`YYYYMMDD-guide-<slug>.md`** for reference or internal-style workflow docs. **[README.md](README.md)** (no dated prefix) holds the **canonical artifact matrix** so directory links stay stable.

---

## Skills index (execution layer)

Portable skills live under **`{SKILLS_ROOT}`** - see [`.ai/skills/README.md`](../../../skills/README.md). **Orientation (read-only):** `@process-router`. Guides explain **when** to invoke which skill; **`skill.md`** is still the source of truth for parse verbs and checklists.
