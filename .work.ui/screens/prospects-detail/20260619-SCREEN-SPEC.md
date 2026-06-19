# Prospects detail — Screen SPEC

**Status:** Draft
**Slug:** prospects-detail
**Path:** `.work.ui/screens/prospects-detail/20260619-SCREEN-SPEC.md`

---

## 1. Summary

Detail view for a single prospect. Shows company name, pipeline stage badge, key metrics (value, source, dates), full notes, and an interactive pipeline progress bar. Users can edit fields, advance/change stage, or delete the prospect. Entry points: table row click on prospects list page, or direct URL `/prospects/{id}`.

## 2. Personas & jobs

| Persona | Job |
|---------|-----|
| Sales rep | Review prospect details; update notes/stage; advance pipeline; log next action |

## 3. States

| State | Behaviour |
|-------|-----------|
| loading | Skeleton rows (pulse) while fetch in-flight |
| not-found | Redirect to `/prospects` list |
| error | Inline error message with back link |
| success | Detail cards with metric grid, notes, pipeline progress, action menu |

## 4. Layout & hierarchy

| Region | Example id | Notes |
|--------|------------|-------|
| Back link + header | D2 | ← Prospects link, company name as H1, stage badge, actions dropdown |
| Metric grid | D2 | Value, source, first contact, last interaction, next action, created |
| Notes card | D2 | Pre-formatted text block (shown only when notes present) |
| Pipeline progress | D2 | Stage sequence with visual progress indicators; advance button |

Breakpoints: sm (0–639px) stacks metric grid to single column; md+ shows 2–3 column grid.

## 5. Content

| Key | EN copy | Notes |
|-----|---------|-------|
| page.back | ← Prospects | Back link |
| page.title | {company_name} | H1 |
| label.value | Value | Metric label |
| label.source | Source | Metric label |
| label.firstContact | First contact | Metric label |
| label.lastInteraction | Last interaction | Metric label |
| label.nextAction | Next action | Metric label |
| label.created | Created | Metric label |
| label.notes | Notes | Section heading |
| label.pipelineProgress | Pipeline progress | Section heading |
| action.edit | Edit | Dropdown item |
| action.advance | Advance to {stage} | Dropdown item / button |
| action.markWon | Mark as won | Dropdown item |
| action.markLost | Mark as lost | Dropdown item (danger) |
| action.delete | Delete | Dropdown item (danger) |

## 6. Interactions

- **Back link:** Navigate to `/prospects` list page.
- **Actions dropdown (▾):** "Edit" opens edit modal, "Advance to {next}" moves stage forward, "Mark as won/lost" shortcuts, "Delete" shows confirmation dialog.
- **Stage advance:** PATCH `/v1/prospects/{id}/stage` — on success, show toast and refresh. On failure, show error toast.
- **Edit form:** Modal dialog with pre-filled fields (name, stage, value, source, notes). Save → PATCH → toast → refresh.
- **Delete:** Confirmation dialog with danger button. DELETE → toast → redirect to `/prospects`.
- **Pipeline progress bar:** Visual stage sequence with current position highlighted. Clicking advance button on terminal stages is disabled.

## 7. Data dependencies

- API: `GET /v1/prospects/{id}` — returns `ProspectDetail` (company_name, pipeline_stage, pipeline_value, source, first_contact_date, last_interaction, next_action, notes, created_by, timestamps)
- API: `PATCH /v1/prospects/{id}` — update fields
- API: `PATCH /v1/prospects/{id}/stage` — advance stage
- API: `DELETE /v1/prospects/{id}` — delete

## 8. Tokens & components

| Component | Catalog status | Native waiver |
|-----------|----------------|---------------|
| Button | done | — |
| Badge | done | — |
| Dialog | done | — |
| DropdownMenu | done | — |
| Input | done | — |

## 9. Accessibility

WCAG AA. Stage badges include text labels (not color-only). Edit/delete modals have focus trap and Escape-to-close. Pipeline stages use both color and text indicators.

## 10. Analytics

| Event | Payload | Trigger |
|-------|---------|---------|
| prospect.detail_viewed | `{prospect_id}` | Page load |
| prospect.stage_advanced | `{prospect_id, from_stage, to_stage}` | Stage advance |
| prospect.edited | `{prospect_id}` | Edit save |
| prospect.deleted | `{prospect_id}` | Delete confirm |

## 11. Acceptance criteria

- [ ] Shows company name, stage badge, metric grid on load
- [ ] Metric grid renders as cards with key-value pairs in 2-3 column layout on md+; stacks to single column on sm
- [ ] Back link navigates to /prospects list page
- [ ] Stage badge uses correct variant color per stage
- [ ] Actions dropdown includes Edit, Advance, Mark won/lost (contextual), Delete
- [ ] Edit modal pre-fills current values and validates required fields
- [ ] Stage advance sends PATCH and refreshes on success; shows error toast on failure
- [ ] Pipeline progress bar highlights current stage and shows advance button
- [ ] Terminal stages (won, lost) disable advance action
- [ ] Delete shows confirmation dialog; on confirm, deletes and redirects to list
- [ ] Notes section only rendered when notes are non-empty
- [ ] Metric grid responsive: stacks on mobile

## 12. Concept / UIS registry

| UIS | Applies | Reason | Status |
|-----|---------|--------|--------|
| UIS-01 | yes | detail layout with metric grid | pending |
| UIS-05 | yes | modals for edit/delete | pending |
| UIS-06 | yes | agent build of screen | pending |
| UIS-07 | yes | craft tier refined | pending |

## 13. Visual references

| Field | Value |
|-------|-------|
| **exampleIds** | `dashboards/D2` |
| **manifestPaths** | `.ai.ui/examples/dashboards/manifest.md` |
| **craftTier** | refined |
| **beforeScreenshot** | (none) |

### extractedRules (binding)

- Detail card grid with key-value layout — D2
- Action menu in header area — D2
- Pipeline stage sequence with visual progress — D2
- Back link pattern — D2

### regionMap

| §4 region | example id |
|-----------|------------|
| Back link + header | D2 |
| Metric grid | D2 |
| Notes card | D2 |
| Pipeline progress | D2 |
