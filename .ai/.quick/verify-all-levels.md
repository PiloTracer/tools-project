# Verify Everything — Code & Plans

## Pre-commit check

```text
@code-verify uncommitted
```

## Post-commit / push check

```text
@code-verify last
```

## Milestone completion check

```text
@code-verify milestone
```

## Plan integrity checks

```text
@plan-verify foundation
@plan-verify master
@plan-verify alignment
@plan-verify coverage
```

## Open-language verification (free text)

```text
@code-verify audit the payment module against its SPEC and run all task gates
@code-verify check the recent migration for schema safety and a rollback plan
@plan-verify check if NEXT.md matches what was actually built in this iteration
```

## Status check (read-only, no file changes)

```text
@code-verify status
@plan-verify status
@plan-master status
@session-control status
```

## Concept / architecture check

```text
@concept-run list
@concept-run - MOD-01
@concept-run - MOD-06
```
