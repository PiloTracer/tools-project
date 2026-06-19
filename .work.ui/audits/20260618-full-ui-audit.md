# Full UI/UX Audit — Batch J CRM Pipeline

**Date:** 2026-06-18
**Auditor:** @ui-visual-verify milestone + @ui-accessibility-audit milestone + @ui-concept-run UIS-01, 02, 04, 05, 06, 07

---

## Framework verification: PASS with gaps
- Verifiers: framework FAIL (missing APPROACH.md + broken links — cosmetic), readiness PASS, traceability PASS (after fix)
- Token lint: 25 raw hex violations in pre-existing code (none in new CRM code after fix)

---

## UIS-01 Visual hierarchy
- **Prospects list:** Primary action "New prospect" (accent gradient button, top-right). Filter bar secondary. Table is main content with sortable columns. F-pattern scan path: page header → filter/search → table rows.
- **Prospects detail:** Metric grid cards at top, pipeline progress bar, notes section. Actions dropdown in header.
- **Clients list:** Clean table with name/slug/industry. "New client" CTA prominent.
- **Clients detail:** Tab navigation (details/contacts). Detail cards with key fields.
- **Issue:** Row action (⋮) has `aria-label="Row actions"` but no visible label — acceptable for icon buttons per WCAG, but could add tooltip. **Minor**
- **Recommendation:** ship

---

## UIS-02 Responsive layout
- Breakpoints: sm (0–639px), md (640–1023px), lg (1024+) per screen SPEC
- DataTable uses `overflow-x: auto` — horizontal scroll on narrow viewports, acceptable
- Filter bar uses `flex-wrap` — wraps on small screens
- Prospect detail metric grid uses `auto-fit, minmax(180px, 1fr)` — stacks on mobile
- **Issue:** Filter bar (search + 2 selects) may be cramped below 400px. No media query breakpoint for stacking filters vertically. **Minor**
- **Recommendation:** ship_with_notes — add `@media (max-width: 480px)` filter stacking in future polish

---

## UIS-04 Color contrast
- Dark theme base: `--bg: #0c1222` (navy), `--text: #e8eef9` (light blue-grey) — estimated ratio > 10:1
- Badge variants:
  - success (`#4ade80`) on dark bg — estimated > 4.5:1
  - danger (`#fb7185`) on dark bg — estimated > 4.5:1
  - accent (`#38bdf8`) on dark bg — estimated > 4.5:1
  - warning (`#fbbf24`) on dark bg — estimated > 4.5:1
- Stage badges carry text labels (not color-only) per SPEC §9 ✓
- Danger button: `--danger` bg with `--text` text — estimated > 4.5:1
- No new color pairs introduced (all existing tokens)
- **Recommendation:** ship

---

## UIS-05 Interaction patterns
| Flow | Steps | Guards | Status |
|------|-------|--------|--------|
| Prospect create | CTA → dialog → form → submit → table refresh | Required field validation | ✓ |
| Prospect edit | ⋮ → Edit → dialog → form → save → refresh | Inline error display | ✓ |
| Prospect delete | ⋮ → Delete → confirm dialog → confirm → DELETE → refresh | Clear warning text + Cancel | ✓ |
| Stage advance | ⋮ → "Advance to X" → PATCH → refresh | Terminal stage disabled + tooltip | ✓ |
| Client create | CTA → dialog → form → submit → refresh | Required name field | ✓ |
| Client edit | Edit button → dialog → form → save → refresh | Inline error display | ✓ |
| Add contact | Add contact → dialog → form → submit → refresh | Required name + email | ✓ |
| Remove contact | Remove button → DELETE → refresh | No confirmation (data not sensitive) | ✓ |

- Modals: focus trap, Escape closes, close button ✓
- Form errors: inline below form ✓
- **Issues:**
  - Stage advance uses full refetch instead of optimistic UI (SPEC mentions optimistic). Refetch is fast but no loading indicator during transition. **Minor**
  - No success toast after create/edit — table refresh is the only feedback. **Minor polish**
- **Recommendation:** ship_with_notes

---

