# Clients List — Screen SPEC

**Status:** Draft  
**Slug:** clients-list  
**Path:** `.work.ui/screens/clients-list/20260618-SCREEN-SPEC.md`

---

## 1. Summary

User browses and manages organization clients. View a sortable data table of all clients (name, slug, industry, created date), search by name/slug, and create new clients. Entry from left nav "Clients" link.

## 2. Personas & jobs

| Persona | Job |
|---------|-----|
| Admin | Manage client records and verify client metadata |
| Project manager | Find and view client details for project assignments |

## 3. States

| State | Behaviour |
|-------|-----------|
| loading | DataTable skeleton rows |
| empty | Empty state message "No clients yet." |
| error | Error banner with retry button |
| success | Data table with client rows, search input, create dialog |

## 4. Layout & hierarchy

| Region | Example id | Notes |
|--------|------------|-------|
| Page header | D2/D4 header | Title, CRM pill, "New client" CTA |
| Filter bar | D4 filter bar | Search input |
| Data table | D2 data table | Name, slug, industry, created columns, sortable |

## 5. Content

- Page title: "Clients"
- Subtitle: "Company clients and organizations"
- CTA: "New client"
- Table columns: Name (bold), Slug (monospace), Industry, Created
- Search placeholder: "Search by name or slug…"
- Create dialog title: "New client"
- Form fields: Company name (required), Industry, Notes

## 6. Interactions

1. Page load → fetch clients GET `/api/clients`
2. Click row → navigate to `/clients/{id}`
3. Search → filter rows client-side by name/slug
4. Sort → click column header to toggle sort
5. "New client" → dialog → POST → refresh + toast

## 7. Data dependencies

- Feature SPEC: inferred from API at `web/src/app/api/clients/route.ts`

## 8. Tokens & components

| Component | Catalog status | Native waiver |
|-----------|----------------|---------------|
| Button | done | — |
| DataTable | done | — |
| Dialog | done | — |
| Input/text | done | — |

## 9. Accessibility

WCAG AA targets. Search input has `aria-label="Search clients"`. DataTable sortable columns announced via ARIA.

## 10. Analytics

TBD

## 11. Acceptance criteria

- [ ] Page loads and displays client data table
- [ ] Search filters rows client-side by name or slug
- [ ] Column headers are sortable with ▲/▼ indicators
- [ ] Row click navigates to client detail page
- [ ] Create dialog opens, validates required field, submits and refreshes
- [ ] Success toast on create
- [ ] Loading skeleton shown during fetch
- [ ] Error state shows banner with retry

## 12. Concept / UIS registry

| UIS | Applies | Reason | Status |
|-----|---------|--------|--------|
| UIS-01 | yes | data table layout | pending |
| UIS-06 | yes | agent build | pending |
| UIS-07 | yes | craft tier refined | pending |

## 13. Visual references

| Field | Value |
|-------|-------|
| **exampleIds** | D2 |
| **manifestPaths** | `.ai.ui/examples/D2-D4/manifest.md` |
| **craftTier** | refined |
| **beforeScreenshot** | — |

### extractedRules (binding)

- D2: Data table with sortable columns, row hover highlight, clear column headers
- D2: Primary action button in page header region

### regionMap

| §4 region | example id |
|-----------|------------|
| Page header | D2/D4 header |
| Data table | D2 data table |
