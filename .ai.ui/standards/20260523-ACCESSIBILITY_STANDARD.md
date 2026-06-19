# Accessibility Standard — template

> WCAG-oriented bar for all UI shipped through UI Design OS.

**Target level:** `REPLACE:UI_WCAG_LEVEL` (default **AA**)

---

## 1. Baseline requirements

- Perceivable: text contrast ≥ 4.5:1 (normal), 3:1 (large); non-text UI components 3:1
- Operable: full keyboard access; no keyboard traps without escape; skip link on app shell
- Understandable: visible labels; errors associated with fields
- Robust: valid roles; name/role/value for custom widgets

## 2. Focus

- Visible focus ring using token `--focus-ring` (not `outline: none` without replacement)
- Focus order matches visual order unless SPEC documents intentional override
- Modals: focus trap + restore on close

## 3. Motion

- Respect `prefers-reduced-motion` — disable non-essential animation (UIS-03)

## 4. Forms

- `label` associated with control; `aria-describedby` for hints/errors
- Required fields marked in copy and `aria-required` where applicable

## 5. Verification

- `@ui-accessibility-audit` uses `REPLACE:UI_A11Y_TOOL` (axe, Lighthouse CI, etc.)
- Critical violations block milestone complete; serious need waiver in HANDOFF_UI

## 6. Testing data

- No real user PII in Storybook or test fixtures
