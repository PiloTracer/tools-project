# UI Vision & Principles

**Archetype:** `admin-dashboard` — internal project management hub with integrated CRM/sales pipeline.

**Craft tier:** refined — this is a customer-adjacent SaaS tool (client portal is external-facing; internal CRM is used daily by sales and PM teams). Surfaces require surface stack tokens, catalog primitives for primary flows, and section grouping.

**Complexity:** medium. Two user modes (internal team admin, client portal). Data-grid-heavy views for pipeline management, with modal/slide-over forms for CRUD. Filter bars, stage badges, overflow menus, and inline editing are primary interaction patterns.

**Style stack:** CSS custom properties on `:root` (current `web/src/app/globals.css`). No Tailwind or CSS-in-JS — plain CSS modules and global utility classes. Token file: `web/src/app/globals.css`.

**Visual language references:**
- Dark theme base (navy/indigo palette from globals.css)
- Elevated cards with soft shadow, subtle border, and glass header
- Accent-driven CTAs (cyan `--accent` gradient)
- Stage badges with semantic color (green=won, red=lost, neutral=pending)
- Data table with sortable columns, row overflow menus

**Example IDs cited in SPECs:** `dashboards/D2`, `dashboards/D4`.
- D2: Data table with status badges + row highlight, sidebar active nav, soft card elevation
- D4: Filter chip row, table sort, KPI/metric row, responsive collapse

**Accessibility target:** WCAG AA. Focus visible, keyboard operable, labels on all controls. Stage badges carry text labels (not color-only). Modal focus traps.

**Responsive:** sm (0-639px), md (640-1023px), lg (1024+). Data tables collapse to card lists on sm. Filter bar stacks on sm behind toggle.

**Performance budget:** standard SPA-level — no aggressive budgets set. Route-level JS splitting via Next.js App Router.
