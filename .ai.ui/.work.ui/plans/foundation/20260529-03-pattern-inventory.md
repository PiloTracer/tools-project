# Demo SaaS dashboard — Pattern inventory

**Doc:** UI foundation **03** · **Created:** 2026-05-29 · **Status:** worked example (demo)

## Existing (in repo today)

| Pattern | Location | Reuse? |
|---------|----------|--------|
| (none — greenfield demo) | - | - |

## Needed (net-new)

| Pattern | Tier | Priority | Screen(s) | Example id | Catalog primitive |
|---------|------|----------|-----------|------------|-------------------|
| Button | primitive | P0 | all | dashboards/D1 | Button |
| AppShell (sidebar + topbar) | composite | P0 | dashboard-home, settings | dashboards/D1 | AppShell |
| StatCard | composite | P0 | dashboard-home | dashboards/D1 | StatCard |
| Tabs | primitive | P1 | settings | dashboards/D1 | Tabs |
| RangeSlider | primitive | P1 | settings | mobile-controls/C1 | RangeSlider |

## Milestone fit (primitive-first)

- **S0:** P0 primitives (Button, AppShell, StatCard) catalogued + Storybook before screens.
- **S1:** `dashboard-home` composition. **S2:** `settings` (Tabs, RangeSlider).

(See `20260529-04-screen-map.md` § Milestones.)

## Catalog

Detailed rows: [`../../design-system/CATALOG.md`](../../design-system/CATALOG.md) (maintained by `@ui-design-system`).
