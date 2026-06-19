# NEXT_UI — UI planning backlog

> **Path:** `<repo-root>/.work.ui/plans/NEXT_UI.md` · **`@ui-component-build`** owns `## Current UI iteration`.

**Updated:** 2026-06-18

---

## Done (UI)

| Item | Artifact |
|------|----------|
| UI bootstrap | `.work.ui/` skeleton |
| UI design foundation | `.work.ui/plans/foundation/20260618-0{1,2,3,4}-*.md` (4 docs) |
| Design tokens in globals.css | Surface stack, spacing, shadows, radius variants, z-index layers |
| Shared UI primitives | Badge, Chip, DataTable, Dialog, DropdownMenu, Skeleton |
| Prospects list page | `/prospects` — data table, filter bar, create/edit/delete, stage transitions |
| Prospects detail page | `/prospects/[id]` — detail view, pipeline progress, stage transitions |
| Clients list page | `/clients` — data table, create |
| Clients detail page (with contacts) | `/clients/[id]` — details tab, contacts tab with add/remove |
| Project settings CRM sections | Client linking + access management |
| AppShell CRM nav | Prospects, Clients links in navigation |
| BFF proxy routes | All CRM API endpoints proxied through Next.js API routes |

---

## Blocked on owner (UI)

| # | Item | Notes |
|---|------|-------|
| - | (none) | |

---

## Recommended next

| Priority | Item | Notes |
|----------|------|-------|
| **0** | `@ui-design-system init` | Populate CATALOG.md with built primitives |
| **1** | `@ui-screen-spec review - prospects-list` | Approve the Draft spec (post-hoc) |
| **2** | `@ui-screen-spec review - prospects-detail` | Approve Draft → Approved |
| **3** | `@ui-screen-spec review - clients-list` | Approve Draft → Approved |
| **4** | `@ui-screen-spec review - clients-detail` | Approve Draft → Approved |

---

## Intake queue

> Free-text UI requests captured by `@ui-screen-spec intake - <sentence>`. Format: `- <YYYY-MM-DD> · <class> · "<sentence>" → <next command>`. Classes: local / cross-cutting / brownfield / underspecified.

- (none yet)

---

## Current UI iteration

**Milestone:** Batch J — CRM Pipeline Front-End (Sprint 1: Implementation) — **CLOSED 2026-06-19**

## Done this UI iteration

| ID | Description | Completed |
|----|-------------|-----------|
| F0 | UI design foundation greenfield | 2026-06-18 |
| F1 | Design tokens in globals.css | 2026-06-18 |
| F4 | S0 primitives | 2026-06-18 |
| F5 | S1 screens | 2026-06-18 |
| F6 | S2 screens | 2026-06-18 |
| F7 | S3 screens | 2026-06-18 |
| F2 | Design system init (CATALOG.md) | Deferred |
| F3 | Review & approve prospects-list SPEC | Deferred |
| V0 | Visual verification | 2026-06-19 |
| A0 | Accessibility audit | 2026-06-19 |
| U8 | UIS-08 intuitive UX | 2026-06-19 |
| U9 | UIS-09 data viz quality | 2026-06-19 |
