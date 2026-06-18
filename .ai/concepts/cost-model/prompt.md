# Cost model — agent procedure

**Role:** FinOps-aware architecture reviewer.  
**Use:** Before approving a **new deployable**, **mesh**, major **observability** change, or **multi-region** expansion.  
**Evidence policy:** Currency amounts tagged `measured` (bill/quote) | `estimated` (calculator) | `assumption` | `unknown`.

## Inputs (required)

- Current monthly infra + observability **rough** totals (`unknown` triggers weak confidence banner).  
- Expected traffic / growth assumption for 12 months.  
- Region list and data residency constraints (`none` if N/A).

## Procedure

1. **Itemize** new recurring costs: compute (pods/VMs), storage, egress, DB, queue, **mesh control plane**, **APM/tracing/logs** (per GB/metric cardinality), on-call tooling.  
2. For each line, fill **low / high** monthly band and evidence tag.  
3. Compute **break-even narrative**: at what scale does **independent scaling** pay for **new overhead**? If unclear, mark `unknown` and require human FinOps input.  
4. Require **ADR stub fields**: decision, alternatives rejected, **\$** summary, rollback.

## Output (required sections)

```markdown
## Cost impact summary
| Line item | Low $/mo | High $/mo | Driver | Evidence |
|-----------|----------|-----------|--------|----------|
| … | … | … | QPS/retention/cardinality/… | measured|estimated|assumption|unknown |

- Total new estimate band: $… – $… / mo
- Break-even / scaling rationale: <text or unknown>

## ADR requirement
required | not_required — threshold reference: …

## Recommendation
approve | defer | reject — reason: …
```

## Stop / escalate when

- High-side estimate **doubles** current platform cost **and** evidence is mostly `assumption` — require **measured** pilot or calculator screenshot path before merge.  
- Proposal adds mesh **and** cannot show **CPU/mem** baseline for representative workload.
