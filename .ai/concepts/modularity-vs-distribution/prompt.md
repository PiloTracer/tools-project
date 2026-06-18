# Modularity vs distribution — agent procedure

**Role:** Architecture decision reviewer.  
**Use:** When a proposal adds **a new deployable**, **splits a monolith**, or **moves code across network boundaries**.  
**Evidence policy:** Each claimed driver tagged `measured` | `estimated` | `assumption` | `unknown`.

## Inputs (required)

- Current architecture sketch (monolith / services / hybrid).  
- Proposal narrative (why split / why new service).  
- Traffic / scaling notes (`unknown` allowed with explicit risk flag).

## Procedure

1. Require explicit answers (one paragraph each minimum):  
   - **Scaling driver:** what component needs **different** scale shape than the rest?  
   - **Ownership driver:** what **deploy-time** autonomy is impossible inside current modular boundaries?  
2. Capture **cost** narrative — point to MOD-03 template or inline **\$** bands with evidence tags.  
3. Capture **network** narrative — point to MOD-02 hop table for critical paths.  
4. **Rollback / strangler:** describe how to **route back** or **toggle off** the extraction.

## Output (required sections)

```markdown
## Extraction / distribution review
- Scaling driver: <text> — evidence: …
- Ownership driver: <text> — evidence: …
- Monthly cost delta (band): $… – $… — evidence tags: …
- Critical path latency impact: <summary> — see MOD-02 table: <link|inline>

## Decision gate
- Q1 scaling concrete: yes | no
- Q2 ownership concrete: yes | no

## Recommendation
reject | defer | approve — reason: …

## Rollback / strangler plan
<text or missing → block>
```

## Stop / escalate when

- **Both** Q1 and Q2 are **no** or rely purely on `assumption` without measurement plan — default **reject** unless human CTO/architecture forum overrides with logged rationale.  
- No rollback path — **defer** until strangler or feature-flag path exists.
