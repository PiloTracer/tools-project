# Repair & Fix Code

## Fix verifier findings

```text
@code-repair repair - from uncommitted
@code-repair repair - from milestone
@code-repair repair - from last
@code-repair repair - from migration
```

## Fix a specific problem (free text)

```text
@code-repair repair - custom - fix the race condition in the payment webhook handler
@code-repair repair - custom - resolve the N+1 query on the user dashboard page
@code-repair repair - custom - add missing input validation to the registration form
@code-repair repair - custom - fix all TypeScript strict mode errors in the services layer
```

## Recover from test / lint / type-check failure

```text
@code-verify uncommitted
@code-repair repair - from uncommitted
@code-verify uncommitted
```

## Fix plan drift or broken NEXT.md

```text
@plan-verify alignment
@plan-repair repair - from alignment
@code-implementation plan - M1
```

## Fix SPEC review findings

```text
@code-repair repair - from feature-spec - .work/specs/password-reset.md
```

## AI-assisted session check

```text
@concept-run - MOD-06
```
