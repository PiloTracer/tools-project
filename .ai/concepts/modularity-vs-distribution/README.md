# Modularity vs distribution — default shapes and extraction gates

**Pack id:** MOD-05  
**Directory:** `modularity-vs-distribution/`  
**Source chain:** [Concepts pack](../README.md) (transcript of [this talk](https://youtu.be/6e9B7q3gvYY)).

## Why this matters for AI-assisted coding

Tools generate **files and APIs** quickly; they do not automatically generate **clear module contracts**. **Modularity** (hard internal boundaries, tests that enforce them) is what makes AI output **reviewable** and **reversible**. **Distribution** (separate processes/network) is an **optional** scaling and ownership tool — not a maturity badge.

## Signals (detect)

| Signal | Interpretation |
|--------|----------------|
| DORA-style delivery metrics good/bad **correlate with coupling**, not “microservice yes/no” | Align investments to **boundary quality** |
| Teams reorganize code repeatedly **without** org/ownership change | Architecture may **snap back** (Conway) |
| Extraction proposal cites **blog** / **fashion** not **measurable** scaling or ownership pain | Likely premature |

## Rules / gates

1. **Default:** modular monolith — one deployable, **enforced** internal APIs, **logical** schema separation where applicable.  
2. **Extract** only with **named** reason: independent **scaling**, **team autonomy** at deploy boundary, **polyglot** / **regulatory** isolation, or **hard SLA** isolation — each with **evidence**.  
3. **Tooling:** prefer **automated** boundary checks (language-appropriate: package rules, ArchUnit-style, custom lint) over human-only review.  
4. **Legacy:** prefer **Strangler Fig** / incremental routing over big-bang rewrites.

## Anti-patterns

- Microservices to emulate “big tech” without **organizational** or **load** driver.  
- “Clean architecture” folders without **compile-time** / **test-time** enforcement.

## Limits (what AI cannot verify alone)

- Whether the org can **actually** own end-to-end domains.  
- Real traffic growth forecasts.

## Related concepts

- [MOD-01 — Coupling audit](../coupling-audit/README.md)  
- [MOD-02 — Network cost](../network-cost/README.md)  
- [MOD-04 — Ops headcount](../ops-headcount/README.md)  
- [MOD-06 — AI amplification](../ai-amplification/README.md)

## Agent procedure

See [`prompt.md`](prompt.md).
