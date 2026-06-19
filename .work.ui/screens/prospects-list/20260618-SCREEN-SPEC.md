# Prospects list — Screen SPEC

**Status:** Draft
**Slug:** prospects-list
**Path:** `.work.ui/screens/prospects-list/20260618-SCREEN-SPEC.md`

---

## 1. Summary

Sales team members browse, filter, and manage a pipeline of prospect companies through a data-table view. Each prospect shows company name, pipeline stage (as a badge), source, value, next action, and last interaction date. Users can filter by stage/source, search by company name, create new prospects, advance prospects through pipeline stages, and navigate to a detail view. Entry points: sidebar nav → "Prospects".

## 2. Personas & jobs

| Persona | Job |
|---------|-----|
| Sales rep | Track and update my pipeline of leads; advance prospects through stages; log next actions |
| Sales manager | View pipeline health across the team; filter by stage/source; identify stalled deals |

## 3. States

| State | Behaviour |
|-------|-----------|
| loading | Skeleton rows (pulse animation) while fetch in-flight; filter bar disabled |
| empty | Illustration + "No prospects yet" heading + "Create first prospect" CTA button |
| error | Inline banner: "Could not load prospects. [Retry]" with action button; previously loaded data hidden |
| success | Data table with rows; filter bar active; row count badge near heading |
| partial | Server returns 200 with empty items array after filters applied — "No prospects match these filters. [Clear filters]" link |
| permission-denied | Redirect to login or show "Access denied" with contact admin message |

## 4. Layout & hierarchy

Regions, breakpoints (UIS-01). Map regions to example ids in §13 `regionMap`.

| Region | Example id | Notes |
|--------|------------|-------|
| App shell (sidebar + header) | D2 | Existing app sidebar/header pattern |
| Filter bar | D4 | Collapses to single row on mobile with "Filters" button |
| Data table | D2 | Responsive: table on md+; card list on sm |
| Empty / error state | D2 | Centered in content area |

Breakpoints: sm (0–639px), md (640–1023px), lg (1024+). Filter bar stacks on sm — filters collapse behind a "Filters" toggle button.

## 5. Content

| Key | EN copy | Notes |
|-----|---------|-------|
| page.title | Prospects | H1 |
| page.subtitle | Manage your sales pipeline | H2 subtitle |
| filter.stage | Stage | Select label |
| filter.source | Source | Select label |
| filter.search | Search by company name… | Input placeholder |
| filter.clear | Clear filters | Link |
| table.col.company | Company | Sortable |
| table.col.stage | Stage | Badge |
| table.col.value | Value | Numeric, formatted |
| table.col.source | Source | |
| table.col.nextAction | Next action | |
| table.col.lastInteraction | Last interaction | Relative time |
| table.col.actions | | Overflow menu |
| empty.heading | No prospects yet | |
| empty.cta | Create first prospect | Button |
| empty.filtered | No prospects match these filters | |
| empty.filtered.clear | Clear filters | Link |
| stage.target | Target | Badge label |
| stage.connected | Connected | |
| stage.engaged | Engaged | |
| stage.call_scheduled | Call scheduled | |
| stage.call_done | Call done | |
| stage.proposal_sent | Proposal sent | |
| stage.negotiating | Negotiating | |
| stage.won | Won | Green badge |
| stage.lost | Lost | Red badge |
| action.advance | Advance stage | Menu item |
| action.edit | Edit | Menu item |
| action.delete | Delete | Menu item (danger) |

## 6. Interactions

- **Filter bar:** Stage and source selects update the query params (no submit button — auto-filter on change). Search input debounces at 300ms before triggering fetch.
- **Table row click:** Navigate to `/prospects/{id}` detail page.
- **Overflow menu (⋮) per row:** "Advance stage" (disabled if terminal stage), "Edit" (opens modal inline), "Delete" (confirmation dialog, `confirm_yes` pattern).
- **Advance stage:** PATCH `/v1/prospects/{id}/stage` with next stage in order. Optimistic UI — on failure, revert row + toast error. Terminal stages (won/lost) show "Stage is terminal" tooltip, menu item disabled.
- **Keyboard:** Focus order = filter bar → table header → first data row. Tab within rows. Enter on row = navigate to detail. Escape closes modals.
- **Empty state CTA:** Navigate to create prospect flow or inline create form.
- **New prospect:** "New prospect" button above filter bar → slide-out panel or modal with `ProspectCreate` form fields.

