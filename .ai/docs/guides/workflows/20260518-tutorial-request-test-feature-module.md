# Tutorial - request tests for a **feature / module / bounded context**

**Doc type:** Scoped test request (portable).  
**Prerequisite:** Feature SPEC exists under `{FEATURE_SPEC_ROOT}` with **§12 Test plan** (or your template’s test section).

---

## 1. Map scope → test pyramid

| Scope | Typical test type | Directory pattern (example) |
|-------|-------------------|----------------------------|
| Single pure function | Unit | `tests/unit/<context>/` |
| Port + adapter | Contract | `tests/contract/<context>/` |
| API + DB | Integration | `tests/integration/<context>/` |
| Browser / full stack | E2E | `tests/e2e/` |
| Fiscal / external sandbox | Marked `sandbox` | separate job per policy |

Use your **CONVENTIONS** doc as source of truth for paths.

---

## 2. Use the SPEC as contract

1. Open feature SPEC **§4 Behavioural rules** - list R1… to cover.  
2. Open **§12 Test plan** - add rows: `Rule` | `Test type` | `Fixture` | `Owner` | `Status`.  
3. If SPEC is **Approved** and must not be edited in place → create **`SPEC-amendment-NN.md`** adding only test-plan rows.

---

## 3. Request to engineering (template)

```markdown
## Test coverage request - <Feature name>

**Bounded context / module:** <e.g. billing, identity>
**Priority:** P0 | P1
**Rules to cover:** R3, R7, R9 (cite SPEC)
**Existing tests:** <paths or "none">
**Gaps:** <bullet list>
**Suggested new files:** …
**Dependencies:** docker services …
**Out of scope:** …
```

---

## 4. Tie to `{ITERATION_CARRIER}`

- If implementation is **in flight** - append sub-tasks `M{n}-T{x}a` “Add tests for R…” per `code-implementation` migration-sub-task pattern (adapt for tests-only).  
- Else - schedule in next **`@code-implementation plan`** milestone.

---

## 5. Verify alignment

During `@code-verify milestone`, **SPEC rules** row should become **pass** only when each R* has a test or explicit **defer** with owner in `UNKNOWNS`.

---

## 6. Feature without SPEC yet

**Stop.** Write minimal SPEC or proposal first - testing requests without behaviour contract create garbage tests.
