# Network cost — latency budgets and synchronous chains

**Pack id:** MOD-02  
**Directory:** `network-cost/`  
**Source chain:** [Concepts pack](../README.md) (transcript of [this talk](https://youtu.be/6e9B7q3gvYY)).

## Why this matters for AI-assisted coding

Agents happily add **another HTTP/RPC client** because the diff is small. The system pays **tail latency** and **failure composition** (timeouts, retries, partial success). Making hop costs explicit prevents “death by a thousand micro-calls.”

## Signals (detect)

| Signal | Interpretation |
|--------|----------------|
| Simple read path crosses **many** synchronous services | Fixed **N × latency** tax on p99 |
| Teams “don’t know” per-hop latency | Observability or discipline gap |
| Latency attributed to “app code” without measuring **wire** segments | Misdiagnosis risk |

**Order-of-magnitude reminder:** In-process vs same-host vs cross-AZ costs differ by orders of magnitude. Treat transcript numbers as **starting hypotheses**; **measure** your paths.

## Rules / gates

1. For each new **sync** hop on a critical path, add an **expected latency range** and the **evidence** tag.  
2. Maintain a **request budget** (p50/p99 targets) for user-facing flows; network overhead must fit inside.  
3. Prefer **in-process** or **async** consolidation when no **independent scaling** or **ownership** reason exists for the hop (ties to MOD-01, MOD-05).

## Anti-patterns

- Chaining services “because clean architecture” with no **SLO** math.  
- Accepting dashboard averages that hide **multi-hop** tail behavior.

## Limits (what AI cannot verify alone)

- Live RTT without traces/metrics.  
- TLS/session reuse effects, connection pool health, regional routing.

## Related concepts

- [MOD-01 — Coupling audit](../coupling-audit/README.md)  
- [MOD-03 — Cost model](../cost-model/README.md)  
- [MOD-05 — Modularity vs distribution](../modularity-vs-distribution/README.md)

## Agent procedure

See [`prompt.md`](prompt.md).
