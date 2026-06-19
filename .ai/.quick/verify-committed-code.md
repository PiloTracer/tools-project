# Verify Committed Code & Add Tests

## Audit first, then fix

```text
@code-verify last
@code-repair repair - from last
```

## Add tests directly

```text
@code-repair repair - custom - add unit tests for <feature>
@code-repair repair - custom - analyze and apply any valuable recommendations from "tmp/feedback.md"
```

