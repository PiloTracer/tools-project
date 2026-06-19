# Analytical Dashboard — Stats, Graphs, Reporting

## Bootstrap with chart-aware approach

```text
@ui-project-approach - analytical dashboard with revenue trends, user growth, and KPI widgets
@ui-design-foundation greenfield
@ui-design-foundation certify screen-spec-ready
```

## Select chart library & set chart tokens

Pick one chart library in foundation doc 03 (see `resources/control-platforms.md`):

```text
# Chart library: Recharts / Nivo / Vega-Lite / Chart.js / Tremor / MUI X Charts
# Add chart tokens to design token file (categorical palette, semantic colors, axis/grid, tooltip)
```

## Create dashboard screen SPEC with data viz section

```text
@ui-screen-spec create - dashboard-overview
@ui-screen-spec create - reports-analytics
# SPEC automatically includes §14 Data visualization:
#   14a — Chart types, data source, interactions
#   14b — Responsive per-chart sizing
#   14c — Chart tokens from token file
#   14d — Loading/empty/error/animation states per chart
#   14e — Data table fallback, aria-labels, keyboard nav, color+pattern encoding
```

## Build chart components & dashboard layout

```text
@ui-component-build plan - S0
@ui-component-build start
@ui-component-build continue - 1
# Build chart cards: KPI row, line chart, bar chart, data table
@ui-component-build continue - until complete
```

## Verify before ship

```text
@ui-visual-verify milestone
@ui-accessibility-audit milestone
@ui-concept-run - UIS-08     # Intuitive UX (required)
@ui-concept-run - UIS-09     # Data viz quality (required for analytical)
@ui-component-build complete
```

## Dashboard layout patterns

| Pattern | When |
|---------|------|
| KPI row (3–5 metrics, sparklines, deltas) | Top of dashboard, above fold |
| Chart grid (responsive auto-fill, min 280px) | Multi-chart view |
| Chart + data table pair | Chart for overview, table beneath for precision |
| Filter bar (date range + metric + group-by) | Across all charts; persisted in URL |
| Cross-filter (click chart → filters other charts) | Complex multi-chart analytical views |
| Drill-down (click → detail panel or new view) | Hierarchical data (year → quarter → month) |
