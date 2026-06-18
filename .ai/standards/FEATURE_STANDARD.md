# Feature SPEC standard

**Brownfield synthesis 2026-06-18:** Minimal FEATURE_STANDARD for formal feature specs.

## SPEC template (mandatory H2 headings)

Each feature SPEC must contain these sections in order:

| # | Section | Required | Description |
|---|---------|----------|-------------|
| 1 | **Purpose** | Yes | One-paragraph: what and why |
| 2 | **Out of scope** | Yes | Explicitly excluded to avoid scope creep |
| 3 | **Functional requirements** | Yes | Numbered FRs (FR-1, FR-2…) |
| 4 | **Non-functional requirements** | Yes | Numbered NFRs (NFR-1, NFR-2…) |
| 5 | **Entity / data model** | Yes | New tables, columns, relationships |
| 6 | **API surface** | Yes | Routes, methods, payloads (or "none") |
| 7 | **UI / UX** | Yes | Screens, states, empty/loading/error |
| 8 | **Permissions / roles** | Yes | Who can do what |
| 9 | **Integration points** | Yes | Other systems, services, data sources |
| 10 | **Dependencies** | Yes | Prerequisites (other SPECs, ADRs, infrastructure) |
| 11 | **Open questions** | Yes | Undecided items needing owner input |
| 12 | **Test plan** | Yes | How to verify: unit, integration, manual |
| 13 | **Migration / rollout** | Yes | DB migration, feature flags, backward compat |
| 14 | **Implementation map** | If applicable | Primary file paths for each FR |
| 15 | **Concept / NFR registry** | Yes before **Approved** | One row per MOD concept: applies yes/no + reason |

## Status lifecycle

```
Draft → Review → Approved → Implemented
```

- **Draft:** Being written, not ready for review
- **Review:** Under review per checklist
- **Approved:** Immutable — changes go in amendment files
- **Implemented:** Code matches SPEC

## Anti-patterns

- Editing an Approved SPEC in place (use `YYYYMMDD-SPEC-amendment-NN-<slug>.md`)
- Skipping §15 for "small" features
- Empty §2 Out of scope
- Writing code before SPEC is Approved
