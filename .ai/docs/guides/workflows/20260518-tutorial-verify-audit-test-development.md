# Tutorial - verify, audit, and test in development

**Doc type:** Quality gate tutorial (portable).  
**Skills:** `code-implementation` (**task gate** + **complete**) · `code-verify` (**milestone** / **uncommitted** / **last**); optional `session-control` for handoff.  
**Tests:** Must match your stack; examples below use commands from `.cursorrules` (`REPLACE:TEST_COMMAND`, etc.).

---

## 1. Three layers of “check”

| Layer | When | Skill | Owner |
|-------|------|-------|-------|
| **Task gate** | After **each** task | `code-implementation` | Implementer - automated commands + manual diff review |
| **Verify** | Pre-commit, post-push, before milestone complete | `code-verify` | Implementer + reviewer; matrix in **milestone** mode |
| **Audit** | Periodic / release | Human or SRE | Security scan, dependency audit (outside skills) |

---

## 2. Task gate (every task)

Per `code-implementation` **Task gate** table (adapt names):

1. **Context unit tests** - fast feedback for the package you touched.  
2. **Full suite smoke** - `pytest` (or `npm test`) for regressions.  
3. **Lint** - `ruff check src/ tests/` (or project equivalent).  
4. **Type check** - `pyright src/ tests/` / `tsc` (project chooses).  
5. **Secrets scan** on `git diff` (same rules as `code-verify` S1).  
6. **Protected files** - no `.cursorrules` §Protected Files paths without owner approval (`code-verify` S5).  
7. **Scope** - `git diff --name-only` ⊆ task file list.  
8. **Manual:** observability fields, concept prompts when AI/multi-boundary (per your rules).

**Rule:** Never mark `done` until **exit code 0** (or documented baseline waiver).

---

## 3. Verify (`code-verify`)

| Mode | Invoke | Purpose |
|------|--------|---------|
| **Milestone** | `@code-verify milestone` | Plan + SPEC matrix before `@code-implementation complete` |
| **Uncommitted** | `@code-verify uncommitted` | Diff-only audit before commit |
| **Last** | `@code-verify last` | Audit last commit or push (whichever was later) |

**Milestone flow:**

1. Run `@code-verify milestone`.  
2. Skill gathers: plan milestone, SPECs, ADRs, `git diff`.  
3. Fill **check matrix** - especially **FR coverage**, **SPEC rules**, **Test coverage**, **Observability**, **Concept registry**.  
4. Optional **Cross-LLM** second model.  
5. Verdict **pass** → proceed to `complete`. **fail** → file issues or fix in `continue`.

Legacy `@code-implementation verify` → route to `@code-verify milestone`.

---

## 4. Local / dev environment

1. Start dependencies (here: `docker compose up` for API + DB + Redis).  
2. Run validation commands from `{ITERATION_CARRIER}` **Validation steps** verbatim.  
3. Manual **curl** or UI smoke for routes you changed.

---

## 5. Audit extras (optional)

- **Dependency audit:** `pip-audit`, `npm audit` - frequency per security policy.  
- **Threat model diff:** when auth or tenant boundaries move - link `{THREAT_MODEL}` if present.  
- **Performance:** p95 budgets from plan NFR - measure with load tool when relevant.

---

## 6. Evidence discipline

Paste **short** excerpts of command output into PR or `{HANDOFF}` for failures; never paste secrets. Use `{EVIDENCE_TAGS}` on numeric claims.

---

## 7. Related

- [Testing in workflow](20260518-guide-testing-and-test-suite-in-workflow.md) - where unit vs integration tests live in process.  
- [Request new test](20260518-tutorial-request-new-test.md).  
- [Request tests for a feature](20260518-tutorial-request-test-feature-module.md).
