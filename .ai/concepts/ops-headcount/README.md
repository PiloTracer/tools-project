# Ops headcount — ownership, on-call, and service load

**Pack id:** MOD-04  
**Directory:** `ops-headcount/`  
**Source chain:** [Concepts pack](../README.md) (transcript of [this talk](https://youtu.be/6e9B7q3gvYY)).

## Why this matters for AI-assisted coding

Agents add **repos, pipelines, and deployables** quickly. Each new surface needs **ownership**, **runbooks**, and **on-call** capacity. If the ratio of services to operators exceeds team tolerance, **incidents queue**, **MTTR rises**, and **AI velocity becomes liability**.

## Signals (detect)

| Signal | Interpretation |
|--------|----------------|
| Service-to-operator ratio exceeds the team’s own threshold | Capacity risk |
| No named **owner** + **runbook stub** per service | Merge hygiene gap |
| Frequent **head-of-line** incidents (one bad deploy blocks many teams) | Platform or coupling stress (ties MOD-01) |

**Heuristic ratios** in the source talk (e.g. mature 10–15 services per SRE) are **rules of thumb** — replace with **your** incident load and automation level.

## Rules / gates

1. Each new deployable: **primary owner**, **secondary**, **runbook link or stub path**, **on-call rotation** slot or explicit **shared platform** exemption.  
2. Define a team-specific **max services per operator**; block when exceeded unless capacity plan updated.  
3. **Two-pizza team (~8–10)** per domain: if more people are needed to “understand” the domain, split the **domain model** before splitting **infra** (ties MOD-01, MOD-05).

## Anti-patterns

- “Everyone owns everything” on-call with **unbounded** stack growth.  
- Microservice sprawl **without** platform engineering maturity.

## Limits (what AI cannot verify alone)

- Real pager noise, vacation coverage, vendor SLOs for managed services.  
- Political willingness to delete services.

## Related concepts

- [MOD-03 — Cost model](../cost-model/README.md)  
- [MOD-01 — Coupling audit](../coupling-audit/README.md)  
- [MOD-05 — Modularity vs distribution](../modularity-vs-distribution/README.md)

## Agent procedure

See [`prompt.md`](prompt.md).
