# Style stacks

**Set active stack:** `@ui-style-stack set - tailwind` (records in `.work.ui/context/HANDOFF_UI.md`).

Skills that emit UI code (`ui-component-build`, `ui-design-system`) **must** read the active stack file below — never mix stacks in one PR.

| Stack | Doc | Typical projects |
|-------|-----|------------------|
| `tailwind` | [tailwind.md](tailwind.md) | Next.js, Vite + React, utility-first |
| `css-modules` | [css-modules.md](css-modules.md) | CRA, component-scoped CSS |
| `vanilla-css` | [vanilla-css.md](vanilla-css.md) | Static sites, token-driven CSS |
| `styled-components` | [styled-components.md](styled-components.md) | React + theme object |

## Add a stack

1. Add `style-stacks/<name>.md` (token mapping + do/don't).
2. Row in this README.
3. Row in `APPROACH.md` §3.
4. Optional: `REPLACE:UI_STYLE_SYSTEM` in `.cursorrules`.

**No per-stack skills** — one `@ui-style-stack` skill owns selection and conventions.
