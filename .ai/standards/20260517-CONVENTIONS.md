# Code Conventions — template

> **Agent OS ships this file as a template.** Copy/rename per `.cursorrules` `REPLACE:CONVENTIONS_FILE`, replace all `REPLACE:` tokens, then treat as binding.

**Status:** Customize for your repo, then binding once code lands.
**Bootstrap:** Copy to `.ai/standards/YYYYMMDD-CONVENTIONS.md`, replace `REPLACE:` tokens, link from `.cursorrules`.

Pairs with: foundation architecture doc, `REPLACE:TECH_STACK_DOC`, ADRs under `.work/decisions/`.

---

## 1. Language and tooling baselines

| Surface | Tooling | Notes |
|---------|---------|-------|
| `REPLACE:PRIMARY_LANGUAGE` | `REPLACE:LINT`, `REPLACE:TYPECHECK`, `REPLACE:TEST_RUNNER` | Mandatory on every PR per `.cursorrules` |
| `REPLACE:SECONDARY_LANGUAGE` | (if any) | Same bar as primary |
| SQL | Idempotent numbered scripts under `REPLACE:MIGRATIONS_DIR` | No inline DDL in application code paths |
| Shell | POSIX `sh` or `bash` with `set -euo pipefail` | `shellcheck` in CI when scripts are committed |

## 2. Type discipline

- Enforce strict typing on all production code (language-appropriate: `pyright --strict`, `tsc --noEmit`, etc.).
- DTOs at boundaries (HTTP, queue, persistence); domain types separate from transport models where the stack supports it.

## 3. Naming

- Follow language idioms (`snake_case` / `camelCase` / `PascalCase` per ecosystem).
- **Platform layer:** shared code in `REPLACE:PLATFORM_PACKAGE` at `REPLACE:PLATFORM_PATH` — choose an import name that does not shadow stdlib modules.
- HTTP routes: `kebab-case`, plural nouns, no verbs in path segments unless using an approved action suffix pattern (see api-style-guide).
- DB tables: `snake_case`, plural; prefix or schema per bounded context if the team uses prefixes.
- Dated docs under `.ai/` and `.work/`: `YYYYMMDD-` prefix per `.cursorrules`.

## 4. Money, quantities, and regulated fields

*Include this section only if the domain handles money or regulated identifiers.*

- No binary floats for money — use decimal types end-to-end.
- Document rounding, scale, and presentation rules in the feature SPEC and here.
- External format constraints (XSD, ISO 20022, etc.) must cite the integration mirror, not memory.

## 5. Time

- Store UTC in persistence; expose ISO-8601 in APIs unless a jurisdiction requires a fixed offset — document in SPEC + here.
- Provide a single clock helper in the platform layer for testability.

## 6. Errors

- Map external provider errors to a small set of domain errors; preserve correlation ids and safe detail for operators.
- HTTP APIs use RFC 7807 Problem Details (see api-style-guide).

## 7. Logging and secrets

- Structured logs; no secrets, tokens, or raw PII in log lines.
- Redaction helper in platform layer for the rare structured log of sensitive payloads.

## 8. Module boundaries

- Bounded contexts do not import each other's `infrastructure/` or `http/` layers.
- Cross-context integration via `ports/` and events only.

## 9. Migrations

Binding policy: `.cursorrules` § **Migration policy**. Summary:

- Scripts: `NNN_snake_case.sql`, idempotent; runner executes in order on **every application startup** (before traffic) or via `@db-migration` for create/verify in dev.
- After create/change: `@db-migration verify` (double-run) before claiming done.
- After stack start: confirm runner logs and spot-check schema/data as needed for the change.
- Exceptions (one-off, destructive, non-numbered, manual hotfix, outside the runner): **human approval in the same message**; agents do not execute.
- Test DB ad-hoc DML: **human approval**; prefer mocks/fixtures (see `.cursorrules` § Test Data).
- Cross-context DDL requires extra review per `.cursorrules`.

## 10. Performance budgets

*Set per route or use case; example placeholders:*

| Class | Budget |
|-------|--------|
| Hot read API | REPLACE:P95_READ_MS ms p95 server-side |
| Hot write API | REPLACE:P95_WRITE_MS ms p95 server-side |
| Outbound integration | REPLACE:P95_OUTBOUND_MS ms p95 (excludes vendor SLA) |

## 11. Review requirements

- ≥1 reviewer for application code.
- ≥2 reviewers (one security-tagged) for auth, secrets, cross-context migrations, and high-risk domains defined in the threat model.
