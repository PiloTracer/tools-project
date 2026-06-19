---
name: ui-visual-verify
description: >-
  Visual and design-token verification: milestone, uncommitted. Use before
  ui-component-build complete and before UI PR merge.
---

# ui-visual-verify

**Craft standard:** `standards/20260523-SURFACE-AND-CONTROL-CRAFT.md` §7

## Modes

| Mode | When |
|------|------|
| `milestone` | End of UI milestone S{N} |
| `uncommitted` | Dirty UI paths before commit |
| `status` | Read-only last report |

## Checks (milestone)

1. `REPLACE:UI_VISUAL_TEST` exit 0 (or documented baseline update with owner approval)
2. **Token contract (machine):** `bash .ai.ui/scripts/token-lint.sh --tokens REPLACE:UI_TOKENS_FILE REPLACE:UI_APP_ROOT` exits 0 — no raw hex/color literals in component source (DESIGN_TOKENS_STANDARD). This is the deterministic backstop: an agent that hardcoded a color fails here, not in a prose grade. One-off exceptions need a trailing `token-lint-ignore` with a reason.
3. Token file unchanged without accompanying visual diff review
4. Storybook/build for UI package passes
5. UIS registry: no `Applies=yes` + `pending`
6. **Craft / §13 compliance** (per active screen SPECs in milestone):

| Check | Fail when |
|-------|-----------|
| exampleIds | Missing in §13 when craft tier ≥ refined (no HANDOFF waiver) |
| extractedRules | §11 bullets not reflected in UI (spot-check) |
| Native controls | Browser-default range/select/checkbox on flows where §8 requires catalog primitive |
| Surfaces | Flat-only page when tier ≥ refined and SPEC requires `--surface-elevated` cards |
| BEFORE compare | `beforeScreenshot` in §13 but no visible improvement on cited rules (manual/vision) |

7. **UIS-07** run when craft tier ≥ refined (`@ui-concept-run - UIS-07`)

## Output

Verdict: **pass** | **pass with gaps** | **fail** — gaps need HANDOFF_UI waiver line.

Include section:

```markdown
### Craft compliance
- SPECs checked: …
- §13 exampleIds: ok | gaps
- Native control violations: none | …
- UIS-07: done | pending | N/A
```

**Does not** replace `@ui-accessibility-audit`.

**Encourage:** register BEFORE/AFTER in `inputs/design-references/` for regression context.
