# Explore & Understand Code Behavior

## Read business rules (feature SPECs first)

```text
@feature-spec status - <slug>
@feature-spec review - .work/features/<slug>/YYYYMMDD-SPEC.md
```

## Trace a specific calculation or behavior

Describe the scenario directly — the agent reads the code:

```text
explore how do invoice types NC and FAC behave when merged into an L2 record?
explore trace the calculate_total() path for a credit note with negative amounts
explore what happens when a null discount is passed to the pricing pipeline
```

## Find where a concept lives in the codebase

```text
explore find all places that reference "invoice_type" or "L2_record"
explore map the call chain from merge_invoice() to the final total
```

## Check architecture / design rationale

```text
@concept-run - MOD-01
@process-router - how is the invoicing module structured?
```

## Orient yourself in the project

```text
@session-control status
@process-router - how do I understand this module?
```
