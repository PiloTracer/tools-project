# Greenfield Start — New UI Project From Scratch

## Bootstrap the workspace

```text
@ui-bootstrap init merge-cursorrules
@ui-style-stack set - tailwind
```

## Choose approach & build foundation

```text
@ui-project-approach - B2B SaaS dashboard with sidebar nav
@ui-design-foundation greenfield
@ui-design-foundation probe
@ui-design-foundation certify screen-spec-ready
```

## Create screen specs

```text
@ui-screen-spec create - dashboard-home
@ui-screen-spec create - settings-billing
@ui-screen-spec create - user-profile
@ui-screen-spec status
```

## Init design system

```text
@ui-design-system init
```

## Build first milestone

```text
@ui-component-build plan - S0
@ui-component-build start
@ui-component-build continue - 1
@ui-component-build continue - until complete
@ui-component-build complete
```

## For analytical dashboards — full chart-aware flow

```text
# Start with analytical archetype
@ui-project-approach - analytical dashboard with revenue trends and user growth charts
@ui-design-foundation greenfield
@ui-design-foundation certify screen-spec-ready

# Select chart library in foundation doc 03 (Recharts / Nivo / Vega-Lite / Tremor / …)
# Add chart tokens to token file (categorical palette, semantic colors, axis, tooltip)

# Create SPEC with §14 data visualization section
@ui-screen-spec create - dashboard-analytics
@ui-screen-spec create - reports

# Build with chart components
@ui-component-build plan - S0
@ui-component-build start

# Verify with data viz quality check
@ui-concept-run - UIS-09
@ui-component-build complete
```
