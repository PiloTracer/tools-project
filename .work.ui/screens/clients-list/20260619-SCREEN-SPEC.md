# Clients list — Screen SPEC

**Status:** Draft
**Slug:** clients-list
**Path:** `.work.ui/screens/clients-list/20260619-SCREEN-SPEC.md`

---

## 1. Summary

Administrative list of client companies. Shows name, slug, industry, and created date in a sortable data table. Users can search by name or slug, create new clients, and navigate to the detail page. Entry points: sidebar nav → "Clients".

## 2. Personas & jobs

| Persona | Job |
|---------|-----|
| Admin | Browse and manage client companies; create new clients |
| Sales rep | View client list and navigate to client details |

## 3. States

| State | Behaviour |
|-------|-----------|
| loading | Skeleton rows while fetch in-flight |
| empty | "No clients yet." message |
| error | Inline error banner with retry button |
| success | Data table with rows; search bar active |

## 4. Layout & hierarchy

| Region | Example id | Notes |
|--------|------------|-------|
| App shell (sidebar + header) | D2 | Existing app shell pattern |
| Page header | D2 | CRM pill, title, lead text, "New client" CTA |
| Search bar | D4 | Search input with Export button |
| Data table | D2 | Name (bold), slug (mono), industry, created date |

Breakpoints: sm (0–639px) shows table with horizontal scroll; md+ full table layout.

## 5. Content

| Key | EN copy | Notes |
|-----|---------|-------|
| page.title | Clients | H1 |
| page.subtitle | Company clients and organizations | H2 subtitle |
| search.placeholder | Search by name or slug… | Input placeholder |
| table.col.name | Name | Sortable |
| table.col.slug | Slug | Monospace |
| table.col.industry | Industry | Sortable |
| table.col.created | Created | Sortable |
| empty.message | No clients yet. | Empty state |
| action.new | New client | Button |

## 6. Interactions

- **Table row click:** Navigate to `/clients/{id}` detail page.
- **Search:** Filters rows client-side by name or slug.
- **New client:** Opens modal with name (required), industry, notes fields.
- **Create:** POST `/api/clients` — on success, toast + table refresh.

## 7. Data dependencies

- API: `GET /api/clients` — returns `{ items: ClientRow[] }`
- API: `POST /api/clients` — create new client
- Feature SPEC: `.work/features/clients-participants/20260618-SPEC.md`

## 8. Tokens & components

| Component | Catalog status | Native waiver |
|-----------|----------------|---------------|
| Button | done | — |
| DataTable | done | — |
| Dialog | done | — |
| Input | done | — |

## 9. Accessibility

WCAG AA. Sortable table headers have `aria-sort`. Search input has `aria-label`. Create modal has focus trap.

## 10. Analytics

| Event | Payload | Trigger |
|-------|---------|---------|
| clients.list_viewed | `{result_count}` | Page load |
| clients.row_clicked | `{client_id}` | Table row click |
| clients.created | `{client_id}` | Create success |

## 11. Acceptance criteria

- [ ] Loads clients from `GET /api/clients` on mount; shows skeleton during load
- [ ] Search filters rows by name or slug client-side
- [ ] Columns: Name (sortable), Slug, Industry (sortable), Created (sortable)
- [ ] Row click navigates to `/clients/{id}`
- [ ] New client button opens create modal with validated form
- [ ] Create sends POST and refreshes table with toast on success
- [ ] Empty state shows "No clients yet."
- [ ] Error state shows retry banner

## 12. Concept / UIS registry

| UIS | Applies | Reason | Status |
|-----|---------|--------|--------|
| UIS-01 | yes | list page with data table | pending |
| UIS-05 | yes | create modal | pending |
| UIS-06 | yes | agent build of screen | pending |
| UIS-07 | yes | craft tier refined | pending |

## 13. Visual references

| Field | Value |
|-------|-------|
| **exampleIds** | `dashboards/D2`, `dashboards/D4` |
| **manifestPaths** | `.ai.ui/examples/dashboards/manifest.md` |
| **craftTier** | refined |
| **beforeScreenshot** | (none) |

### extractedRules

- Data table with sortable columns — D4
- Page header with pill + title + subtitle — D2
- Search bar with action buttons — D4

### regionMap

| §4 region | example id |
|-----------|------------|
| App shell | D2 |
| Page header | D2 |
| Search bar | D4 |
| Data table | D2 |
