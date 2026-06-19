# Data visualization quality — agent procedure (UIS-09)

## Inputs

- Screen SPEC §14 (data visualization)
- Chart tokens from design token file
- Rendered chart components or chart specs
- User goals / analytical questions from foundation doc 01

## Procedure

1. **Chart integrity & truthful encoding** — Are axis scales zero-based for bar charts? Are pie/donut charts ordered by value? Flag misleading truncation, 3D perspective distortion, dual axes without clear labeling, or cherry-picked ranges. Sparkline-only must be accompanied by precise value.

2. **Perceptibility & colorblind safety** — Run categorical palette through colorblind simulation (deuteranopia, protanopia). Do any series pairs become indistinguishable? Is there non-color encoding (patterns, dashes, markers, direct labels) on every chart? Minimum 3:1 contrast for data-ink vs background.

3. **Responsive & dense-read** — Can every chart be read at 375px width? Do axis labels rotate, truncate, or overlap? Does the chart have a minimum readable size below which it switches to a compact variant or data table? KPI row collapses to 2 columns on mobile.

4. **Interactivity & data precision** — Tooltip shows exact values on hover/focus (not just approximate). Cross-filter or drill-down behavior documented in SPEC §14. Loading, empty, error, and animation states present per chart. No silent failures on partial data.

5. **Non-chart ink & chart junk** — Flag excessive gridlines, unnecessary gradients/glows on data marks, decorative 3D, redundant labels, or ornament that competes with data. Chart ink ratio should exceed 70% (data-ink / total ink).

## Output

```markdown
## UIS-09 Data visualization quality
- Chart integrity: ok | misleading — <issues>
- Colorblind safety: ok | at-risk — <confusable pairs>
- Responsive: ok | broken at <breakpoint> — <issues>
- Interactivity: ok | missing — <gaps>
- Chart junk: ok | excess — <items to remove>
- Overall: ship | revise — <top 1-2 fixes>
evidence: …
```
