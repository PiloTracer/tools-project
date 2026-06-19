# Screen SPEC Standard — template

> Binding shape for `.work.ui/screens/<slug>/YYYYMMDD-SCREEN-SPEC.md`. Replace `REPLACE:UI_` tokens.

**Skill:** `@ui-screen-spec create - <slug>`

---

## 1. Filename and lifecycle

- Path: `{SCREEN_SPEC_ROOT}/<slug>/YYYYMMDD-SCREEN-SPEC.md`
- Status: `Draft` → `Review` → `Approved` → `Implemented` (amendments: `YYYYMMDD-SCREEN-SPEC-amendment-NN.md`)
- Slug: kebab-case, matches route or product name (`checkout`, `settings-profile`)

## 2. Required sections

| § | Title | Content |
|---|-------|---------|
| 1 | Summary | One paragraph: user goal, entry points |
| 2 | Personas & jobs | Who, job-to-be-done |
| 3 | States | Loading, empty, error, success, partial, permission-denied |
| 4 | Layout & hierarchy | Regions, responsive breakpoints, UIS-01 reference |
| 5 | Content | Copy keys, labels, empty states (or i18n key ids) |
| 6 | Interactions | Clicks, keyboard, focus order, modals (UIS-05) |
| 7 | Data dependencies | APIs, feature SPECs in `.work/features/` (links only) |
| 8 | Tokens & components | Catalog primitives with **status** (`done` / `planned` / `native allowed` + waiver); link foundation doc 02 surface tokens |
| 9 | Accessibility | WCAG target level, focus trap rules, live regions |
| 10 | Analytics & observability | Events (no PII in payloads) |
| 11 | Acceptance criteria | Testable bullets; include **extractedRules** copied from cited examples |
| 12 | Concept / UIS registry | UIS-01…07 applies yes/no + reason |
| 13 | Visual references | **Required shape** — see §6 below |

## 3. §12 Concept registry (required)

Mirror Agent OS FEATURE_STANDARD §15 pattern:

| UIS id | Applies | Reason | Status |
|--------|---------|--------|--------|
| UIS-01 | yes/no | … | pending/done/N/A |

## 4. Approval gate

`@ui-screen-spec review` must pass before `@ui-component-build plan` references the screen.

**Review failures (craft):**

- §13 missing `exampleIds` when craft tier ≥ refined (foundation 01)
- §8 lists catalog primitive but status ≠ `done` and no waiver
- §8 allows native controls while §13 cites example requiring custom primitives (e.g. `mobile-controls/C1`) without `native allowed` waiver
- §11 missing acceptance bullets from manifest `extractedRules`

## 5. §13 Visual references (required shape)

```markdown
## 13. Visual references

| Field | Value |
|-------|-------|
| **exampleIds** | `mobile-controls/C1`, `dashboards/D2` |
| **manifestPaths** | `.ai.ui/examples/mobile-controls/manifest.md` |
| **craftTier** | utilitarian \| refined \| premium (from foundation 01) |
| **beforeScreenshot** | `inputs/design-references/settings-before.png` (optional) |
| **extractedRules** | Bullets copied from manifest — also mirror in §11 |
| **regionMap** | §4 region → governing example id |

### extractedRules (binding)

- Card grid for control clusters; custom RangeSlider with readout
- …

### Figma / external (optional)

- URL (no embedded auth)
```

**N/A waiver:** If no examples apply, set `exampleIds: N/A` + reason in HANDOFF_UI.

## 6. Do not duplicate

- API request/response shapes → link domain SPEC
- Backend business rules → link domain SPEC or ADR
