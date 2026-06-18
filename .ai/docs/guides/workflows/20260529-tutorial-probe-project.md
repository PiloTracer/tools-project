# Tutorial - probe a project until the agent understands it

**Audience:** operator. **Goal:** use `probe` so the agent *interrogates* your project (or your draft plan) and fills knowledge gaps before it certifies readiness - instead of guessing.

**Skills:** [`plan-foundation`](../../../skills/plan-foundation/skill.md) · [`plan-master`](../../../skills/plan-master/skill.md) · engine: [`probe-protocol.md`](../../../skills/probe-protocol.md).

---

## When to use it

| You feel… | Run |
|-----------|-----|
| "The agent doesn't really understand the project" / scope, NFRs, constraints are vague | `@plan-foundation probe` |
| "The draft plan has hand-wavy NFRs, unmapped features, or ownerless risks" | `@plan-master probe` → `@plan-master integrity` |
| "Just tell me where the gaps are, don't ask yet" | `@plan-foundation probe - status` |

Probe is **read+write to planning artifacts only** - it never writes application code.

---

## What one iteration does

Probe scores your project across fixed **coverage dimensions** (foundation D1–D10; master M-D1…M-D7), then runs one loop:

```text
ASSESS → PRIORITIZE → ASK (≤5 targeted questions) → RECORD → RE-SCORE → EXIT?
```

- **Records** answers into their canonical home: foundation doc 01 / the plan body, ADR **Proposed** stubs, and the `ASSUMPTIONS` / `UNKNOWNS` / `RISK_REGISTRY` registries (never a forked list).
- **Persists** state in a ledger (`{PLANS_ROOT}/foundation/PROBE_LEDGER.md` or `{PLANS_ROOT}/full/PROBE_LEDGER.md`) so it is resumable across sessions.
- **Defers** anything you skip into `UNKNOWNS` (owner + what it blocks) - stopping early is always safe, never a silent gap.

A dimension reaches **confirmed/high** only with a cited source or your explicit answer - an inference is **partial/med** at best.

---

## Step by step (foundation)

1. **Start interrogating:**

```text
@plan-foundation probe
```

The agent reports current **Coverage %**, asks up to 5 questions targeting the lowest-confidence, highest-impact gaps, records your answers, and updates the ledger.

2. **Go deeper** - re-invoke to run another iteration, or let it loop to the target:

```text
@plan-foundation probe - until ready
```

It stops at Coverage ≥ 85% with no gate-blocking (★) dimension still `unknown`, or at the first blocker only you can resolve.

3. **Check honesty at any time** (also runs in CI and `@session-control close`):

```text
bash .ai/scripts/readiness-verify.sh
```

Fails if a `confirmed/high` dimension cites no evidence, if the header Coverage % is inflated vs the table, or if it claims "ready" while a ★ dimension is still `unknown`.

4. **When coverage is reached** - the gaps are filled, so certify:

```text
@plan-foundation certify plan-master-ready
```

---

## Step by step (master plan)

Probe here is the **interactive front-end to `integrity`**: it asks you to resolve gaps an automated sweep can flag but not answer (quantify a vague NFR, map an orphan FR, assign a risk owner).

```text
@plan-master probe            # fill plan-completeness gaps (needs a Draft plan)
@plan-master integrity        # automated contradiction/fitness sweep
@plan-master status           # scores implementation-ready
```

Probe never sets the plan **Approved** - that stays with `integrity` + the approval gate.

---

## How it fits the pipeline

```text
greenfield → probe (fill gaps) → certify plan-master-ready
                                      → plan-master greenfield → probe → integrity → status (implementation-ready)
```

See [`SKILL_DEPENDENCIES.md`](../../../skills/SKILL_DEPENDENCIES.md) for the gate graph and the coverage maps in each skill's `reference.md`.
