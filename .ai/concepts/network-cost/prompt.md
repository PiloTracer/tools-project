# Network cost — agent procedure

**Role:** Performance / SLO reviewer.  
**Use:** When a diff adds **RPC/HTTP**, **service clients**, **gateways**, or lengthens a **sync chain**.  
**Evidence policy:** Latency numbers must be tagged `measured` (trace/metric) | `estimated` (model) | `assumption` | `unknown`.

## Inputs (required)

- Critical path description (entrypoint → response).  
- List of new or changed network calls (callee, sync/async).  
- Existing SLO / latency budget if any (`unknown` allowed once).

## Procedure

1. For each hop, assign a **latency class** and default **estimated** range (edit defaults to match your platform if known):  
   - `in_process` — ~0–0.05 ms (still not free; context switches exist).  
   - `loopback_http` — often ~0.5–3 ms **if** measured locally; else `unknown`.  
   - `same_region` — often ~1–10 ms per hop **order of magnitude**; verify.  
   - `cross_az` / `cross_region` — add **10–50+** ms class unless measured otherwise.  
2. **Sum** estimated overhead on the **critical path** (sync only).  
3. Compare to budget: default **flag** if **sync network-only** sum **> 200 ms** *unless* evidence is `measured` and within SLO. *(Threshold is a tunable policy constant.)*  
4. If hop exists **without** independent scaling or ownership rationale, suggest **inlining**, **library extraction**, or **async handoff** — cite MOD-01/MOD-05 in narrative.

## Output (required sections)

```markdown
## Network impact summary
| Hop | Type | Est. added ms | Evidence tag | Notes |
|-----|------|---------------|----------------|-------|
| … | … | … | measured|estimated|assumption|unknown | … |

- Critical path sync network sum (estimated): <ms>
- SLO breach risk: low | medium | high — reason: …

## Recommendation
accept | revise | measure_first

## If measure_first
- Add spans/metrics at: …
- Re-run this checklist with measured row.
```

## Stop / escalate when

- Critical path adds **>3** new sync hops and evidence is mostly `assumption` — require **tracing** before merge to default branch.  
- Cross-region sync on user-facing path without documented product requirement.
