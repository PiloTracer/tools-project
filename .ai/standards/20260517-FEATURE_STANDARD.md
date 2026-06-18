# Feature Standard — template

**Status:** Customize for your repo, then binding once code lands.
**Scope:** every code-shaped change large enough to be called a "feature". Bug fixes follow `.cursorrules` § Verification; they do not need this full lifecycle unless they change invariants.

---

## 1. What counts as a "feature"

A feature is any unit of work that:

- Adds, modifies, or removes a user-visible capability, **or**
- Changes a domain invariant, **or**
- Adds a new bounded-context module, public port, or persisted table, **or**
- Modifies behaviour covered by a high-risk SPEC (security, payments, compliance — list in threat model).

Anything else is a maintenance change.

## 2. Lifecycle

```
Proposal → Spec → Implementation → Release notes → Archive
```

| Stage | Required artifact | Gate |
|-------|------------------|------|
| 1. Proposal | Issue tracker item or `.work/plans/proposals/YYYYMMDD-<slug>.md` | Tech lead acks scope |
| 2. Spec | `.work/features/<slug>/YYYYMMDD-SPEC.md` (§3 template) | Reviewed; ≥2 reviewers if threat model flags the area |
| 3. Implementation | Code, tests, migrations, observability | PR references SPEC; passes `.cursorrules` gates |
| 4. Release notes | `.work/features/<slug>/CHANGELOG.md` + `HANDOFF.md` if session-relevant | Deployed through your environments |
| 5. Archive | SPEC frozen; amendments as sibling `*-amendment-NN.md` files | In production |

## 3. SPEC template (mandatory sections)

```markdown
# <Feature Name> — Feature SPEC

**Status:** Draft | Approved | Implemented | Superseded
**Owner:** <role>
**ADRs referenced:** <list>
**Related plans:** <list>

## 1. Purpose
## 2. In scope / Out of scope
## 3. Domain language
## 4. Behavioural spec
## 5. Data model
## 6. APIs
## 7. Invariants
## 8. Error model
## 9. Observability
## 10. Security and privacy
## 11. Test plan
## 12. Rollout and rollback
## 13. Open questions
## 14. Implementation map (optional — brownfield / locate-ability)
## 15. Concept / NFR registry
```

**§14 Implementation map** — list primary code paths so `@plan-verify coverage` and agents can find files without tree walks. Not a substitute for R1… behavioural rules. Use for cross-cutting surfaces (shell, layout, analytics dashboards) and brownfield adoption.

**§15 Concept / NFR registry** — one row per MOD-01…MOD-06 (`Applies` yes/no + reason). Required before **Approved** (see `feature-spec` skill).

```markdown
## 14. Implementation map (optional)
| Layer | Paths |
|-------|-------|
| frontend | `dashboard/src/pages/...` |
| backend | `apis/src/...` |
```

```markdown
## 15. Concept / NFR registry
| Concept id | Applies | Notes |
|------------|---------|-------|
| MOD-06 | yes | … |
```

## 4. SPEC quality bar

- Every behavioural rule numbered (R1, R2, …) for traceability in tests and PRs.
- Out of scope is explicit.
- External contracts cite integration mirror paths or OpenAPI ids.

## 5. PR requirements

- Title or body links the SPEC path.
- Migration scripts listed when schema changes.
- Observability hooks listed when new routes or jobs are added.

## 6. Amendments

- Never rewrite a merged SPEC; add `YYYYMMDD-SPEC-amendment-NN.md` and update status on the original.

## 7. Exceptions

- Emergency production fixes: document in `HANDOFF.md` and backfill SPEC within one sprint unless owner waives.

## 8. Directory changes

- New top-level directory → ADR + update DIRECTORY_MAP.

## 9. Integration with Agent OS skills

| Action | Skill |
|--------|-------|
| Create SPEC | `@feature-spec create - <slug>` |
| Review SPEC | `@feature-spec review - <path>` |
| Implement | `@code-implementation start` / `continue` |
| Verify milestone | `@code-verify milestone` |
| Map code surfaces to registry | `@plan-verify coverage` |
| Close registry gaps | `@plan-repair repair - from coverage` |
