# Prospect Detail — Screen SPEC

**Status:** Draft  
**Slug:** prospects-detail  
**Path:** `.work.ui/screens/prospects-detail/20260618-SCREEN-SPEC.md`

---

## 1. Summary

Sales user views a single prospect's full profile: pipeline progress, metadata (value, source, dates, notes), and stage transitions (advance, mark won/lost). Entry from prospects list row click or direct URL.

## 2. Personas & jobs

| Persona | Job |
|---------|-----|
| Sales rep | Review prospect details and advance through pipeline |
| Sales manager | Audit prospect history and verify stage accuracy |

## 3. States

| State | Behaviour |
|-------|-----------|
| loading | Skeleton placeholders for metadata cards and pipeline strip |
| empty | N/A (prospect exists or 404 redirect) |
| error | Error banner with retry; 404 redirects to prospects list |
| success | Metadata grid, pipeline progress, notes, header with actions |

## 4. Layout & hierarchy

| Region | Example id | Notes |
|--------|------------|-------|
| Page header | D2/D4 header | Title, breadcrumb back-link, actions dropdown |
| Pipeline progress | D4 pipeline strip | Horizontal stage sequence with active stage highlight |
| Metadata grid | D4 metric cards | Value, source, dates, contacts in auto-fill grid |
| Notes section | — | Free-text field in edit dialog |

## 5. Content

- Page title: `{company_name}`
- Breadcrumb: `← Prospects`
- Pipeline strip: `{STAGE_LABEL}` per stage; active stage highlighted with accent badge
- Metadata labels: "Value", "Source", "First contact", "Last interaction", "Next action", "Created by"
- Edit dialog title: "Edit prospect"
- Delete dialog title: "Delete prospect"
- Actions dropdown: "Edit", "Advance to {next stage}" or Mark won/lost, "Delete"

## 6. Interactions

1. Page load → fetch prospect GET `/api/prospects/{id}`
2. Actions dropdown → stage transition PATCH `/api/prospects/{id}/stage` → refetch + toast
3. Edit → dialog opens with pre-filled form → PATCH → refetch + toast
4. Delete → confirmation dialog → DELETE → redirect to list + toast
5. Back link → navigate to prospects list

## 7. Data dependencies

- Feature SPEC: inferred from API at `web/src/app/api/prospects/[id]/route.ts` and `web/src/app/api/prospects/[id]/stage/route.ts`

## 8. Tokens & components

| Component | Catalog status | Native waiver |
|-----------|----------------|---------------|
| Button | done | — |
| Badge | done | — |
| Dialog | done | — |
| DropdownMenu | done | — |
| Skeleton | done | — |
| Input/text | done | — |
| Select | done | native allowed (form inside dialog) |

## 9. Accessibility

WCAG AA targets for this screen. Focus visible on all controls. Keyboard operable (Tab through form fields, Escape closes modals).

## 10. Analytics

TBD

## 11. Acceptance criteria

- [ ] Page loads prospect data and renders metadata grid
- [ ] Pipeline progress strip shows all stages with current stage highlighted
- [ ] Stage transitions (advance, won, lost) update prospect and show toast feedback
- [ ] Edit dialog opens with pre-filled data and saves on submit
- [ ] Delete requires confirmation dialog before redirecting
- [ ] Skeleton loading shown during fetch
- [ ] Error state shows retry banner; 404 redirects to list
- [ ] Dropdown menu with role="menu" and keyboard dismiss

## 12. Concept / UIS registry

| UIS | Applies | Reason | Status |
|-----|---------|--------|--------|
| UIS-01 | yes | new layout sections | pending |
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

- D2: Use consistent card grid pattern for metric display with clear label/value separation
- D4: Pipeline stages displayed as a horizontal progress sequence with active stage visually emphasized
- D4: Stage transitions gated by terminal stages (won/lost not advanceable)

### regionMap

| §4 region | example id |
|-----------|------------|
| Page header | D2/D4 header |
| Pipeline progress | D4 pipeline strip |
| Metadata grid | D4 metric cards |
