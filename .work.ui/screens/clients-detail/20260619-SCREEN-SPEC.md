# Clients detail — Screen SPEC

**Status:** Draft
**Slug:** clients-detail
**Path:** `.work.ui/screens/clients-detail/20260619-SCREEN-SPEC.md`

---

## 1. Summary

Detail view for a single client company. Shows company info (name, slug, industry, notes) and a contacts sub-table with add/remove capability. Tab navigation switches between Details and Contacts views. Users can edit client fields, delete client, and manage contacts. Entry points: table row click on clients list page, or direct URL `/clients/{id}`.

## 2. Personas & jobs

| Persona | Job |
|---------|-----|
| Admin | Review/edit client details; manage contacts |
| Sales rep | View client info and contact list |

## 3. States

| State | Behaviour |
|-------|-----------|
| loading | Skeleton rows while fetch in-flight |
| not-found | Redirect to `/clients` list |
| error | Inline error message with back link |
| success | Tabbed view: details tab shows info cards; contacts tab shows contact table + add button |

## 4. Layout & hierarchy

| Region | Example id | Notes |
|--------|------------|-------|
| Back link + header | D2 | ← Clients link, name as H1, slug mono, industry badge, edit/delete buttons |
| Tab navigation | D2 | Details | Contacts ({count}) tabs |
| Details tab | D2 | Industry, created date info cards; optional notes card |
| Contacts tab | D2 | Data table with name, email, phone, title, role, remove action |

Breakpoints: sm (0–639px) stacks detail cards to single column.

## 5. Content

| Key | EN copy | Notes |
|-----|---------|-------|
| page.back | ← Clients | Back link |
| page.title | {client.name} | H1 |
| tab.details | Details | Tab label |
| tab.contacts | Contacts ({count}) | Tab label with count |
| label.industry | Industry | Info label |
| label.created | Created | Info label |
| label.notes | Notes | Section heading |
| contacts.col.name | Name | Data table column |
| contacts.col.email | Email | Data table column |
| contacts.col.phone | Phone | Data table column |
| contacts.col.title | Title | Data table column |
| contacts.col.role | Role | Badge column |
| action.edit | Edit | Button |
| action.delete | Delete | Danger button |
| action.addContact | Add contact | Button |
| action.remove | Remove | Danger button per row |

## 6. Interactions

- **Tab switch:** Toggle between Details and Contacts views. No page navigation.
- **Edit:** Opens modal with pre-filled name, industry, notes. Save → PATCH → toast → refresh.
- **Delete:** Confirmation dialog → DELETE → toast → redirect to `/clients`.
- **Add contact:** Opens modal with name (required), email (required), phone, title. Submit → POST → toast → refresh.
- **Remove contact:** Direct DELETE with toast, no confirmation (data not sensitive).

## 7. Data dependencies

- API: `GET /api/clients/{id}` — returns `ClientDetail`
- API: `GET /api/clients/{id}/contacts` — returns `{ items: ContactRow[] }`
- API: `PATCH /api/clients/{id}` — update client
- API: `DELETE /api/clients/{id}` — delete client
- API: `POST /api/clients/{id}/contacts` — add contact
- API: `DELETE /api/clients/{id}/contacts/{contactId}` — remove contact
- Feature SPEC: `.work/features/clients-participants/20260618-SPEC.md`

## 8. Tokens & components

| Component | Catalog status | Native waiver |
|-----------|----------------|---------------|
| Button | done | — |
| Badge | done | — |
| DataTable | done | — |
| Dialog | done | — |
| Input | done | — |

## 9. Accessibility

WCAG AA. Tab buttons have `aria-selected` or active styling. Edit/contact modals have focus trap. Remove contact buttons have clear labeling.

## 10. Analytics

| Event | Payload | Trigger |
|-------|---------|---------|
| client.detail_viewed | `{client_id}` | Page load |
| client.tab_switched | `{client_id, tab}` | Tab switch |
| client.edited | `{client_id}` | Edit save |
| client.deleted | `{client_id}` | Delete confirm |
| client.contact_added | `{client_id, contact_email}` | Contact add |
| client.contact_removed | `{client_id, contact_id}` | Contact remove |

## 11. Acceptance criteria

- [ ] Loads client + contacts on mount; shows skeleton during load
- [ ] Tab navigation: Details shows info cards (industry, created); Contacts shows contact table
- [ ] Notes card only shown when notes are non-empty
- [ ] Edit button opens modal with pre-filled fields; PATCH on save
- [ ] Delete shows confirmation dialog; on confirm, deletes and redirects to list
- [ ] Add contact opens modal with required name/email
- [ ] Remove contact sends DELETE without confirmation
- [ ] Primary contact shows "Primary" badge
- [ ] Responsive: metric grid stacks on mobile

## 12. Concept / UIS registry

| UIS | Applies | Reason | Status |
|-----|---------|--------|--------|
| UIS-01 | yes | detail layout with tabs + data table | pending |
| UIS-05 | yes | modals for edit/add contact | pending |
| UIS-06 | yes | agent build of screen | pending |
| UIS-07 | yes | craft tier refined | pending |

## 13. Visual references

| Field | Value |
|-------|-------|
| **exampleIds** | `dashboards/D2` |
| **manifestPaths** | `.ai.ui/examples/dashboards/manifest.md` |
| **craftTier** | refined |
| **beforeScreenshot** | (none) |

### extractedRules

- Tab navigation pattern — D2
- Detail card grid with key-value layout — D2
- Data table with action buttons per row — D2
- Back link pattern — D2

### regionMap

| §4 region | example id |
|-----------|------------|
| Back link + header | D2 |
| Tab navigation | D2 |
| Details tab cards | D2 |
| Contacts tab table | D2 |
