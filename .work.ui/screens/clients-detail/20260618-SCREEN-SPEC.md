# Client Detail — Screen SPEC

**Status:** Draft  
**Slug:** clients-detail  
**Path:** `.work.ui/screens/clients-detail/20260618-SCREEN-SPEC.md`

---

## 1. Summary

User views and edits a single client's profile with tabbed navigation for details (metadata, slug, industry, notes) and contacts (add/remove contact records). Entry from clients list row click or direct URL.

## 2. Personas & jobs

| Persona | Job |
|---------|-----|
| Admin | Maintain client metadata and contact records |
| Project manager | Find client contacts for project communication |

## 3. States

| State | Behaviour |
|-------|-----------|
| loading | Skeleton placeholders |
| empty | N/A (client exists or 404 redirect) |
| error | Error banner; 404 redirects to clients list |
| success | Tabbed layout with details or contacts panel |

## 4. Layout & hierarchy

| Region | Example id | Notes |
|--------|------------|-------|
| Page header | D2/D4 header | Title, breadcrumb back-link, edit/delete actions |
| Tab navigation | — | Details / Contacts tabs |
| Details tab | D4 metric cards | Name, slug, industry, created date in grid |
| Contacts tab | D2 data table | Contact rows with add/remove, primary badge |

## 5. Content

- Page title: `{name}`
- Breadcrumb: `← Clients`
- Tabs: "Details" | "Contacts"
- Details fields: Name, Slug (monospace), Industry, Created
- Contact columns: Name (with "Primary" badge), Email, Phone, Title, Role (badge)
- Edit dialog: Name (required), Industry, Notes
- Add contact dialog: Name (required), Email (required), Phone, Title/role
- Delete dialog: "Delete {name}" with confirmation text

## 6. Interactions

1. Page load → fetch client GET `/api/clients/{id}` + contacts GET `/api/clients/{id}/contacts`
2. Tab switch → toggle between Details and Contacts panels
3. Edit → dialog → PATCH → refetch + toast
4. Delete → confirmation dialog → DELETE → redirect to list + toast
5. Add contact → dialog → POST → refetch + toast
6. Remove contact → DELETE → refetch + toast (no confirmation)

## 7. Data dependencies

- Feature SPEC: inferred from APIs at `web/src/app/api/clients/[id]/` and `web/src/app/api/clients/[id]/contacts/`

## 8. Tokens & components

| Component | Catalog status | Native waiver |
|-----------|----------------|---------------|
| Button | done | — |
| Badge | done | — |
| DataTable | done | — |
| Dialog | done | — |
| Input/text | done | — |
| Select | done | native allowed (form inside dialog) |

## 9. Accessibility

WCAG AA targets. Tab navigation uses role="tablist" pattern. Focus visible on all controls.

## 10. Analytics

TBD

## 11. Acceptance criteria

- [ ] Page loads client data and contacts in parallel
- [ ] Tabs toggle between Details and Contacts panels
- [ ] Details tab shows metadata in card grid
- [ ] Contacts tab shows data table with name, email, phone, title, role
- [ ] Primary contact shown with accent badge
- [ ] Edit dialog opens, validates, saves with toast
- [ ] Delete dialog requires confirmation before redirecting
- [ ] Add contact form validates required fields, submits with toast
- [ ] Remove contact fires DELETE and refreshes with toast
- [ ] Loading skeleton shown during fetch

## 12. Concept / UIS registry

| UIS | Applies | Reason | Status |
|-----|---------|--------|--------|
| UIS-01 | yes | tabbed layout sections | pending |
| UIS-06 | yes | agent build | pending |
| UIS-07 | yes | craft tier refined | pending |

## 13. Visual references

| Field | Value |
|-------|-------|
| **exampleIds** | D2/D4 |
| **manifestPaths** | `.ai.ui/examples/D2-D4/manifest.md` |
| **craftTier** | refined |
| **beforeScreenshot** | — |

### extractedRules (binding)

- D2: Data table with contact rows, action column for remove
- D4: Card grid for metadata with label/value separation
- D2: Badge used for contact role and primary indicator

### regionMap

| §4 region | example id |
|-----------|------------|
| Page header | D2/D4 header |
| Details tab | D4 metric cards |
| Contacts tab | D2 data table |
