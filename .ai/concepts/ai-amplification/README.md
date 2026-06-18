# AI amplification — coupling vs safe AI-generated velocity

**Pack id:** MOD-06  
**Directory:** `ai-amplification/`  
**Source chain:** [Concepts pack](../README.md) (transcript of [this talk](https://youtu.be/6e9B7q3gvYY)).

## Why this matters for AI-assisted coding

Under tight coupling, models **increase output volume** faster than reviewers can validate invariants — **risk rises superlinearly**. Under **strong module contracts** and **fast isolated tests**, AI becomes a **bounded** accelerator: wrong changes fail **locally**, fixes are **small**.

## Signals (detect)

| Signal | Interpretation |
|--------|----------------|
| PR volume ↑ sharply; defect rate / change-fail rate **flat or worse** | Amplifier on unstable base |
| Most AI diffs touch **many** modules | Review surface too large — see MOD-01 |
| Few **module-scoped** tests; heavy reliance on **e2e only** | Slow feedback → risky AI merge |

**Epistemic note:** DORA / “2025 research” figures in the talk are **not verified** in this pack. Use your delivery metrics (lead time, CFR, restore time) instead of transcript percentages when deciding.

## Rules / gates

1. **Before** expanding AI merge volume: enforce **module isolation** (MOD-01) and **automated boundary checks** (MOD-05).  
2. Cursor/agent sessions are **AI-assisted by default** — MOD-06 output must declare **blast radius** and **test isolation** path (PR template or iteration registry).  
3. **>1** hard boundary crossed → **architectural review** or stricter CI (policy choice).

## Anti-patterns

- “AI wrote it” as excuse to skip **design** on cross-cutting changes.  
- Raising generation quotas without **raising** test/review capacity.

## Limits (what AI cannot verify alone)

- Team skill, review thoroughness, governance.  
- True defect rate without issue tracker discipline.

## Related concepts

- [MOD-01 — Coupling audit](../coupling-audit/README.md)  
- [MOD-05 — Modularity vs distribution](../modularity-vs-distribution/README.md)  
- [MOD-02 — Network cost](../network-cost/README.md)

## Agent procedure

See [`prompt.md`](prompt.md).
