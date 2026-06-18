# Coupling audit — before splits and for AI blast radius

**Pack id:** MOD-01  
**Directory:** `coupling-audit/`  
**Source chain:** [Concepts pack](../README.md) (transcript of [this talk](https://youtu.be/6e9B7q3gvYY)).

## Why this matters for AI-assisted coding

Large language models produce **diffs faster** than humans can reason about cross-module effects. If the codebase is a **distributed monolith** (physically separate, logically chained), each “small” change can still force **multi-package releases** and **flaky integration** tests. Coupling audits turn implicit risk into a **checklist** agents and humans can run before merging or before carving new deployables.

## Signals (detect)

| Signal | Interpretation |
|--------|----------------|
| One business rule change touches **3+** deployables or release trains | Logical coupling likely dominates split boundaries |
| Standard feature needs **standing cross-team coordination** | Ownership / boundary mismatch (see also MOD-05) |
| Shared **mutable** state or tables across “services” | Not independent domains |
| Frequent “we must deploy A+B+C together” | Split did not decouple |

## Rules / gates

1. **Map calls and data** across the proposed boundary: synchronous calls, events, shared DB schemas, shared libraries.  
2. If **module A cannot ship** without **module B** deploying, they are not independent — fix coupling **first**, split second.  
3. Prefer splits aligned to **business capability ownership**, not folder/layer accidents (controllers vs repositories).  
4. For **AI-generated** changes: treat any diff touching **>1** hard boundary as higher risk until proven isolated by tests (see `prompt.md`).

## Anti-patterns

- Splitting by technical layer only.  
- Declaring “microservices done” while business invariants still span services.  
- Using AI to **speed up** the same cross-cutting edits without shrinking coupling first (see MOD-06).

## Limits (what AI cannot verify alone)

- **Organizational** truth (who really owns what, political coordination cost).  
- Whether a “shared” schema is **accidental** or a **deliberate** bounded context.  
- Production incident history without logs/tickets/metrics.

## Related concepts

- [MOD-02 — Network cost](../network-cost/README.md) — what you buy when coupling spans the wire.  
- [MOD-05 — Modularity vs distribution](../modularity-vs-distribution/README.md) — default shapes.  
- [MOD-06 — AI amplification](../ai-amplification/README.md) — why coupling burns review bandwidth.

## Agent procedure

See [`prompt.md`](prompt.md).
