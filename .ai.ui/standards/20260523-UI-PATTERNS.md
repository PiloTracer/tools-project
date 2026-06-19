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
- [ ] Empty states guide users (not blank or "no data" dead-ends) (UIS-08)
- [ ] Destructive actions guarded (confirm, undo, or reversible) (UIS-08)
- [ ] Error messages in plain language with recovery path (UIS-08)
- [ ] Feedback visible within 100ms of every user action (UIS-08)

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

## Dashboards & data visualization (admin, analytical, reporting)

### Layout & structure

- [ ] KPI row: 3–5 metrics max above fold; label + value + delta arrow + optional sparkline
- [ ] Dashboard grid: responsive auto-fill (`repeat(auto-fill, minmax(300px, 1fr))`) for chart cards; full-width for primary chart on desktop
- [ ] Filter bar: date range + metric selector + group-by; collapse into expandable chip row ≤ `md`
- [ ] Section headers or tab groups for multi-chart layouts; stick on scroll
- [ ] Reference: `examples/dashboards/manifest.md`

### Charts & graphs

- [ ] Chart library chosen in foundation doc 03 + HANDOFF_UI; one library per project
- [ ] Chart tokens used consistently across all charts (categorical palette, axis, grid, tooltip)
- [ ] Every chart has: loading skeleton (matching chart shape), empty state, error with retry
- [ ] Responsive: chart container scales; min readable width; legend wraps or hides at breakpoints
- [ ] Animations: `prefers-reduced-motion` disables chart enter/update animations (UIS-03)
- [ ] Interactivity documented in SPEC §14: tooltip, cross-filter, drill-down, zoom
- [ ] Reference: `resources/control-platforms.md` § Chart & data-viz libraries

### Accessibility

- [ ] Data table fallback for every chart (visually hidden or toggleable)
- [ ] `aria-label` on chart SVG regions; `role="img"` on chart root
- [ ] Keyboard navigation for interactive charts (arrow keys step through data points)
- [ ] Color + pattern encoding — not color-only (hatch, dash, shape markers)
- [ ] Tooltip content available to screen readers (aria-live region)
- [ ] UIS-09 check required at milestone verify

### Operational dashboards (real-time, monitoring)

- [ ] Auto-refresh indicator; pause/resume control; "last updated" timestamp
- [ ] Status indicators: colored dot + text label (not color-only per UIS-04)
- [ ] Activity feed: time-stamped, infinite scroll or paginated, category chips
- [ ] Alert / anomaly highlighting: visual emphasis with dismiss action
- [ ] Reference: `examples/dashboards/manifest.md` (D1, D4, D8)

### Analytical dashboards (trends, reporting)

- [ ] Date range selector (preset + custom) — persisted in URL for shareable views
- [ ] Export: CSV, PDF, or PNG per chart or full dashboard; loading state during export
- [ ] Chart + data table pair: chart for overview, table beneath for precision
- [ ] Cross-filter: clicking a chart segment filters other charts on same dashboard
- [ ] Drill-down: click data point → navigates to detail view or overlays detail panel
- [ ] Reference: `examples/dashboards/manifest.md` (D2, D4, D6)

### Reporting & export

- [ ] Report builder: metric selection, grouping, date range, schedule
- [ ] Saved reports: list + rename + delete; load applies filters automatically
- [ ] Export formats: CSV (raw data), PDF (formatted report), PNG (chart snapshots)
- [ ] Reference: `examples/dashboards/manifest.md` (D5, D6)

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
