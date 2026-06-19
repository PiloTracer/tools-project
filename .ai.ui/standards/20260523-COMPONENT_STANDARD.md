# Component Standard — template

> Shared UI building blocks under `REPLACE:UI_COMPONENTS_DIR`.

---

## 1. Tiers

| Tier | Examples | Rules |
|------|----------|-------|
| **Primitive** | Button, Input, Text, Icon | No domain copy; variant API documented in design system |
| **Compound** | DateField, SearchBar | May compose primitives; still domain-agnostic |
| **Pattern** | PageHeader, EmptyState | Opinionated layout; optional slot props |
| **Screen** | CheckoutPage | Lives in `REPLACE:UI_SCREENS_DIR`; implements one screen SPEC |

## 2. API design

- `variant`, `size`, `disabled`, `className` — consistent names across primitives
- Forward refs on interactive primitives
- `asChild` or polymorphic `as` only when documented in design system

## 3. Styling

- Use token-backed classes or CSS variables
- No `!important` except documented escape hatches
- Responsive: mobile-first; breakpoints from token file

## 4. Documentation

Each primitive added via `@ui-design-system add`:

- Storybook: default + all variants + disabled + focus
- Props table in story description or MDX
- a11y note: role, keyboard, aria-*

## 5. Testing

| Tier | Unit | Visual | a11y |
|------|------|--------|------|
| Primitive | required | recommended | axe in story or test |
| Compound | required | recommended | required |
| Screen | integration | required | required per screen SPEC |

## 6. Deprecation

Mark `@deprecated` in JSDoc; migration note in `.work.ui/decisions/` or `.work/decisions/`.
