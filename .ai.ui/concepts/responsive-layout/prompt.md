# Responsive layout — agent procedure (UIS-02)

## Inputs

- Breakpoints from token file or SPEC
- Target viewports (min: mobile 320, tablet, desktop)

## Procedure

1. List layout regions and how they reflow per breakpoint.
2. Check overflow: horizontal scroll, clipped focus rings, sticky overlap.
3. Touch targets ≥ 44×44px where interactive (estimate if not measured).
4. Note content priority when stacked (order vs visual order).

## Output

```markdown
## UIS-02 Responsive layout
- Breakpoints covered: <list>
- Overflow risks: <list|none>
- Touch targets: ok | gaps — …
- Recommendation: ship | revise
evidence: …
```
