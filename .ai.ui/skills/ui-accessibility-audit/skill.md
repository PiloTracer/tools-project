---
name: ui-accessibility-audit
description: >-
  WCAG-oriented audits per screen or milestone. Use screen - <slug> or milestone
  before ui-component-build complete.
---

# ui-accessibility-audit

**Standard:** `REPLACE:UI_ACCESSIBILITY_FILE` (ACCESSIBILITY_STANDARD template)

## Modes

| Mode | Action |
|------|--------|
| `screen - <slug>` | Audit against approved screen SPEC §9 |
| `milestone` | All screens in active NEXT_UI iteration |
| `status` | Last findings summary |

## Tooling

Run `REPLACE:UI_A11Y_TOOL` in container per `.cursorrules`.

## Verdict

- **critical** findings → fail (block complete)
- **serious** → pass with gaps only if HANDOFF_UI documents waiver + owner

Pair with UIS-04 when color tokens changed in same milestone.
