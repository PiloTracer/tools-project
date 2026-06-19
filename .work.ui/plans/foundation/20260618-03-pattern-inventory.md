# Pattern Inventory

**Example IDs:** `dashboards/D2`, `dashboards/D4`

---

## 1. Existing components (catalog status: done)

| Component | File | Notes |
|-----------|------|-------|
| Button | `globals.css` `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-sm` | Utility classes, not a React component |
| Input | `globals.css` `.input` | Utility class |
| Badge/Pill | `globals.css` `.pill`, `.pill-ok`, `.pill-muted` | Utility classes, not a React component |
| AppShell | `web/src/components/AppShell.tsx` | Navigation shell with header + nav links |
| CmdkPalette | `web/src/components/CmdkPalette.tsx` | Command palette |
| KanbanBoard | `web/src/components/KanbanBoard.tsx` | Task kanban |
| MarkdownEditor | `web/src/components/MarkdownEditor.tsx` | Rich text |

## 2. Needed components (catalog status: planned)

Per prospects list SPEC §8 + craft tier refined.

| Priority | Component | Tier | Source example | React? | Notes |
|----------|-----------|------|----------------|--------|-------|
| P0 | `DataTable` | Compound | D2, D4 | Yes | Sortable columns, responsive (card list on sm), row click, selectable rows |
| P0 | `Badge` | Primitive | D2 | Yes | Semantic colors (success, danger, neutral, accent). Stage badges with text label |
| P0 | `Dialog` | Compound | — | Yes | Modal with header, body, footer. Focus trap, Escape to close, overlay backdrop |
| P0 | `DropdownMenu` | Compound | D4 | Yes | Overflow menu (kebab ⋮). Per-row actions: Advance stage, Edit, Delete |
| P1 | `Chip` | Primitive | D4 | Yes | Filter chips, removable. Used in filter bar |
| P1 | `Select` | Primitive | D4 | Native waiver per SPEC | Native `<select>` styled via `.input` allowed on filter bar (non-primary flow) |
| P1 | `Skeleton` | Primitive | — | Yes | Pulse-animated loading placeholder rows |

## 3. Screen-level components (planned)

| Component | Route | Depends on |
|-----------|-------|------------|
| `ProspectListPage` | `/prospects` | DataTable, Badge, DropdownMenu, Dialog, Select, Skeleton |
| `ProspectDetailPage` | `/prospects/[id]` | Badge, Dialog, (tabs) |
| `ProspectCreateForm` | modal/slide-over | Dialog, Input, Button, Select |
| `StageTransitionButton` | inline | DropdownMenu, Badge |
| `ClientListPage` | `/clients` | DataTable, Badge, Dialog |
| `ClientDetailPage` | `/clients/[id]` | Badge, (tabs), (contacts sub-list) |
| `ClientContactForm` | modal | Dialog, Input, Button |

## 4. AppShell nav additions

| Link | Route | Icon | Gate |
|------|-------|------|------|
| Prospects | `/prospects` | — | Authenticated internal user |
| Clients | `/clients` | — | Authenticated internal user |

These appear after Inbox in the nav-links list.
