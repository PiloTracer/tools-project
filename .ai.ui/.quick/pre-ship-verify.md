# Pre-Ship Verification — Verify Before You Ship

## Visual regression

```text
@ui-visual-verify milestone
@ui-visual-verify uncommitted
```

## Accessibility audit

```text
@ui-accessibility-audit milestone
@ui-accessibility-audit uncommitted
```

## Plan audit (probe coverage + traceability)

```text
@ui-plan-verify audit
@ui-plan-verify probe-coverage
@ui-plan-verify traceability
```

## Concept checks

```text
@ui-concept-run - UIS-06
@ui-concept-run - UIS-07
@ui-concept-run - UIS-08
@ui-concept-run - UIS-09    # if analytical dashboard
@ui-concept-run status
```

## Close milestone after all gates pass

```text
@ui-component-build complete
```
