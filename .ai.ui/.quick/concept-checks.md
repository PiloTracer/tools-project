# Concept Checks — Running UIS Prompts

## List available concepts

```text
@ui-concept-run list
```

## Check status (pending UIS rows in active milestone)

```text
@ui-concept-run status
```

## Run individual UIS checks

```text
@ui-concept-run - UIS-01     # Visual hierarchy
@ui-concept-run - UIS-02     # Responsive layout
@ui-concept-run - UIS-03     # Motion design
@ui-concept-run - UIS-04     # Color contrast
@ui-concept-run - UIS-05     # Interaction patterns
@ui-concept-run - UIS-06     # AI visual quality (required before complete)
@ui-concept-run - UIS-07     # Surface/control craft (required when tier >= refined)
@ui-concept-run - UIS-08     # Intuitive UX (required before ship)
@ui-concept-run - UIS-09     # Data visualization quality (required for analytical dashboards)
```

## Run full pre-ship sweep

```text
@ui-concept-run - UIS-01
@ui-concept-run - UIS-06
@ui-concept-run - UIS-07
@ui-concept-run - UIS-08
@ui-concept-run - UIS-09
@ui-concept-run status
```

## Output destinations

| Check | Output goes to |
|-------|---------------|
| During SPEC authoring | Screen SPEC §12 |
| During build | `NEXT_UI.md` › UIS registry |
| Before ship | PR, verify report, NEXT_UI |
