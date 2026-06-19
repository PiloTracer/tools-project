# Add a Feature — Idea to Implementation

## Classify and route a feature idea (free text)

```text
@feature-spec intake - let users reset their password via email link
@feature-spec intake - add real-time notifications for order status changes
```

## Create a formal SPEC

```text
@feature-spec create - password-reset
@plan-master status
```

## Plan the milestone

```text
@code-implementation plan - M2
```

## Implement incrementally

```text
@code-implementation start
@code-implementation continue - 3
@code-implementation continue - until blocked
@code-implementation complete
```

## Cross-cutting feature

```text
@feature-spec intake - add audit logging to all mutations across the codebase
@concept-run - MOD-06
```

## Add tests for a feature

```text
@code-repair repair - custom - add unit tests for password-reset flow
@code-repair repair - custom - analyze and apply any valuable recommendations from "tmp/feedback.md"
```
