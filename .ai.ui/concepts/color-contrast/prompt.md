# Color & contrast — agent procedure (UIS-04)

## Inputs

- Semantic token pairs (text on surface, border on surface)
- Target WCAG level from accessibility standard

## Procedure

1. List new or changed color pairs.
2. For each pair: contrast ratio or `unknown` + tool to run.
3. Flag non-text UI (icons, borders) below 3:1.
4. Theme switch: verify pairs in light and dark.

## Output

```markdown
## UIS-04 Color & contrast
| Pair | Ratio | Pass AA |
|------|-------|---------|
| … | … | yes/no/unknown |
- Recommendation: ship | revise
evidence: …
```
