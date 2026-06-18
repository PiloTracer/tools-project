# Coupling audit — agent procedure

**Role:** Architecture / merge-risk reviewer (human or tool).  
**Use:** Before approving **service extraction**, **large refactors**, or **merge of AI-assisted multi-module diffs**.  
**Evidence policy:** Every numeric or ratio claim must be tagged `measured` | `estimated` | `assumption` | `unknown`.

## Inputs (required)

- Repository layout map (packages, contexts, or services).  
- The proposed change: diff summary or design note.  
- Test commands available to the author (or `unknown`).

## Procedure

1. **Enumerate boundaries crossed** — list distinct modules/packages/services touched.  
2. **List inter-module calls** introduced or modified (imports, RPC clients, shared DTOs, events).  
3. **Flag shared persistence** — tables, caches, queues touched by more than one owner.  
4. **Business-rule span** — if one invariant is edited, list all deployables that **must** roll together.  
5. **Coupling score** — assign `low` | `medium` | `high`:  
   - `high`: any mandatory multi-deploy train for a single rule change, or shared mutable state without a single writer.  
   - `medium`: clear interfaces but frequent coordinated releases.  
   - `low`: single-owner module; others consume stable APIs; tests isolate failures.  
6. **AI diff rule** — if author marks change as AI-assisted and **>1** hard boundary is crossed, set `human_arch_review: required`.

## Output (required sections)

Use this skeleton in Markdown:

```markdown
## Coupling audit summary
- Boundaries crossed: <n> — <names>
- New or tighter dependencies: <list or none>
- Shared persistence risks: <list or none>
- Coupling score: low | medium | high (evidence: assumption|measured|estimated)
- Human architectural review: required | optional — reason: …

## Recommendation
fix_coupling_first | proceed_split | proceed_with_guards

## Guardrails if merging now
- Tests: …
- Rollout: …
```

## Stop / escalate when

- Coupling score is `high` **and** the change is AI-assisted **and** no isolated test plan exists — **do not approve** extraction; recommend merge only with explicit human sign-off.  
- Missing ownership map — output `unknown` for org coupling and request product/engineering input.
