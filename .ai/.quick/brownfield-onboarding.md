# Brownfield Onboarding & Planning

## Audit the existing codebase

```text
@plan-verify brownfield
@plan-repair brownfield
@plan-verify brownfield
```

## Map code to feature coverage

```text
@plan-verify coverage
@plan-repair repair - from coverage
```

## Free-text feature intake in brownfield

```text
@feature-spec intake - add rate limiting to the existing API endpoints
@plan-repair repair - custom - map existing controllers to the new feature-spec
```

## Align existing code with standards

```text
@code-repair repair - custom - audit current codebase against CONVENTIONS and report gaps
@code-repair repair - custom - add missing error handling patterns from DIRECTORY_MAP
```

## Orient yourself

```text
@process-router - how do I start working with this existing repo?
@session-control status
```
