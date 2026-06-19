# UI Patterns — template

> Binding **checklists** for common surfaces. Referenced from screen SPECs and `@ui-project-approach`. Replace `REPLACE:UI_` tokens after copy.

**Not a skill** — agents apply sections that match the screen SPEC type.

---

## All screens (baseline)

- [ ] One obvious primary action per viewport (UIS-01)
- [ ] Loading, empty, error, success states defined (SPEC §3)
- [ ] Focus order documented for keyboard users (UIS-05)
- [ ] Semantic tokens only — no ad-hoc hex in components
- [ ] `prefers-reduced-motion` respected (UIS-03)
- [ ] Craft tier documented in foundation 01; surfaces/controls per [`20260523-SURFACE-AND-CONTROL-CRAFT.md`](20260523-SURFACE-AND-CONTROL-CRAFT.md)

---

## Marketing / landing (`marketing-site`)

- [ ] Hero: headline hierarchy (one H1-equivalent), subcopy, single primary CTA
- [ ] Nav: logo, 3–7 top links or hub MENU pattern; sticky only if SPEC says so
- [ ] Social proof block (logos, quote, award badge) optional but structured
- [ ] Footer: legal, contact, sitemap — do not bury sole CTA
- [ ] Imagery: alt text; text-on-image contrast (UIS-04) or scrim
- [ ] Reference: `examples/websites/manifest.md`

---

## App shell (saas / admin)

- [ ] Persistent nav (sidebar or top) + clear active state
- [ ] Page title + optional breadcrumbs; actions top-right
- [ ] Content max-width on marketing pages; full-bleed only when SPEC requires
- [ ] User menu, notifications — icon buttons need `aria-label`
- [ ] Reference: `examples/dashboards/manifest.md`, `examples/websites-tecnology/manifest.md`

---

## Data density (dashboards, admin)

- [ ] KPI row: 3–5 metrics max above fold; label + value + delta pattern
- [ ] Tables: sticky header, sort indicator, row actions, empty state
- [ ] Filters: collapse on mobile; show applied filter count
- [ ] Charts: color + non-color encoding; table fallback for a11y
- [ ] Segmented status bars: do not rely on color alone (UIS-04)
- [ ] Reference: `examples/dashboards/manifest.md`

---

## Forms

- [ ] Labels visible (not placeholder-only); `aria-describedby` for errors
- [ ] Inline validation timing specified; error summary for long forms
- [ ] Primary submit disabled state vs loading state distinct
- [ ] Multi-step: progress, back, save draft if SPEC requires
- [ ] Touch targets ≥ 44px on mobile (UIS-02)
- [ ] Craft: [`20260523-SURFACE-AND-CONTROL-CRAFT.md`](20260523-SURFACE-AND-CONTROL-CRAFT.md) §3–5 when tier ≥ refined
- [ ] Reference: `examples/mobile-controls/manifest.md`

---

## Navigation (mobile & desktop)

- [ ] Mobile: bottom nav ≤ 5 items; FAB only if SPEC allows
- [ ] Drawers: focus trap, escape closes, restore focus
- [ ] Horizontal scroll lists: affordance (fade edge or partial next item)
- [ ] Reference: `examples/mobile/manifest.md`

---

## Mobile-native patterns

- [ ] Safe areas / notches considered in padding tokens
- [ ] Bottom sheets for secondary flows (filters, AI panels)
- [ ] Editor vs browse modes: different toolbars (see mobile examples)
- [ ] Craft: SURFACE-AND-CONTROL-CRAFT §2–4 when tier ≥ refined
- [ ] Reference: `examples/mobile-controls/manifest.md` · pair with `examples/mobile/manifest.md`

---

## Style stack notes

Emit implementation using active stack from `{HANDOFF_UI}` — see `style-stacks/<stack>.md`:

- **tailwind:** layout utilities + `@apply` only in primitives when documented
- **css-modules:** co-located `.module.css`; tokens as CSS variables
- **vanilla-css:** BEM or consistent prefix; tokens on `:root`
- **styled-components:** theme object mirrors token file
