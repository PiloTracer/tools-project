# AI visual quality — agent procedure (UIS-06)

**Role:** UI reviewer for **AI-assisted** front-end diffs.

**In scope:** Agent-generated components, pages, Tailwind/class strings, layout JSX.

**Out of scope:** Human-only UI when explicitly declared in the same message.

## Inputs

- Diff summary (files, approximate LOC)
- Link to screen SPEC or design tokens file
- Storybook or screenshot if available

## Procedure

1. **Token discipline:** count raw hex/px outside token file — target 0 in components.
2. **Generic AI chrome:** gradient heroes, purple shadows, redundant cards — flag.
3. **Spacing consistency:** compare to scale (4/8px or token steps); list outliers.
4. **Component reuse:** new one-off vs existing primitive — justify or refactor.
5. **a11y smoke:** focusable controls, labels on inputs in diff.
6. **Pair with MOD-06?** If diff also touches API/services → note "also run @concept-run - MOD-06".

## Output

```markdown
## UIS-06 AI visual quality
- AI-assisted: yes | no | unknown
- Token violations: <n> — examples
- Generic chrome risk: low | medium | high
- Spacing outliers: <list|none>
- Reuse: ok | new duplicates — …
- a11y smoke: ok | gaps
- Also MOD-06: required | no
- Recommendation: ship | ship_with_notes | revise
evidence: …
```
