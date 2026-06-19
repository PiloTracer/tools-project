# Design system catalog

**Updated:** 2026-06-19 · **Refresh cmd:** `@ui-design-system init`

---

## Built primitives

| Component | Tier | Path | Variants | Behavior source | Storybook | a11y notes |
|-----------|------|------|----------|-----------------|-----------|------------|
| Badge | Primitive | `web/src/components/Badge.tsx` | `neutral`, `accent`, `success`, `danger`, `warning` | — | no | Presentational `<span>`; no ARIA needed |
| Chip | Primitive | `web/src/components/Chip.tsx` | `default`, `accent` | — | no | Remove button has `aria-label="Remove"` |
| Skeleton | Primitive | `web/src/components/Skeleton.tsx` | — | — | no | `aria-hidden`; uses CSS `skeleton-pulse` keyframes |
| Toast | Primitive | `web/src/components/Toast.tsx` | `success`, `error` | — | no | Container has `aria-live="polite"`; auto-dismiss 3500ms |
| DataTable | Compound | `web/src/components/DataTable.tsx` | loading skeleton, empty state, data state | — | no | `aria-sort` on sortable headers, `role="button"` on clickable rows, keyboard navigable |
| Dialog | Compound | `web/src/components/Dialog.tsx` | — | — | no | `role="dialog"`, `aria-modal`, `aria-label={title}`, Escape to close, no focus trap |
| DropdownMenu | Compound | `web/src/components/DropdownMenu.tsx` | — | — | no | `role="menu"` + `role="menuitem"`, arrow-key nav, `aria-expanded` missing on trigger |
| DonutChart | Compound | `web/src/components/DonutChart.tsx` | — | Recharts (MIT) | no | Relies on Recharts SVG semantics; no `aria-label` on chart |
| PipelineFunnel | Compound | `web/src/components/PipelineFunnel.tsx` | count mode, value mode | Recharts (MIT) | no | Relies on Recharts SVG semantics; no `aria-label` on chart |
| MarkdownEditor | Compound | `web/src/components/MarkdownEditor.tsx` | — | — | no | Native textarea accessibility; suggestion list keyboard nav |
| StatCard | Primitive | `web/src/components/StatCard.tsx` | — | — | no | Presentational; no ARIA needed |
| CmdkPalette | Pattern | `web/src/components/CmdkPalette.tsx` | — | — | no | `role="combobox"` on input, `role="listbox"` on results, arrow-key list nav |
| KanbanBoard | Pattern | `web/src/components/KanbanBoard.tsx` | — | — | no | Column layout with `role="region"` + `aria-label` per column; drag-and-drop not implemented |
| AppShell | Pattern | `web/src/components/AppShell.tsx` | — | — | no | Skip-to-content link; `id="main-content"` on body wrapper |

## Tiers

| Tier | Definition | Components |
|------|------------|------------|
| Primitive | Single-purpose, variant API, no domain copy | Badge, Chip, Skeleton, Toast, StatCard |
| Compound | Composes primitives, domain-agnostic | DataTable, Dialog, DropdownMenu, DonutChart, PipelineFunnel, MarkdownEditor |
| Pattern | Opinionated layout, optional slot props | CmdkPalette, KanbanBoard, AppShell |

## Missing

- **no** Storybook stories for any component (requires `@ui-design-system add` per component)
- **no** `Button` or `Input` React primitives — use utility classes (`.btn`, `.btn-primary`, `.btn-sm`, `.input` in `globals.css`)
- **no** `Select` React component — native `<select>` styled via `.input` per SPEC §8 waiver
