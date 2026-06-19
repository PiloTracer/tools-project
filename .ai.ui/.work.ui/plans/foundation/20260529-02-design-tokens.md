# Demo SaaS dashboard — Design tokens

**Doc:** UI foundation **02** · **Created:** 2026-05-29 · **Status:** worked example (demo)

## Canonical token file (code)

**Path:** [`../../design-system/tokens.css`](../../design-system/tokens.css) (`.work.ui/design-system/tokens.css`)

> In a real adopter this lives at the application source path (`REPLACE:UI_TOKENS_FILE`, e.g. `src/styles/tokens.css`). For the demo it ships under `.work.ui/design-system/` so the example is self-contained. Linked in `HANDOFF_UI` § Repository UI state.

## Semantic token map (summary)

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--color-text-primary` | `#1a1d21` | `#e7eaee` | body text |
| `--color-text-secondary` | `#5b6470` | `#9aa4b1` | muted labels |
| `--surface-base` | `#f6f7f9` | `#0f1216` | page background |
| `--surface-elevated` | `#ffffff` | `#171b21` | cards, panels |
| `--surface-inset` | `#eceef1` | `#0a0c10` | wells, input backgrounds |
| `--surface-overlay` | `#ffffffe6` | `#11141ae6` | sheets, modals |
| `--elevation-1` | light shadow | deep shadow | card elevation |
| `--elevation-inset` | inset light | inset deep | input/preview wells |

## Surface & control tokens (craft tier ≥ refined)

Craft tier is **refined**, so `--surface-*` and `--elevation-*` are required and present in **both** themes (see `SURFACE-AND-CONTROL-CRAFT` §2). Every semantic token in the default theme is overridden in `[data-theme="dark"]` — including the inset bg + text pairs and inset elevation, per `DESIGN_TOKENS_STANDARD` § theme variant completeness.

## Rules

- Components use semantic tokens only (no raw hex) — see `DESIGN_TOKENS_STANDARD`.
- Theme changes require a UIS-04 contrast audit on inset/elevated pairs in **each** theme before ship.

## Evidence

| Claim | Tag |
|-------|-----|
| WCAG 2.1 AA contrast on text/surface pairs | assumption until UIS-04 measured |
| Dark theme overrides every default semantic token | confirmed — see `tokens.css` `[data-theme="dark"]` block |
