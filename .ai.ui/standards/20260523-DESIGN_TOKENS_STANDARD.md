# Design Tokens Standard — template

> Single source of visual truth at `REPLACE:UI_TOKENS_FILE`.

---

## 1. Token categories (required)

- **Color:** semantic (`--color-text-primary`, `--color-surface-elevated`) not palette-only names in components
- **Surface (required when craft tier ≥ refined):** `--surface-base`, `--surface-elevated`, `--surface-inset`, `--surface-overlay` — see SURFACE-AND-CONTROL-CRAFT
- **Spacing:** scale `0–n` or `xs–xl` — consistent step
- **Typography:** font family, size, weight, line-height as named sets (`text-body`, `text-heading-lg`)
- **Radius, shadow, border** — semantic where possible
- **Motion:** duration + easing tokens (UIS-03)
- **Z-index:** named layers (`dropdown`, `modal`, `toast`)

## 2. Format

Document one canonical format for the repo:

- CSS custom properties on `:root` / `[data-theme="dark"]`
- or TypeScript `theme` object consumed by `REPLACE:UI_STYLE_SYSTEM`
- or Style Dictionary export — path documented in HANDOFF_UI

### Theme variant completeness (required when dark or scoped themes exist)

Every semantic token that components consume in the default theme **must** be overridden in each alternate theme block — not only canvas, surface, and `--color-text-primary`.

Minimum surface/text pairs to audit (see SURFACE-AND-CONTROL-CRAFT):

| Pair | Typical failure |
|------|-----------------|
| `--color-bg-inset` / `--surface-inset` + `--color-text-primary` | Light inset bg with light text in dark mode |
| `--color-bg-elevated` + `--color-text-secondary` | Muted labels on wrong elevation |
| Inset elevation (`--elevation-inset`) | Flat or light-scheme shadow on dark wells |

Foundation doc 02 must list **light and dark values** for every inset/elevated token used by inputs, previews, and segmented controls. Run UIS-04 contrast checks on inset pairs in **each** theme before ship.

## 3. Change process

1. Update token source
2. Run visual regression (`@ui-visual-verify`)
3. Note in screen SPECs if contrast pairs change (UIS-04)
4. ADR if breaking rename

## 4. Forbidden in components

- Raw `#`, `rgb(`, `hsl(` except in token definition file
- Arbitrary `z-index: 9999`
- `transition: all`

## 5. Brand inputs

Brand colors from `.ai.ui/inputs/brand/` map **into** semantic tokens — components never import brand files directly.
