## UIS-09 Data visualization quality

- **Chart integrity:** ok — zero-based Y domain `[0, maxVal]`. Bars ordered by pipeline stage sequence (natural funnel order). No misleading truncation, 3D perspective, or dual axes. Single metric per bar.
- **Colorblind safety:** ok — single accent color (`var(--accent)` = #38bdf8) across all bars, so no confusable series pairs. Tooltip provides exact values on hover. No non-color encoding needed for single-series data.
- **Responsive:** ok — `ResponsiveContainer` adapts to width. Labels angled -20° with `textAnchor="end"` remain readable at 375px. Height fixed at 220px adequate.
- **Interactivity:** ok — Tooltip shows exact values on hover/focus. No drill-down (appropriate for overview). **Minor gap:** pipeline stats fetch failure is silent — chart simply doesn't render. Add error state or inline error for fetch failure.
- **Chart junk:** ok — minimal horizontal dashed gridlines only. No gradients, glows, 3D effects, or ornament. Chart ink ratio well above 70%.
- **Overall:** ship — no blocking issues. Minor: add error handling for pipeline stats fetch failure.
