# UI Code Conventions — template

> **UI Design OS template.** Copy/rename per `.cursorrules` `REPLACE:UI_CONVENTIONS_FILE`. Replace all `REPLACE:UI_` tokens.

**Status:** Customize per repo, then binding for UI code.
**Pairs with:** `REPLACE:UI_DESIGN_TOKENS_FILE`, `REPLACE:UI_COMPONENT_STANDARD_FILE`, screen SPECs under `{SCREEN_SPEC_ROOT}`.

---

## 1. Stack surfaces

| Surface | Tooling | Notes |
|---------|---------|-------|
| `REPLACE:UI_FRAMEWORK` | `REPLACE:UI_LINT`, `REPLACE:UI_TYPECHECK`, `REPLACE:UI_TEST` | Run in container per `.cursorrules` § Docker |
| Styles | `REPLACE:UI_STYLE_SYSTEM` (e.g. Tailwind, CSS Modules, styled-components) | No raw hex in components — use tokens |
| Visual regression | `REPLACE:UI_VISUAL_TEST` (e.g. Playwright, Chromatic) | Required before UI milestone complete |

## 2. File and folder layout

Follow `{UI_DIRECTORY_MAP}` (or interim paths in `.cursorrules`):

- `REPLACE:UI_APP_ROOT` — application UI entry (e.g. `src/`, `apps/web/`)
- `REPLACE:UI_COMPONENTS_DIR` — shared primitives and compounds
- `REPLACE:UI_SCREENS_DIR` — route-level or page-level modules
- `REPLACE:UI_TOKENS_FILE` — single source for design tokens (CSS variables, theme object, or JSON → codegen)

## 3. Naming

- Components: `PascalCase` files matching export (`Button.tsx` → `Button`)
- Hooks: `useKebabScope` in `use-*.ts`
- Screen modules: match route slug or screen SPEC slug
- Storybook stories: `<Component>.stories.tsx` colocated or under `__stories__/`
- Test ids: `data-testid="scope-element"` — stable, not CSS-class-derived

## 4. Design tokens (mandatory)

- **Semantic tokens** for color, spacing, typography, radius, shadow, z-index
- **No** hard-coded `#RRGGBB` or `px` magic numbers in feature components (exceptions: documented in token file with owner approval)
- Dark mode: use semantic tokens that map per theme — not duplicate component trees

## 5. Components

- **Primitive** → **compound** → **screen** layering; screens do not import other screens' internals
- Props: explicit types; prefer composition over boolean prop explosion (`variant`, `size` enums documented in design system skill)
- Accessibility: focus visible, keyboard operable, labels on form controls — see `REPLACE:UI_ACCESSIBILITY_FILE`

## 6. State and data

- Server state: `REPLACE:UI_DATA_FETCHING` (e.g. TanStack Query) — loading/error/empty states required in screen SPEC
- URL state for shareable views when SPEC says so
- No fetching in leaf primitives unless documented as data-aware

## 7. Performance

| Budget | Target |
|--------|--------|
| LCP (marketing) | REPLACE:UI_LCP_MS ms |
| Interaction (INP) | REPLACE:UI_INP_MS ms |
| JS bundle per route | REPLACE:UI_ROUTE_BUDGET_KB kb gzip (document exceptions) |

## 8. Internationalization

- User-visible strings via `REPLACE:UI_I18N_METHOD` — no literal English in shared components unless locale-fixed by SPEC
- RTL: layout tokens and logical properties (`margin-inline`, `inset-inline`)

## 9. Review

- UI PR: ≥1 reviewer; a11y-tagged reviewer when forms, modals, or navigation change
