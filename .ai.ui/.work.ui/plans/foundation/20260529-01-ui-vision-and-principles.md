# Demo SaaS dashboard — UI vision and principles

**Doc:** UI foundation **01** · **Created:** 2026-05-29 · **Path:** `.work.ui/plans/foundation/` · **Status:** worked example (demo)

> Worked example shipped with the framework so the demo can pass `@ui-design-foundation certify screen-spec-ready` end-to-end. A real adopter regenerates this via `@ui-design-foundation greenfield`.

## Project classification

| Field | Value |
|-------|-------|
| **Archetype** | saas-product |
| **Complexity** | M (app shell + 5–15 screens) |
| **Style stack** | tailwind |
| **Primary surfaces** | web responsive |

(Source: `@ui-project-approach - B2B SaaS dashboard with sidebar` · recorded in `HANDOFF_UI`)

## Product UI intent

> A B2B operations dashboard where small-team operators monitor key metrics and manage account settings. UI must feel calm and dense-but-legible — fast scanning over decoration.

Primary users: internal operators / admins. Primary jobs: scan dashboard KPIs, drill into a detail, adjust account + billing settings.

## Design principles

1. **Legible density** — comfortable information density without clutter; whitespace earns its place.
2. **Token-driven, themeable** — light/dark parity from day one; no raw hex in components.
3. **Calm motion** — motion clarifies state changes only (UIS-03 moderate), never decorative.

## Density and tone

- Density: comfortable
- **Craft tier:** refined (surface/elevation tokens required — see `SURFACE-AND-CONTROL-CRAFT`)
- Motion: moderate (see UIS-03)
- Brand voice in UI copy: plain, direct, operator-friendly

## Accessibility targets

- **WCAG 2.1 AA** target (assumption until measured — see `ASSUMPTIONS.md`). Contrast on inset/elevated pairs checked per theme via UIS-04.

## Platform / responsive

- Breakpoints: mobile ≤640, tablet 641–1024, desktop ≥1025. Sidebar collapses to a drawer < 1025.

## Out of scope (UI v1)

- Marketing/landing pages, white-label theming, i18n (deferred).

## Links

- Tokens: `20260529-02-design-tokens.md`
- Pattern inventory: `20260529-03-pattern-inventory.md`
- Screen map: `20260529-04-screen-map.md`
- Domain scope: `.work/plans/foundation/*-01-*` (Agent OS) when present
