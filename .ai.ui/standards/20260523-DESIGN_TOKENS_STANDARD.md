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
- **Chart (required for analytical dashboards):** categorical palette, semantic palette, sequential/diverging, axis, tooltip — see §5

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

## 5. Chart tokens (required when archetype = analytical dashboard)

Define a separate chart palette in the token file. Charts must **not** consume general surface/text tokens for data encoding.

| Token group | Examples | Purpose |
|-------------|----------|---------|
| **Categorical palette** | `--chart-cat-0` through `--chart-cat-N` | Distinguish data series (N = max series per chart; overflow uses repeating or `--chart-cat-other`) |
| **Semantic palette** | `--chart-pos`, `--chart-neg`, `--chart-neutral`, `--chart-warning`, `--chart-info` | Up/down/flat indicators, delta badges, gauge zones |
| **Axis & grid** | `--chart-axis-line`, `--chart-grid-line`, `--chart-label-fill` | Non-data ink — subtle, no visual competition with data |
| **Tooltip & interaction** | `--chart-tooltip-bg`, `--chart-tooltip-border`, `--chart-crosshair-line`, `--chart-highlight-fill` | Hover/selection feedback surfaces |
| **Sequential / diverging** | `--chart-seq-0` through `--chart-seq-5`, `--chart-div-neg-3` through `--chart-div-pos-3` | Heatmaps, choropleths, diverging bars |

**Rules:**
- Categorical palette must be colorblind-safe (check with UIS-09 / UIS-04)
- Sequential scales: 5–9 stops from light to saturated; luminance contrast verified
- Chart tokens are **separate** from UI surface tokens — a chart's `--chart-cat-0` is not `--color-primary`
- Dark theme chart tokens must be defined independently (not inverted)

## 6. Brand inputs

Brand colors from `.ai.ui/inputs/brand/` map **into** semantic tokens — components never import brand files directly.
