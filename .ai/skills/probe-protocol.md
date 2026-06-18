# Probe protocol (shared engine)

**Single source of truth** for the adaptive, gap-driven interrogation loop used by `probe` modes. `plan-foundation` and `plan-master` **reference** this file; they do **not** restate the loop. Each caller supplies a **coverage profile** (dimensions + exit gate + ledger path); this file owns the engine.

**Purpose:** Guarantee a skill has *enough information* before it certifies a readiness state. Instead of a fixed questionnaire, `probe` scores knowledge across fixed dimensions, asks targeted questions only for the gaps, records answers into the canonical registries, and loops until a confidence target is met or the user stops.

**Tool-agnostic** (Cursor, Claude Code, opencode, Codex). **Read+write planning artifacts only** - never application code, migrations, or docker.

---

## What probe is / is not

| Probe **is** | Probe **is not** |
|--------------|------------------|
| An adaptive clarification loop with a confidence score | A fixed questionnaire (that is greenfield's `INTERACTION` blocks) |
| A driver that *feeds* `ASSUMPTIONS` / `RISK_REGISTRY` / `UNKNOWNS` and doc 01 / plan body | A new registry (link, never fork - per `.cursorrules`) |
| The interactive front-end that *fills gaps* | The automated contradiction sweep (that is `plan-master integrity`) |
| Bounded: ≤5 questions per batch, every gap deferrable | An infinite interrogation; never blocks the user from stopping |

---

## Caller contract (coverage profile)

A consuming skill invokes probe with three parameters, defined in its own `reference.md`:

| Parameter | Meaning | Example |
|-----------|---------|---------|
| **Coverage map** | Fixed list of knowledge dimensions `D1…Dn`, each with a one-line "what good looks like" | `plan-foundation` § Foundation coverage map |
| **Exit gate** | The readiness criteria each dimension must satisfy to stop | S4 plan-master-ready · implementation-ready |
| **Ledger path** | Where the persisted probe state lives | `{PLANS_ROOT}/foundation/PROBE_LEDGER.md` |

Probe is **generic over the coverage map**: the engine below does not care what the dimensions are.

---

## Dimension status and confidence

Each dimension carries a **status** and a **confidence band**, set **only** from evidence or an explicit user answer (per `.cursorrules` Core Principle 5):

| Status | Confidence | Set when |
|--------|-----------|----------|
| **confirmed** | high | Cited file/ADR/answer that fully satisfies the dimension's "what good looks like" |
| **partial** | med | Some evidence or an inference; gaps remain |
| **unknown** | low | No evidence; absent or only assumed |

Never mark **confirmed/high** without a cite or a same-session user answer. An inference is **partial/med** at best.

---

## Coverage Score

```text
Coverage = ( Σ weight(Di) × confidence(Di) ) / Σ weight(Di)

confidence(Di):  high = 1.0   med = 0.5   low = 0.0
weight(Di):      gate-blocking dimension = 2   else = 1
```

Report as a percentage. **Default target = 85%** with **no gate-blocking dimension below `partial`**. Callers may override the target in their coverage profile.

---

## The loop

One pass = **one probe iteration**. Each iteration:

```text
ASSESS      Read existing artifacts + the three registries + the ledger.
            Score every Di (status, confidence, evidence cite).

PRIORITIZE  Rank gaps by:  gate-blocking? × risk impact × (1 − confidence)
            Take the top dimensions only.

ASK         Emit ONE batch of ≤5 targeted questions generated from the top
            gaps (AskQuestion in Cursor, or INTERACTION blocks in markdown).
            Each question states which Di it resolves and why it matters.
            Offer "skip / defer" on every question.

RECORD      Write answers to their home:
              product intent / scope        → foundation doc 01 (or plan body)
              a chosen option / trade-off    → ADR stub (Proposed)
              a belief taken as true         → ASSUMPTIONS.md  (labeled)
              an open question / blocker      → UNKNOWNS.md  (owner + blocks)
              a newly surfaced risk           → RISK_REGISTRY.md (mitigation)
            Update the ledger row for each Di touched.

RE-SCORE    Recompute Coverage Score and per-dimension status.

EXIT?       Stop when ANY of:
              • Coverage ≥ target AND no gate-blocking Di below partial
              • No high-priority gaps remain (all open items deferred)
              • User says stop / defer / enough
            Else → next iteration.
```

Deferred questions become **UNKNOWNS** entries (owner + what they block), so stopping early is always **safe and explicit** - never a silent gap.

---

## The ledger artifact

`probe` persists state so it is **resumable across sessions** and **auditable**. Caller supplies the path. Shape:

```markdown
# <Foundation|Plan> probe ledger
**Updated:** YYYY-MM-DD · **Iterations:** N · **Coverage:** NN% (target 85%)

| Dim | Topic | Status | Conf | Evidence / source | Iter |
|-----|-------|--------|------|-------------------|------|
| D1  | …     | confirmed | high | doc01 §… | 1 |
| D5  | …     | partial   | med  | answered iter-3; value TBD → U7 | 3 |

## Open probes (carried to next iteration)
- D5: <specific question> → blocks <gate criterion>

## Deferred (→ UNKNOWNS)
- U9: <question> · owner=<who> · blocks=<ADR/gate>
```

A dimension reaching **confirmed/high** must cite the evidence that justifies it in the ledger row.

---

## Output report (every probe run)

```markdown
## <skill> probe - iteration N

**Coverage:** NN% (target 85%) · **Δ from last:** +M%
**Gate-blocking gaps:** <count>

### Asked this iteration
- D5 NFRs: <question> → answer recorded in <path>

### Recorded
| Where | ID | Entry |
|-------|----|-------|
| ASSUMPTIONS | A4 | … (Inference) |
| UNKNOWNS | U9 | … (blocks ADR-hosting) |

### Ledger
- Updated <ledger path> · dimensions touched: D5, D8

### Next
- <continue (run probe again) | gate reachable: run @<skill> certify/status | owner blockers: U9>
```

---

## Ease-of-use rules

- **Batch small:** ≤5 questions per iteration; group by theme; never wall-of-questions.
- **Pre-fill defaults:** when a sensible default exists (stack, locale), offer it as the first option.
- **One command:** `@<skill> probe` runs a full iteration and stops; the user re-invokes to go deeper. `@<skill> probe - until ready` may loop autonomously, still ≤5 questions per batch, stopping at target or first unanswerable blocker.
- **Always resumable:** state lives in the ledger + registries, never only in chat.
- **Read-only twin:** `@<skill> probe - status` reports Coverage and gaps **without asking** anything.

---

## Verification (machine-checkable)

The ledger is **auditable**, not just asserted. Run the honesty linter against any project:

```bash
bash .ai/scripts/readiness-verify.sh                 # scan .work/ for PROBE_LEDGER.md
bash .ai/scripts/readiness-verify.sh path/to/PROBE_LEDGER.md
```

It **fails** (exit 1) when:

1. A dimension is **confirmed/high** but cites no evidence (empty / `—` / `TBD`) - enforces `.cursorrules` Core Principle 5.
2. The header **Coverage %** disagrees with the value recomputed from the table (tolerance 2 pts) - no inflated scores.
3. The header claims **Coverage ≥ target** while a gate-blocking (★) dimension is still **unknown** - no "ready" with a known blocking gap.

With no ledger present it exits 0 (probe is optional). Suitable for CI or a `@session-control close` pre-check.

---

## Anti-patterns

- Marking a dimension **confirmed** from an inference (must be cite or user answer).
- Forking a probe-private assumption/risk/unknown list instead of writing the canonical registries.
- Asking >5 questions in one batch, or refusing to let the user stop/defer.
- Treating probe as the integrity check - probe **fills** gaps; `integrity` **detects contradictions**. Run probe first, then integrity.
- Writing application code or ADR **Decided** status from a probe answer (ADR stubs are **Proposed** until the owner decides).
- Letting Coverage reach target while a gate-blocking dimension is still **unknown** (weighting prevents this; do not bypass it).
