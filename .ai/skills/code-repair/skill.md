---
name: code-repair
description: >-
  Remediate failures from code-verify, db-migration verify, feature-spec review,
  or open-language fix requests. Maps free text to implementation framework
  (SPECs, CONVENTIONS, NEXT, concepts); re-runs originating verifier before pass.
  Use code-repair repair - from …, repair - custom - …, or natural-language fixes.
---

# code-repair

Remediation layer for the implementation workflow. **Implements fixes**; does not replace detection (`code-verify`) or iteration planning (`code-implementation`).

**Pairs with:** `code-verify` (findings source + mandatory re-verify), `code-implementation` (task gate + post-fix re-gate), `db-migration`, `feature-spec`, `concept-run`, `.cursorrules`, `.ai/standards/*CONVENTIONS*`, `.ai/standards/*FEATURE_STANDARD*`.

**Canonical path:** `.ai/skills/code-repair/skill.md` · **Invocation examples:** `reference.md`

**Registry:** [`.ai/skills/SKILL_DEPENDENCIES.md`](../SKILL_DEPENDENCIES.md).

**Hard rules:**

- **Findings in, evidence out.** Start from a numbered findings table (prior verifier report in chat, run the source verifier now, or decompose a custom brief). No code changes without documented F* rows.
- **Re-verify mandatory.** After repairs, re-run the **same** upstream check that produced the findings (see [R4](#r4--re-verify-mandatory)). Claim **repaired** only when that check passes (or **pass with gaps** only for documented waivers).
- **Standards-bound.** Apply `.cursorrules`, CONVENTIONS, FEATURE_STANDARD, relevant SPECs, and `.ai/concepts/README.md` § Trigger table on every fix diff. AI-assisted by default; MOD-06 required when agent-authored code changes unless **`human-only`** in the same message.
- **Scope discipline.** Edit only paths tied to findings or an explicit user file list. Out-of-scope expansion requires user approval in the same message.
- **Schema via db-migration.** No inline DDL. Follow `.cursorrules` § **Migration policy**. Mass backfills forbidden; test DB ad-hoc DML requires human approval.
- **Protected files / secrets.** Stop on `code-verify` S1/S5 failures; do not work around without owner approval in HANDOFF or the same user message.
- **Does not own HANDOFF/NEXT** unless the user explicitly asks (route bookends to `session-control`). May update task `Notes`, `UNKNOWNS.md`, and concept registry rows.
- Every **repair** mode ends with a **Completion checklist** - each item `pass` | `fail` | `skip` with evidence.

---

## Parse invocation

Normalize to **mode** + optional **source** or **brief**. Use ASCII hyphen **`-`** between tokens.

| User says | Mode | Action |
|-----------|------|--------|
| `@code-repair` | repair | [Repair protocol](#repair-protocol) - infer source (see default below) |
| `@code-repair` **repair** | repair | Same |
| `@code-repair` **repair** - **from** **uncommitted** | repair | Findings from `@code-verify uncommitted` (run if no fresh report) |
| `@code-repair` **repair** - **from** **milestone** | repair | Findings from `@code-verify milestone` |
| `@code-repair` **repair** - **from** **last** | repair | Findings from `@code-verify last` |
| `@code-repair` **repair** - **from** **migration** | repair | Findings from `@db-migration verify` |
| `@code-repair` **repair** - **from** **feature-spec** - \<path\> | repair | Findings from `@feature-spec review - <path>` |
| `@code-repair` **repair** - **custom** - \<brief\> | repair | User brief → findings table → fix → targeted re-verify |
| `@code-repair` **fix** - … | repair | Alias for **repair** |
| `@code-repair` **status** | status | [Status protocol](#status-protocol) - read-only |

**Open language examples (map to rows above):**

```text
@code-repair - fix the lint errors in apis/src/foo.py
@code-repair repair - custom - add test for SPEC R3 edge case in identity module
@code-repair - tests failed on the payment webhook handler
@code-repair fix verify findings from the last commit
```

**Free request → implementation alignment:** When findings come from **open language** (`repair - custom - …`, goal text after `-`, or implicit source resolution with no verifier report in chat), run **[R0-free](#r0-free---implementation-alignment-free-requests-only)** before triage. The map feeds F* rows (add **Implementation ref** column) and constrains R2/R3 to framework-consistent fixes.

**Legacy / colloquial:** `remediate` → **repair**; `audit` as source → **from uncommitted** (same alias as `code-verify`).

**Default source when omitted:**

1. If the current chat contains a **fail** report from `@code-verify` or `@db-migration verify` in the last 3 assistant turns → use that mode.
2. Else if working tree dirty → **from uncommitted**.
3. Else if `.work/plans/NEXT.md` has valid `## Current iteration` → **from milestone**.
4. Else if user message describes a code/test/lint fix without naming source → **custom** (run R0-free).
5. Else ask once: **Q:** Which findings should I repair? (paste report, `from uncommitted`, `from migration`, or `custom - …`)

When invocation is explicit (`repair - from milestone`, `from uncommitted`, …), skip R0-free; record `**Request:** explicit source`.

---

## Repair protocol

### R0 - Findings intake (mandatory)

Build a **Findings table** before editing:

| ID | Source | Severity | Finding | Affected paths | Fix strategy | Implementation ref |
|----|--------|----------|---------|----------------|--------------|---------------------|
| F1 | code-verify uncommitted | fail | … | … | code / config / owner | `—` (verify-sourced) |

**Implementation ref** — populate for **open language** / **custom** / inferred fixes; may be `—` when rows come from `@code-verify`, `@db-migration verify`, or `@feature-spec review` reports. Must cite at least one: SPEC rule (R{n}), task `M{N}-T{N}`, `.cursorrules` section, CONVENTIONS/FEATURE_STANDARD, concept MOD id, `{MASTER_PLAN}` §19, migration policy, or HANDOFF waiver.

**Obtain findings by:**

1. **Chat report** - parse the latest verifier output in the session, or
2. **Run source now** - invoke the matching skill (see [Source → re-verify map](#r4--re-verify-mandatory)), or
3. **Custom brief / open language** - run [R0-free](#r0-free---implementation-alignment-free-requests-only), then decompose into F* rows with explicit paths.

If there are **no fixable findings** and the tree is clean after optional source run → stop with verdict **nothing to repair**; suggest `@code-verify uncommitted` or `@session-control status`.

### R0-free - Implementation alignment (free requests only)

**When:** Findings from **custom** brief, open-language message, or goal text after `-` without a verifier report in the last 3 turns. **Skip** when all F* rows come from `@code-verify`, `@db-migration verify`, or `@feature-spec review`.

Produce an **Implementation alignment map** before filing F* rows:

```markdown
### Free request → Implementation alignment

**Request:** <one-line paraphrase>

| Aspect | Framework component | Artifact / gate | Action |
|--------|---------------------|-------------------|--------|
| <phrase from request> | SPEC rule | `.work/features/<slug>/*-SPEC.md` R{n} | Implement / test |
| <…> | Iteration task | `NEXT.md` M{N}-T{n} | Scope / Notes |
| <…> | CONVENTIONS | `.ai/standards/*CONVENTIONS*` | Naming / layout |
| <…> | FEATURE_STANDARD | `.ai/standards/*FEATURE_STANDARD*` | Test plan shape |
| <…> | Migration policy | `.cursorrules` § Database | `@db-migration create` if schema |
| <…> | MOD-06 | `.ai/concepts/` | Required for agent-authored fix |
| <…> | MOD-01 | `{BOUNDARY_MAP}` / DIRECTORY_MAP | Cross-boundary check |
| <…> | Task gate | `code-implementation` § Task gate | tests/lint/type after fix |
| <…> | Master plan FR | `{MASTER_PLAN}` §19 / §3–4 | Traceability |
```

**Rules:**

- Minimum one row per distinct aspect; label probabilistic mappings **Inference**.
- Redirect plan-only gaps to `@plan-repair` / `@plan-master revise` in triage — do not fix in code-repair.
- Freeze map before F* triage; update if new connections appear.

**Triage each row** (annotate in report):

| Disposition | Action |
|-------------|--------|
| **fix-now** | Agent resolves under standards |
| **owner** | Log in `.work/plans/UNKNOWNS.md` or HANDOFF § Open owner actions; do not claim pass |
| **waiver** | Only with HANDOFF or same-message user approval; cite in report |
| **redirect** | Wrong layer (plan docs → `@plan-repair` / `@plan-master revise`; missing iteration → `@code-implementation plan - M{N}`) |

If **>50%** of rows are **owner** and the user did not ask for documentation-only → stop and list owner actions.

### R1 - Context load (mandatory)

Read before implementing fixes. Record `pass` only after reading.

| # | File (repo-root path) | When |
|---|------------------------|------|
| 1 | `.cursorrules` | always |
| 2 | `.work/context/HANDOFF.md` | always |
| 3 | `.work/plans/NEXT.md` § Current iteration | iteration-scoped findings |
| 4 | `.ai/standards/*CONVENTIONS*` | app code or tests touched |
| 5 | `.ai/standards/*FEATURE_STANDARD*` | app code or tests touched |
| 6 | Relevant `.work/features/<slug>/*-SPEC.md` | per bounded context in F* paths |
| 7 | `.ai/concepts/README.md` § Trigger table | architecture, boundaries, AI-assisted diff |
| 8 | `.work/plans/UNKNOWNS.md` | open U* rows referenced by findings |

State a short **assumption ledger** (Confirmed / Inference / Unverified) when the fix depends on non-obvious behavior.

### R2 - Plan fixes (no code yet)

Output a **Repair plan** (≤15 lines): order of F* ids, files to touch, whether `@db-migration create` or `@concept-run` is required, and what will be re-run in R4.

**Fix order:** secrets/protected → scope blockers → tests/lint/type → migration idempotency → SPEC/concept gaps → docs-only.

### R3 - Apply fixes

- **Minimal diff** - smallest change that resolves the finding.
- **Per finding** - one logical commit worth of change; note in report if split is needed.
- **Schema** - `@db-migration create` / amend script; never inline DDL in application code.
- **Concepts** - `@concept-run - MOD-06` when agent fixes application code; MOD-01 when diff crosses hard module boundaries per `{BOUNDARY_MAP}`.
- **TODO/FIXME** - promote to `UNKNOWNS.md` or task `Notes` before claiming F* fixed.
- **Stop** if a fix requires protected file edit without approval.

### R4 - Re-verify (mandatory)

| Repair source (invocation) | Re-run after fixes |
|----------------------------|-------------------|
| **from uncommitted** | `@code-verify uncommitted` |
| **from milestone** | `@code-verify milestone` |
| **from last** | `@code-verify last` |
| **from migration** | `@db-migration verify` + Migration policy §3 startup log check when runner wiring may have changed |
| **from feature-spec** - \<path\> | `@feature-spec review - <path>` |
| **custom** | At minimum `@code-verify uncommitted` if tree dirty; plus any checks named in the brief |

**Iteration tasks touched:** also run the mechanical subset of `code-implementation` § Task gate (tests, lint, type, scope, secrets, warnings in touched files) for each affected task id. Record:

```text
Task M{N}-T{N} re-gated <YYYY-MM-DD> after code-repair: pass | fail (<reason>)
```

**Verdict:**

| Verdict | Meaning |
|---------|---------|
| **repaired** | Originating verifier **pass**; task re-gates **pass** where applicable |
| **partial** | Some F* fixed; re-verify still **fail** or owner items remain |
| **failed** | Could not fix; re-verify **fail** |
| **nothing to repair** | No findings / clean tree |

### R5 - Repair report (mandatory output)

```markdown
## code-repair - <source> - <verdict>

**Date:** <ISO> · **Branch:** <branch> · **Tree:** clean | dirty
<when open language / custom — insert ### Free request → Implementation alignment; else: **Request:** explicit source>

### Findings
| ID | Disposition | Status | Evidence |
|----|-------------|--------|----------|
| F1 | fix-now | fixed | re-verify uncommitted: pass |

### Completion checklist
| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Findings table (R0) | pass/fail | |
| 1b | R0-free map (open language only) | pass/skip | |
| 2 | Context load (R1) | pass/fail | |
| 3 | Repair plan shown (R2) | pass/fail | |
| 4 | Standards / SPEC / concepts applied | pass/fail | |
| 5 | Fixes minimal and in scope | pass/fail | |
| 6 | Originating verifier re-run (R4) | pass/fail | |
| 7 | Task re-gate (if iteration) | pass/skip | |
| 8 | Residual risks in Notes or UNKNOWNS | pass | |

### Remaining / owner
<list or none>

### Next
@code-implementation continue | @code-verify milestone | @session-control close
```

---

## Status protocol

Read-only. No fixes.

1. `git status -sb` · `git diff --stat`
2. `.work/plans/NEXT.md` - active iteration? blocked tasks?
3. Note last verifier mention in chat if visible; else "unknown - run code-verify first"

```markdown
## code-repair status

**Tree:** clean | dirty (<N> files)
**Iteration:** M{N} active | none
**Suggested repair:** @code-repair repair - from uncommitted | from milestone | custom - …
```

---

## Integration

| Skill | Relationship |
|-------|----------------|
| `code-verify` | **Upstream detector** - on **fail**, recommend `@code-repair repair - from <mode>`. Does not auto-invoke repair. |
| `code-implementation` | Batch-end sweep **fail** → `@code-repair repair - from uncommitted`. Shares task gate and post-fix re-gate semantics. |
| `db-migration` | **verify** fail → `@code-repair repair - from migration`. |
| `feature-spec` | **review** fail → `@code-repair repair - from feature-spec - <path>` (SPEC/doc fixes) or route code gaps to implementation. |
| `concept-run` | Run when repair diff triggers MOD rows per concept pack. |
| `session-control` | Optional after **repaired** before `close commit`. |

---

## Anti-patterns

- Claiming **repaired** without re-running the originating verifier
- Fixing without reading CONVENTIONS / FEATURE_STANDARD / relevant SPECs
- Expanding scope beyond F* rows without user approval
- Inline DDL instead of `@db-migration create`
- Skipping MOD-06 on agent-authored code fixes
- Marking owner/legal/vendor items as fixed in code
- Using **milestone** re-verify for a one-line typo when **uncommitted** suffices (heavy but allowed if user asked)
- Open-language repair without **R0-free** Implementation alignment map
- Plan-doc-only fixes in code-repair (redirect to `@plan-repair`)

---

## Project layout (convention)

Repair consumes artifacts under `.work/` and standards under `.ai/`. Path resolution: [`SKILL_DEPENDENCIES.md`](../SKILL_DEPENDENCIES.md) § Work tree path resolution.