## 7. Data dependencies

- API: `GET /v1/prospects?stage=&source=&created_by=` — returns `ProspectListResponse` (items: `ProspectOut[]`)
- API: `POST /v1/prospects` — create new prospect
- API: `PATCH /v1/prospects/{id}/stage` — advance pipeline stage
- API: `PATCH /v1/prospects/{id}` — update prospect fields
- API: `DELETE /v1/prospects/{id}` — delete prospect
- Feature SPEC: `.work/features/prospects/…` (link only)

## 8. Tokens & components

| Component | Catalog status | Native waiver |
|-----------|----------------|---------------|
| Button | done | — |
| DataTable | planned | no — required per §13 |
| Badge | planned | no — required per §13 (stage badges) |
| Chip | planned | no — required per §13 (filter chips) |
| Select | planned | no — native `<select>` allowed on filter bar (non-primary flow) |
| Input | done | — |
| Dialog | planned | no — required for create/edit/delete confirm |
| DropdownMenu | planned | no — required for per-row actions |
| Skeleton | planned | no — required for loading state |

Use `--surface-*` tokens from globals.css. Status must be **done** before screen build tasks unless waiver documented.

## 9. Accessibility

WCAG AA targets for this screen. Focus trap in modals (UIS-05). Stage badges must not rely on color alone — include text label. Table must have semantic `<th>` scope. Sortable column headers are `<button>` elements with `aria-sort`. Empty state image has `alt=""` (decorative).

## 10. Analytics

| Event | Payload | Trigger |
|-------|---------|---------|
| prospects.list_viewed | `{filter_stage, filter_source, result_count}` | Page load / filter change |
| prospects.row_clicked | `{prospect_id, stage}` | Table row click |
| prospects.stage_advanced | `{prospect_id, from_stage, to_stage}` | Stage advance action |
| prospects.created | `{prospect_id}` | Create success |
| prospects.deleted | `{prospect_id}` | Delete confirm |
| prospects.error | `{error_type, endpoint}` | API failure |

## 11. Acceptance criteria

- [ ] Table loads prospects from `GET /v1/prospects` on mount; shows skeleton during load
- [ ] Filter by stage updates query params and refetches; empty filtered state shown when no results
- [ ] Stage badges render with distinct visual style per stage; won=green, lost=red, others=neutral
- [ ] Advance stage sends `PATCH /v1/prospects/{id}/stage` with next stage; row updates optimistically
- [ ] Terminal stages (won, lost) have disabled advance action with tooltip
- [ ] Overflow menu includes Edit (opens modal) and Delete (confirms via `confirm_yes` dialog)
- [ ] Table responsive: md+ shows full table; sm shows card list with same data
- [ ] Empty state (no prospects at all) shows illustration + CTA
- [ ] Error state shows retry banner
- [ ] Permission denied redirects to login with message
- [ ] Filter bar: stage and source as native `<select>`; search debounced 300ms
- [ ] Create new prospect opens a slide-out panel or modal with validated form
- [ ] All copy matches §5 content table (use i18n keys)
- [ ] Keyboard: Tab order follows filter → table headers → rows; Enter on row → detail page; Escape closes modals

## 12. Concept / UIS registry

| UIS | Applies | Reason | Status |
|-----|---------|--------|--------|
| UIS-01 | yes | new layout for prospects list page | pending |
| UIS-05 | yes | modals for create/edit/delete | pending |
| UIS-06 | yes | agent build of screen | pending |
| UIS-07 | yes | craft tier refined | pending |

## 13. Visual references

| Field | Value |
|-------|-------|
| **exampleIds** | `dashboards/D2`, `dashboards/D4` |
| **manifestPaths** | `.ai.ui/examples/dashboards/manifest.md` |
| **craftTier** | refined |
| **beforeScreenshot** | (none) |

### extractedRules (binding)

- Light base page; white cards; soft shadow elevation — D2
- Sidebar active pill — D2
- Mixed card + table layout; table with status badges + row highlight — D2
- Dark accent card for contrast block — D2
- Filter chips row collapses on mobile — D4
- Table with sortable columns — D4
- Dashboard grid with data row first (filter bar + count as data summary row) — D4

### regionMap

| §4 region | example id |
|-----------|------------|
| App shell (sidebar + header) | D2 |
| Filter bar | D4 |
| Data table | D2 |
| Empty / error state | D2 |

### Figma / external (optional)

- (none)