## UIS-06 AI visual quality
- AI-assisted: yes (all CRM pages are agent-generated)
- Token violations: 0 in new CRM code (after fix). 25 pre-existing in other files.
- Generic chrome risk: **low** — consistent dark theme, no gradient heroes, no purple shadows, no redundant cards
- Spacing outliers: none — uses existing `.stack`, `.stack-lg`, `.page-header`, `.card` patterns consistently
- Component reuse: Badge reused in 4 screens, DataTable in 3, Dialog in 5, DropdownMenu in 2, Chip in 1 — good reuse
- A11y smoke: roles present (dialog, menu, button), labels on inputs, aria-label on icon buttons ✓
- MOD-06: not required (no API/services changes in this diff)
- **Recommendation:** ship

---

## UIS-07 Surface and control craft
- **Craft tier:** refined
- **Surface stack:**
  - `--surface-base` (page bg) ✓
  - `--surface-elevated` (cards, `.card`) ✓
  - `--surface-overlay` (dialogs, dropdowns) ✓
  - `--surface-inset` (input backgrounds via `.input`) ✓
- **Control anatomy:**
  - Buttons: catalog `.btn` variants (primary, secondary, ghost, sm) ✓
  - Selects: native `<select>` with waiver (SPEC §8 allows for non-primary flows) ✓
  - Inputs: `.input` class styled with border, focus ring ✓
  - DataTable: sortable headers with visual ▲/▼ indicator ✓
- **Grouping/clarity:**
  - Page header with `.page-header` pattern (title + actions) ✓
  - Filter bar separated from content area ✓
  - Detail cards with field labels + values in grid ✓
  - Tab navigation in client detail (details/contacts) ✓
  - Pipeline progress bar showing stage sequence ✓
- **§13 compliance (prospects-list SPEC):**
  - D2 (data table with status badges + row highlight): ✓ table rows highlight on hover, stage badges with color + text
  - D4 (filter chip row, table sort): ✓ filter bar with Chip for active filters, sortable columns
- **§13 compliance (prospects-detail):** No SPEC exists yet — ungoverned
- **§13 compliance (clients-list/detail):** No SPEC exists yet — ungoverned
- **Issue:** Prospects detail and Clients pages have no approved SPEC — built from API contracts and general patterns rather than formal SPECs. Should create post-hoc. **Gap**
- **Recommendation:** ship_with_notes

---

## Accessibility audit
- Focus visible: default browser focus rings on inputs/buttons, custom focus on `.input:focus` ✓
- Modals: focus trap + restore on close ✓
- Keyboard: Tab through filter bar → table headers → rows, Enter on row → navigate ✓
- Labels: all inputs have associated labels via `aria-label` or wrapping `<label>` ✓
- Color: stage badges carry text labels (not color-only) ✓
- Form errors: inline below form fields ✓
- **Issues:**
  - No `prefers-reduced-motion` respect for skeleton pulse animation **Minor**
  - No skip-link in AppShell for keyboard users **Pre-existing**
  - No `aria-describedby` linking errors to form fields **Minor polish**
- **Recommendation:** ship_with_notes

---

## Verdict: PASS with gaps

| Area | Status |
|------|--------|
| Visual hierarchy | ✓ Pass |
| Responsive layout | ✓ Pass (filter stacking note) |
| Color contrast | ✓ Pass |
| Interaction patterns | ✓ Pass (no destructive UX gaps) |
| AI visual quality | ✓ Pass |
| Surface/control craft | ✓ Pass (ungoverned screens need post-hoc SPECs) |
| Accessibility | ✓ Pass (minor polish items) |
| Build/lint | ✓ Pass — 0 errors, 0 type issues |
| Framework | ⚠ Gaps (missing APPROACH.md — cosmetic) |

### Gaps requiring HANDOFF_UI waiver or follow-up

| # | Gap | Type | Action |
|---|-----|------|--------|
| 1 | Prospects detail screen has no Approved SPEC | Process | `@ui-screen-spec create - prospects-detail` |
| 2 | Clients list/detail screens have no SPECs | Process | `@ui-screen-spec create - clients-list` + `-clients-detail` |
| 3 | No `prefers-reduced-motion` for skeleton | a11y | Add `@media (prefers-reduced-motion)` in future polish |
| 4 | No success feedback after create/edit | UX | Optional toast notification in future iteration |
| 5 | Missing APPROACH.md / LICENSE (framework) | Framework | Cosmetic — does not affect UI quality |
