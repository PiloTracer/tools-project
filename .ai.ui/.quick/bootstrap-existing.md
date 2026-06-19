# Bootstrap Existing Project — Add UI Design OS to a Codebase

## Scaffold UI workspace

```text
@ui-bootstrap init merge-cursorrules
```

## Probe existing UI to fill foundation gaps

```text
@ui-design-foundation probe
@ui-style-stack set - tailwind
@ui-design-foundation certify screen-spec-ready
```

## Intake existing screens as spec stubs

```text
@ui-screen-spec intake - we have a settings page with tabs and a profile form
@ui-screen-spec intake - the dashboard has a KPI row and a table
```

Then promote stubs to full SPECs:

```text
@ui-screen-spec create - settings
@ui-screen-spec create - dashboard
```

## If existing project has charts — bootstrap analytical path

```text
@ui-project-approach - analytical dashboard with existing charts
# Identify chart library already in use
# Add chart tokens to token file (or extract from existing theme)
@ui-screen-spec create - dashboard-analytics
@ui-concept-run - UIS-09
```

## Route questions

```text
@ui-process-router - how do I add specs for existing pages?
@ui-project-approach status
```
