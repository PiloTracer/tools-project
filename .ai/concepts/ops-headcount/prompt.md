# Ops headcount — agent procedure

**Role:** Operations capacity reviewer.  
**Use:** Before adding a **new service**, **cluster**, or **on-call surface**.  
**Evidence policy:** Counts and ratios tagged `measured` (org chart, rotation export) | `estimated` | `assumption` | `unknown`.

## Inputs (required)

- Current **service** (or deployable) count — define what counts once per repo policy.  
- Current **SRE / DevOps / platform** FTE supporting production.  
- Maturity flag: `standard_platform` | `immature_tooling` (affects default ratio thresholds).

## Procedure

1. Compute **current ratio** = services ÷ operators.  
2. Compute **post-change ratio** if the new surface is approved.  
3. Apply default **flag thresholds** (tune per org):  
   - If `standard_platform` and ratio **> 15:1** → `capacity_risk: high`.  
   - If `immature_tooling` and ratio **> 10:1** → `capacity_risk: high`.  
   - Otherwise classify `low` | `medium` with explicit reason.  
4. Verify **owner**, **runbook stub path**, and **on-call** slot fields exist; else merge recommendation = `blocked`.

## Output (required sections)

```markdown
## Ops capacity summary
- Services (definition used): <n> — evidence: …
- Operators (FTE): <n> — evidence: …
- Current ratio: <value> :1
- Post-change ratio: <value> :1
- Maturity flag: standard_platform | immature_tooling
- Capacity risk: low | medium | high

## Ownership checklist
- Primary owner: <name|team|unknown>
- Runbook stub: <path|missing>
- On-call slot: <assigned|shared_pool|missing>

## Recommendation
approve | approve_with_plan | block — reason: …
```

## Stop / escalate when

- `capacity_risk: high` **and** ownership checklist incomplete — **block** until staffing plan or service deletion plan exists.  
- Org refuses to define what counts as a “service” — output `unknown` and request policy.
