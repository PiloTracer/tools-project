# Visual hierarchy — agent procedure (UIS-01)

## Inputs

- Screen SPEC §4 or screenshot / Storybook link
- List of user goals (primary vs secondary)

## Procedure

1. Identify **one** primary action per viewport.
2. List heading levels used; flag skipped levels or multiple h1-equivalents.
3. Check spacing scale: are related items grouped (proximity)?
4. Flag elements competing for attention (same size/weight/color).

## Output

```markdown
## UIS-01 Visual hierarchy
- Primary action: <element> — clear | weak | missing
- Scan path: <1-2 sentence expected F-pattern or Z-pattern>
- Issues: <bullets>
- Recommendation: ship | revise — …
evidence: measured | estimated | assumption | unknown
```
