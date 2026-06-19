# Surface and control craft — agent procedure (UIS-07)

**Role:** Craft reviewer for **surfaces, controls, grouping, and clarity** — not color scheme or brand palette.

**In scope:** Cards, elevation, form controls, sliders, segmented selectors, section grouping, label/value pairing.

**Out of scope:** Brand color approval (UIS-04); generic AI slop only (UIS-06 covers overlap — run both on agent diffs).

## Inputs

- Screen SPEC §4, §8, §13 (exampleIds, extractedRules)
- Foundation doc 01 **craft tier**
- Diff summary or screenshot / Storybook link
- CATALOG.md primitive status

## Procedure

1. **Surface stack:** Are `--surface-base`, `--surface-elevated`, `--surface-inset` used appropriately for tier? Flag flat-only layouts when SPEC requires cards.
2. **Control anatomy:** For each control in diff — label visible, value readout, custom primitive vs native. Fail native range/select/checkbox on primary flows when §8 requires catalog.
3. **Grouping:** Section headers, fieldsets, card clusters match §13 extractedRules and example regionMap.
4. **Clarity:** One primary metric per card (dashboards); legends on multi-segment bars; spacing from token scale.
5. **Primitive reuse:** New one-off vs CATALOG — justify or refactor.
6. **§13 compliance:** Each cited example id — at least one extractedRule visible in UI.

## Output

```markdown
## UIS-07 Surface and control craft
- Craft tier: utilitarian | refined | premium
- SPEC §13 exampleIds: …
- Surface stack: ok | gaps — …
- Control anatomy: ok | native violations — …
- Grouping / clarity: ok | gaps — …
- §13 rules reflected: yes | partial | no
- Recommendation: ship | ship_with_notes | revise
evidence: …
```

**Pair with:** `@ui-concept-run - UIS-06` on agent-assisted diffs; `@ui-visual-verify milestone` consumes this output.
