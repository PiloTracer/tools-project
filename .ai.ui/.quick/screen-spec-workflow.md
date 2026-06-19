# Screen SPEC Workflow — Intake, Create, Review, Amend

## Intake a free-text request (classify without writing)

```text
@ui-screen-spec intake - add a two-factor auth setup page with QR code and backup codes
@ui-screen-spec intake - the dashboard needs a new notifications panel
```

## Create a full SPEC

```text
@ui-screen-spec create - two-factor-setup
@ui-screen-spec create - notifications-panel
```

## Create dashboard SPEC with data viz section (§14)

```text
@ui-screen-spec create - dashboard-overview
# SPEC includes §14 Data visualization:
#   14a — Chart types, data source, interactions (tooltip, zoom, drill-down)
#   14b — Responsive per-chart sizing (grid cols at each breakpoint)
#   14c — Chart tokens from token file (categorical palette, axis, tooltip)
#   14d — Loading/empty/error/animation states per chart
#   14e — Data table fallback, aria-labels, color+pattern encoding
```

## Review and amend

```text
@ui-screen-spec review - two-factor-setup
@ui-screen-spec amend - two-factor-setup - add error state for expired QR codes
@ui-screen-spec amend - dashboard-overview - add spider radar chart to comparison section
```

## Check status

```text
@ui-screen-spec status
```
