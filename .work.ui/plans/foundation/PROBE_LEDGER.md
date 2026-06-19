# PROBE_LEDGER — UI Design OS foundation coverage

**Last updated:** 2026-06-19

**Coverage: 86%** (target 85%)

|  | Dimension | Status | Confidence | Evidence | Notes |
|--|----------|--------|------------|----------|-------|
| D1 | design-tokens | confirmed | high | `web/src/app/globals.css` defines full token set (surface stack, spacing, shadows, z-index, color, fonts) | All tokens documented |
| D2 | screen-map | confirmed | high | `.work.ui/plans/foundation/20260618-04-screen-map.md` lists 7 screens with routes, milestones, SPEC status | All screens mapped |
| D3 | screen-specs | confirmed | high | `.work.ui/screens/prospects-list/20260618-SCREEN-SPEC.md`, `.work.ui/screens/prospects-detail/20260619-SCREEN-SPEC.md`, `.work.ui/screens/clients-list/20260619-SCREEN-SPEC.md`, `.work.ui/screens/clients-detail/20260619-SCREEN-SPEC.md` | 4 SPECs authored; remaining 3 are embedded sections |
| D4 | component-catalog | confirmed | med | Badge, Button, Chip, DataTable, Dialog, DropdownMenu, Input, Skeleton, Toast implemented; `.work.ui/design-system/CATALOG.md` placeholder exists | CATALOG.md needs population |
| D5 | accessibility | confirmed | med | Focus traps, aria-labels, color+text badges, global `prefers-reduced-motion`; no skip-link in AppShell | WCAG AA target |
| D6 | responsive | confirmed | high | Breakpoints sm/md/lg; DataTable overflow-x; filter-bar flex-wrap; metric grid auto-fit | All screens responsive |
| D7 | craft-tier | confirmed | high | Surface stack (base, elevated, overlay, inset); catalog components used; §13 references on all SPECs | Craft tier: refined |
