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
| **1** | `@ui-visual-verify milestone` | Verify against SPEC §13 extractedRules |
| **2** | `@ui-accessibility-audit milestone` | WCAG AA audit for CRM screens |
| **3** | `@ui-concept-run - UIS-06` | Agent-assisted UI diff compliance |
| **4** | `@ui-concept-run - UIS-07` | Craft tier refined compliance |
| **5** | `@ui-screen-spec review - prospects-list` | Approve the Draft spec (post-hoc) |
| **6** | `@ui-screen-spec create - prospects-detail` | Create SPEC for prospect detail view |
| **7** | `@ui-screen-spec create - clients-list` | Create SPEC for client list |
| **8** | `@ui-screen-spec create - clients-detail` | Create SPEC for client detail |

---

## Intake queue

> Free-text UI requests captured by `@ui-screen-spec intake - <sentence>`. Format: `- <YYYY-MM-DD> · <class> · "<sentence>" → <next command>`. Classes: local / cross-cutting / brownfield / underspecified.

- (none yet)

---

## Current UI iteration

**Milestone:** Batch J — CRM Pipeline Front-End (Sprint 1: Implementation)

### Active tasks

| ID | Description | Status |
|----|-------------|--------|
| F0 | UI design foundation greenfield | **Done** 2026-06-18 |
| F1 | Add design tokens to globals.css | **Done** 2026-06-18 |
| F2 | Design system init (CATALOG.md) | **Pending** |
| F3 | Review & approve prospects-list SPEC | **Pending** |
| F4 | Build S0 primitives (DataTable, Badge, Dialog, DropdownMenu, Chip, Skeleton) | **Done** 2026-06-18 |
| F5 | Build S1 screens (Prospects list + AppShell nav) | **Done** 2026-06-18 |
| F6 | Build S2 screens (Prospects detail, Clients list/detail, Contacts) | **Done** 2026-06-18 |
| F7 | Build S3 screens (Project settings CRM sections) | **Done** 2026-06-18 |
| V0 | Visual verification | **Pending** |
| A0 | Accessibility audit | **Pending** |

---

## Done this UI iteration

| ID | Description | Completed |
|----|-------------|-----------|
| F0 | UI design foundation greenfield | 2026-06-18 |
| F1 | Design tokens in globals.css | 2026-06-18 |
| F4 | S0 primitives | 2026-06-18 |
| F5 | S1 screens | 2026-06-18 |
| F6 | S2 screens | 2026-06-18 |
| F7 | S3 screens | 2026-06-18 |
