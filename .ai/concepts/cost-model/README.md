# Cost model — architecture as a line item

**Pack id:** MOD-03  
**Directory:** `cost-model/`  
**Source chain:** [Concepts pack](../README.md) (transcript of [this talk](https://youtu.be/6e9B7q3gvYY)).

## Why this matters for AI-assisted coding

Models rarely see your **invoice**. They will propose **new services, meshes, and observability stacks** that are “best practice.” A cost model turns proposals into **comparable options** and keeps FinOps-compatible language in ADRs.

## Signals (detect)

| Signal | Interpretation |
|--------|----------------|
| New deployable with **no** monthly cost estimate | Financial blind spot |
| Mesh/sidecar added “for security” without **CPU/mem** headroom math | Risk of **fixed overhead** dominating small workloads |
| Observability priced per **service** or per **span volume** without caps | Runaway opex |

**Epistemic note:** Figures in the source talk (e.g. “~25% more compute,” “sidecars up to 90%,” dollar ranges for APM) are **anecdotal or third-party**. Use them as **questions to model**, not facts, until tied to **your** vendor quotes and usage.

## Rules / gates

1. For any **new billable unit** (service, cluster, mesh, log index), produce **monthly estimate bands** (low/high).  
2. Tie spend to **drivers**: QPS, payload size, retention, cardinality, regions.  
3. Add an **ADR** when spend crosses a team-defined **threshold** - include **\$** and **rollback** plan.  
4. Compare **N+1** architecture vs **consolidation** scenario at same traffic **at least** qualitatively.

## Anti-patterns

- “We’ll optimize cost later” for **structural** overhead (mesh, multi-cluster).  
- Cost review only **after** quarter close.

## Limits (what AI cannot verify alone)

- Contracted cloud discounts, committed use, enterprise support bundles.  
- Real trace/log cardinality explosion without production traffic.

## Related concepts

- [MOD-04 — Ops headcount](../ops-headcount/README.md)  
- [MOD-02 — Network cost](../network-cost/README.md)  
- [MOD-05 — Modularity vs distribution](../modularity-vs-distribution/README.md)

## Agent procedure

See [`prompt.md`](prompt.md).
