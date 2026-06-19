# REPLACE:SCREEN_NAME — Screen SPEC

**Status:** Draft  
**Slug:** example-slug  
**Path:** `.work.ui/screens/example-slug/YYYYMMDD-SCREEN-SPEC.md`

---

## 1. Summary

One paragraph: user goal, entry points.

## 2. Personas & jobs

| Persona | Job |
|---------|-----|
| REPLACE:PERSONA | REPLACE:JOB |

## 3. States

| State | Behaviour |
|-------|-----------|
| loading | |
| empty | |
| error | |
| success | |

## 4. Layout & hierarchy

Regions, breakpoints (UIS-01). Map regions to example ids in §13 `regionMap`.

| Region | Example id | Notes |
|--------|------------|-------|
| REPLACE:REGION | REPLACE:EXAMPLE_ID | |

## 5. Content

Copy or i18n keys.

## 6. Interactions

Focus order, modals (UIS-05).

## 7. Data dependencies

- Feature SPEC: `.work/features/REPLACE:FEATURE_SLUG/…` (link only)

## 8. Tokens & components

| Component | Catalog status | Native waiver |
|-----------|----------------|---------------|
| Button | done | — |
| RangeSlider | planned | no — required per §13 |

Use `--surface-*` tokens from foundation doc 02. Status must be **done** before screen build tasks unless waiver documented.

## 9. Accessibility

WCAG REPLACE:UI_WCAG_LEVEL targets for this screen.

## 10. Analytics

Event names (no PII).

## 11. Acceptance criteria

- [ ] … (include bullets from §13 extractedRules)

## 12. Concept / UIS registry

| UIS | Applies | Reason | Status |
|-----|---------|--------|--------|
| UIS-01 | yes | new layout | pending |
| UIS-06 | yes | agent build | pending |
| UIS-07 | yes | craft tier refined | pending |

## 13. Visual references

| Field | Value |
|-------|-------|
| **exampleIds** | `REPLACE:FOLDER/ID` |
| **manifestPaths** | `.ai.ui/examples/REPLACE:FOLDER/manifest.md` |
| **craftTier** | refined |
| **beforeScreenshot** | `inputs/design-references/REPLACE:before.png` (optional) |

### extractedRules (binding)

- REPLACE:RULE_FROM_MANIFEST_1
- REPLACE:RULE_FROM_MANIFEST_2

### regionMap

| §4 region | example id |
|-----------|------------|
| REPLACE:REGION | REPLACE:ID |

### Figma / external (optional)

- REPLACE:URL (no secrets)
