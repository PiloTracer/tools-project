# Motion design — agent procedure (UIS-03)

## Inputs

- Motion tokens (duration, easing) from design tokens file
- `prefers-reduced-motion` handling

## Procedure

1. List animations; classify: essential feedback vs decorative.
2. Verify reduced-motion path disables or replaces decorative motion.
3. Flag `transition: all` or >400ms blocking transitions on large surfaces.
4. Check focus not lost during route transitions.

## Output

```markdown
## UIS-03 Motion
- Animations: <list>
- reduced-motion: ok | missing
- Issues: …
- Recommendation: ship | revise
evidence: …
```
