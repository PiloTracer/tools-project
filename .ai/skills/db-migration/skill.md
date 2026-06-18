---
name: db-migration
description: >-
  Create, run, and verify idempotent SQL migration scripts. No version table,
  no migration-chain conflicts - scripts are numbered, executed in order on
  every startup, and safe to re-run. Use when the user asks to create a migration,
  add a table/column/trigger/insert, run migrations, or check migration status.
  Replaces Alembic-style versioned migrations.
---

# db-migration

Manage database schema and data with **idempotent numbered SQL scripts** - no version table, no migration chain, no conflicts when environments diverge.

**Tool-agnostic** (Cursor, Claude Code, opencode, Codex). **DB-agnostic** at the concept level; implementation targets PostgreSQL 16+.

**Pairs with:** `CONVENTIONS` (§17), `DIRECTORY_MAP`, `.cursorrules` §"Schema Changes Ledger".

**Canonical path:** `.ai/skills/db-migration/skill.md` · **Invocation examples:** `reference.md`

**Hard rules:**

- **Every script is idempotent.** Re-running the same script N times produces the same result as running it once. No exceptions.
- **Scripts are append-only.** Add new numbered scripts. Never renumber, delete, or reorganize existing scripts.
- **No version table.** The runner does not track which scripts have been applied. Idempotency guarantees safety.
- **Order is explicit.** Scripts execute in alphanumeric order (`001_`, `002_`, …). Gaps are acceptable but discouraged.
- **One script per conceptual change.** Don't cram unrelated DDL into one file. Don't split one table across three files.
- **Stop on first error.** If a script fails, the runner halts. Fix the script, restart. No partial state.
- **Never embed secrets.** Migration scripts contain DDL/DML only. Credentials, keys, tokens live in environment variables or KMS.
- **Policy:** `.cursorrules` § **Migration policy** (startup runner, verify idempotency, verify applied, exceptions, test DB mutations) is canonical; this skill implements items 1–3.

---

## Parse invocation

Normalize the user message to **verb** + optional **target**.

| User says | Verb | Action |
|-----------|------|--------|
| `@db-migration` **init** | init | Bootstrap the full migration system into the project |
| `@db-migration` **implement** | init (alias) | Same as init |
| `@db-migration` **setup** | init (alias) | Same as init |
| `@db-migration` **bootstrap** | init (alias) | Same as init |
| `@db-migration` **create** - add users table | create | Produce a new numbered `.sql` script |
| `@db-migration` **add** column `email` to `users` | add | Append to `schema_changes.sql` or create a new script |
| `db-migration` **run** | run | Simulate/dry-run or execute all scripts |
| `db-migration` **status** | status | Read-only: list scripts, verify idempotency |
| `db-migration` **verify** | verify | Run each script twice and assert no errors |

**Aliases:** `implement`, `setup`, `bootstrap` → init.

---

## Step 0 - Pick a mode

| Mode | Action |
|------|--------|
| **init** | [Init protocol](#init-protocol) - bootstrap the migration system into the project: create directory, runner, initial scripts, wire into startup, remove Alembic if present |
| **create** | [Create protocol](#create-protocol) - write a new numbered migration script |
| **add** | [Add protocol](#add-protocol) - append DDL to an existing script or create one |
| **run** | [Run protocol](#run-protocol) - execute scripts against the database |
| **status** | [Status protocol](#status-protocol) - list scripts, check order, validate idempotency |
| **verify** | [Verify protocol](#verify-protocol) - run twice, confirm safe re-execution |

---

## Prerequisite gate (mutating modes)

**Applies to:** `create`, `add`, `run`, `verify`. Skipped for `init` (it builds the prerequisites) and `status` (read-only).

Before any of those modes touches a file or the database:

1. Check that `REPLACE:MIGRATIONS_DIR/001_init.sql` exists.
2. Check that `REPLACE:MIGRATION_RUNNER_PATH` exists.
3. If either is missing → **stop** with the [blocked-report shape](#blocked-report-shape):
   - **Required:** `db-migration init` already run (runner module + `001_init.sql` baseline)
   - **Detected:** `REPLACE:MIGRATIONS_DIR/001_init.sql` missing **and/or** `REPLACE:MIGRATION_RUNNER_PATH` missing
   - **Run first:** `@db-migration init`

This prevents silent failures where `create` writes a script into a non-existent directory or `run` cannot find the runner.

### Blocked-report shape

Per [SKILL_DEPENDENCIES.md § Blocked report shape](../SKILL_DEPENDENCIES.md#blocked-report-shape) - header: `## @db-migration <command> - blocked (prerequisite)`.

---

## Init protocol

Bootstraps the entire idempotent SQL migration system into a project. This mode **removes Alembic** (if present), creates the `migrations/` directory with initial scripts, writes the `migration_runner.py`, wires it into application startup, and updates all configuration files.

**Triggers:** `@db-migration init`, `@db-migration implement`, `@db-migration setup`, `@db-migration bootstrap`

### IB0 - Brownfield detection (mandatory before any write)

Before touching the migration system, inventory existing artifacts:

| Path | If exists |
|------|-----------|
| `REPLACE:MIGRATIONS_DIR/001_init.sql` | Mark as **existing - baseline** |
| `REPLACE:MIGRATIONS_DIR/` (with `*.sql` files) | Mark as **existing - populated** |
| `REPLACE:MIGRATION_RUNNER_PATH` | Mark as **existing - runner installed** |
| `alembic.ini` or `REPLACE:APP_ROOT/alembic/` | Mark as **existing - Alembic present (will be removed)** |

If **any** of the first three are present:

1. **Stop** - do not write.
2. Emit the brownfield summary:

```markdown
## @db-migration init - brownfield detected

The migration system is already initialized. Choose how to proceed:

| Existing | Path | Action choice |
|----------|------|---------------|
| {list every detected file} | … | keep / overwrite / abort |

### Choose one (reply in the same message)
- **`keep`** - run `@db-migration status` instead (read-only) and exit init
- **`overwrite-runner`** - replace `migration_runner.py` only (preserves your `*.sql` files)
- **`overwrite-all`** - replace runner + all `001`–`005` baseline files (destroys current content; **append-only scripts beyond `005_` are preserved**)
- **`abort`** - exit silently
```

3. On **`overwrite-all`**: require an extra `confirm-overwrite-all` token in the same message; otherwise treat as `abort`.
4. On **`keep`** / **`abort`**: exit; do not write.
5. On **`overwrite-runner`** or **`overwrite-all`**: proceed to I0; honor the choice when writing files.

**Anti-pattern:** silently overwriting a curated `001_init.sql` that already contains project-specific extensions and base tables. The brownfield gate exists to prevent exactly this.

### I0 - Detect the database dialect

1. Read `REPLACE:TECH_STACK_DOC` (stack document from `.cursorrules`). Look for the primary database.
2. If PostgreSQL → use **plpgsql**. All `DO $$ … END $$` blocks, `CREATE OR REPLACE FUNCTION`, `SERIAL`/`BIGSERIAL` types, `TIMESTAMPTZ`, `UUID`, `IF NOT EXISTS` (PG 9.6+ syntax).
3. If SQLite → use SQLite-compatible idempotent patterns (`CREATE TABLE IF NOT EXISTS`, no `DO $$` blocks, no stored procedures).
4. If MySQL/MariaDB → use `CREATE TABLE IF NOT EXISTS`, `CREATE PROCEDURE IF NOT EXISTS`, `SIGNAL` for conditional guards.
5. If not specified → default to **PostgreSQL / plpgsql**.
6. Record the detected dialect in the `001_init.sql` header comment.

### I1 - Remove Alembic (if present)

1. Delete `REPLACE:APP_ROOT/alembic/` (or equivalent) directory and all contents.
2. Delete `alembic.ini` from project root (if present).
3. Remove `alembic` from `pyproject.toml` dependencies.
4. Remove any `alembic upgrade head` commands from `Dockerfile.*`, `docker-compose.yml`, entrypoint scripts, CI configs.
5. Search the entire codebase for remaining `alembic` references and remove/update them.

### I2 - Create directory structure

```
REPLACE:MIGRATIONS_DIR/
├── 001_init.sql
├── 002_schema_changes.sql       ← empty ledger - ALTER TABLE changes go here
├── 003_triggers.sql             ← empty - CREATE OR REPLACE FUNCTION/TRIGGER
├── 004_inserts.sql              ← empty - idempotent INSERTs go here
└── 005_constraints.sql          ← empty - ADD CONSTRAINT IF NOT EXISTS
```

### I3 - Write `001_init.sql`

Header comment documenting the database dialect. Contents:

```sql
-- 001: Initial schema setup - PostgreSQL / plpgsql (idempotent)
-- Dialect detected from: `REPLACE:TECH_STACK_DOC` (stack document from `.cursorrules`) → PostgreSQL 16
-- Every statement is safe to re-run.

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Base schemas (for schema-per-tenant: create the public schema baseline)
-- Tenant schemas are created at provisioning time by provision_tenant.py
```

### I4 - Write `migration_runner.py`

Create `REPLACE:MIGRATION_RUNNER_PATH` using the reference implementation from `reference.md`. Adapt paths to the project's actual layout:
- `WORKDIR` → resolved from `pyproject.toml` or `Dockerfile` WORKDIR directive
- `MIGRATIONS_DIR` → `Path(__file__).resolve().parent.parent.parent / "migrations"`
- Use `asyncpg` or `psycopg` (async) per the project's SQLAlchemy configuration
- The runner is called on application startup before the HTTP server starts

### I5 - Wire into application startup

Update the application entrypoint (e.g. `REPLACE:APP_ENTRYPOINT`). Use the framework's startup hook to call `run_migrations(get_engine())` **before** the HTTP server accepts traffic.

**Reference code blocks** (FastAPI lifespan, deprecated `on_event`, schema-per-tenant loop): see `reference.md` § Application startup wiring. Adapt to the target framework (FastAPI, Starlette, Flask, custom) per the project's stack doc.

For schema-per-tenant: iterate tenants first, run migrations per schema.

### I6 - Update Docker entrypoint

Remove any `alembic upgrade head` or `sleep && alembic` lines. The migration runner is called from application code on startup - no separate init container needed (unless the project's architecture requires it).

### I7 - Update project configuration

1. **`pyproject.toml`:** Remove `alembic` dependency. No replacement needed (runner uses SQLAlchemy's `text()` execution - already a dependency).
2. **`REPLACE:TECH_STACK_DOC`:** Replace Alembic row with idempotent SQL scripts.
3. **`CONVENTIONS`:** Ensure §17 (Migration strategy) references this skill.
4. **`.cursorrules`:** Update Schema Changes Ledger section to point to `migrations/`.
5. **`DIRECTORY_MAP`:** Update to show `REPLACE:MIGRATIONS_DIR/` instead of `alembic/`.

### I8 - Init report (mandatory output)

```markdown
## db-migration init - <Project>

**Database:** PostgreSQL (plpgsql) · **Directory:** `REPLACE:MIGRATIONS_DIR/`

### Actions taken
| # | Action | Result |
|---|--------|--------|
| 1 | Alembic removed | <path or "not present"> |
| 2 | `migrations/` directory created | <path> |
| 3 | `001_init.sql` written | pass |
| 4 | `002_schema_changes.sql` created (empty) | pass |
| 5 | `003_triggers.sql` created (empty) | pass |
| 6 | `004_inserts.sql` created (empty) | pass |
| 7 | `005_constraints.sql` created (empty) | pass |
| 8 | `migration_runner.py` written | <path> |
| 9 | `main.py` wired with startup hook | pass |
| 10 | Docker entrypoint cleaned | pass/skip |
| 11 | `pyproject.toml` cleaned (Alembic removed) | pass/skip |
| 12 | `REPLACE:TECH_STACK_DOC` updated | pass |
| 13 | `.cursorrules` updated | pass |
| 14 | `DIRECTORY_MAP` updated | pass |

### Remaining manual steps
- Review `001_init.sql` - add any project-specific extensions, base tables, or default schemas.
- Test: `docker compose up` → check logs for `migration.runner.complete`.
- Run `@db-migration verify` to confirm idempotency.
```

---

## Create protocol

### C1 - Determine next script number

Scan `migrations/` (or the project's configured migrations directory). Find the highest numeric prefix. The new script gets that number + 1.

```
migrations/
├── 001_init.sql
├── 002_platform_audit_log.sql
├── 003_identity_users.sql
└── 004_  ← next script goes here
```

### C2 - Classify the change

| Change type | Script pattern | Naming |
|-------------|---------------|--------|
| New table | `CREATE TABLE IF NOT EXISTS` | `{NNN}_{context}_{table}.sql` |
| New bounded context | Multiple tables in one script | `{NNN}_{context}_init.sql` |
| Triggers/functions | `CREATE OR REPLACE FUNCTION/TRIGGER` | `{NNN}_triggers.sql` (append) or new numbered |
| Reference data | `INSERT … ON CONFLICT DO NOTHING` | `{NNN}_inserts.sql` (append) or new numbered |
| Constraints/indexes | `ALTER TABLE … ADD CONSTRAINT IF NOT EXISTS` | `{NNN}_constraints.sql` (append) or new numbered |
| Schema change (add column) | `ALTER TABLE … ADD COLUMN IF NOT EXISTS` | Append to latest `schema_changes` script or new numbered |

### C3 - Apply idempotency pattern

| Operation | Idempotent form |
|-----------|----------------|
| Create table | `CREATE TABLE IF NOT EXISTS {name} (…)` |
| Add column | `ALTER TABLE {t} ADD COLUMN IF NOT EXISTS {col} {type} {constraints}` |
| Drop column | Wrap in `DO $$ BEGIN IF EXISTS (…) THEN ALTER TABLE … DROP COLUMN …; END IF; END $$` (rare; prefer soft deprecation) |
| Add constraint | PG 9.6+: `ALTER TABLE {t} ADD CONSTRAINT IF NOT EXISTS`<br>Older PG: `DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE …) THEN ALTER TABLE …; END IF; END $$` |
| Create index | `CREATE INDEX IF NOT EXISTS {name} ON {t} (…)` |
| Create unique index | `CREATE UNIQUE INDEX IF NOT EXISTS {name} ON {t} (…)` |
| Create function | `CREATE OR REPLACE FUNCTION {name}(…) RETURNS … AS $$ … $$ LANGUAGE …` |
| Create trigger | `DROP TRIGGER IF EXISTS {name} ON {t}; CREATE TRIGGER {name} …` (DROP+CREATE is safer than CREATE OR REPLACE for triggers) |
| Create schema | `CREATE SCHEMA IF NOT EXISTS {name}` |
| Grant permission | `GRANT … TO …` (re-granting is idempotent) |
| Insert data | `INSERT INTO {t} (…) VALUES (…) ON CONFLICT (key) DO NOTHING`<br>Or: `INSERT INTO {t} (…) SELECT … WHERE NOT EXISTS (SELECT 1 FROM {t} WHERE …)` |
| Update data | `UPDATE {t} SET … WHERE … AND …` (targeted; produces same result on re-run) |
| Upsert data | `INSERT INTO {t} (…) VALUES (…) ON CONFLICT (key) DO UPDATE SET …` |
| Add RLS policy | `DROP POLICY IF EXISTS {name} ON {t}; CREATE POLICY {name} ON {t} …` |
| Add enum value | `ALTER TYPE {name} ADD VALUE IF NOT EXISTS '{value}'` (PG 9.6+) or `DO $$ BEGIN … EXCEPTION WHEN duplicate_object THEN … END $$` |

### C4 - Write the script

- Header comment: `-- {NNN}: {description} (idempotent)`
- Single transaction per script (PostgreSQL wraps DDL in implicit transactions; for multi-statement scripts, wrap in explicit `BEGIN … COMMIT` if atomicity is needed).
- One blank line between statements.
- Trailing newline.

### C5 - Register in DIRECTORY_MAP

If this script introduces a new directory or a new bounded-context module, update `{BOUNDARY_MAP}` / `.ai/standards/*DIRECTORY_MAP*` (path from `.cursorrules`).

### C6 - Output checklist

| # | Check | Result |
|---|-------|--------|
| 1 | Script numbered correctly (next in sequence) | pass |
| 2 | Every statement is idempotent | pass |
| 3 | Script matches the change type described | pass |
| 4 | No secrets in script | pass |
| 5 | DIRECTORY_MAP updated (if applicable) | pass/skip |
| 6 | **Idempotency double-run executed** (`@db-migration verify` against the new script, or `@db-migration run` twice in a row in a dev DB) | pass/fail/skip - skip allowed only when DB not reachable; record reason |

**Why row 6 is mandatory by default:** A script that fails on second run is not idempotent by definition - and silent failure on re-run produces drift the runner cannot detect (no version table). Verifying at create-time prevents shipping broken idempotency to other environments. Record the verify output (exit code + the runner's `migration.run` log line) as evidence in the create report.

---

## Add protocol

For small changes to **existing** structures (e.g., adding one column to an existing table):

1. Determine if the change belongs in an existing script (append to `schema_changes.sql`) or warrants a new numbered script.
2. **Guideline:** a new table, index, or constraint → new script. A single `ALTER TABLE ADD COLUMN` → append to the latest `schema_changes` script.
3. Apply the same idempotency pattern as [Create protocol](#c3--apply-idempotency-pattern).
4. Output the SQL block with the target script path.

---

## Run protocol

### R1 - Locate the runner

Find `REPLACE:MIGRATION_RUNNER_PATH` (or equivalent). If it doesn't exist, draft one before running scripts.

### R2 - Dry-run (optional but recommended)

For production/staging: run the migration runner in dry-run mode per `.cursorrules` (e.g. `docker compose exec REPLACE:SERVICE_API … --dry-run`).

### R3 - Execute

```bash
docker compose exec REPLACE:SERVICE_API bash -c "cd REPLACE:APP_WORKDIR && REPLACE:MIGRATION_RUN_CMD"
```

The runner:
1. Scans `migrations/` for `*.sql` files sorted alphanumerically.
2. Executes each against the configured database.
3. Logs: `{"event": "migration.run", "script": "003_identity_users.sql", "duration_ms": 45, "result": "ok"}`.
4. Stops on first error. Container exits with code 1.

### R4 - Verify idempotency

Run the runner a **second time**. All scripts should produce zero errors (they're idempotent). If any script fails on re-run, it's not truly idempotent - fix it.

### R5 - Output checklist

| # | Check | Result |
|---|-------|--------|
| 1 | All scripts executed without error | pass/fail |
| 2 | Re-run produced no errors (idempotency verified) | pass/fail |
| 3 | Runner logs captured | pass |
| 4 | Application health check passes after migrations | pass |

---

## Status protocol

Read-only. No writes to scripts or database.

1. List all scripts in `migrations/` by name and line count.
2. Check numbering: no gaps that skip logical order (gaps after deleted scripts are acceptable if intentional).
3. Spot-check 3 random scripts for idempotent patterns (`IF NOT EXISTS`, `CREATE OR REPLACE`, `ON CONFLICT DO NOTHING`).
4. Check `git log --oneline migrations/` for the last 5 changes.
5. Output:

```markdown
## Migration status

**Directory:** `migrations/` · **Scripts:** <N> · **Last change:** <date> by <commit>

### Script inventory
| # | Name | Lines | Last modified |
|---|------|-------|---------------|
| 001 | init.sql | 15 | … |
| … | | | |

### Idempotency spot-check
| Script | Has IF NOT EXISTS / OR REPLACE / ON CONFLICT | Pass |
|--------|----------------------------------------------|------|
| 003_… | yes | pass |
| … | | |

### Runner status
- Runner exists: yes/no
- Last run: <date or "not run">
- Last result: ok/fail/unknown
```

---

## Verify protocol

Confirms every script is truly idempotent:

1. Start a fresh test database (or use `ci` environment with recorded fixtures).
2. Run all scripts: `docker compose exec REPLACE:SERVICE_API bash -c "cd REPLACE:APP_WORKDIR && REPLACE:MIGRATION_RUN_CMD"`.
3. Run all scripts a second time.
4. Assert: zero errors on second run.
5. Compare schema (`pg_dump --schema-only`) before and after second run - must be identical.

Failures produce a report listing the script name and the error message. The script must be fixed before merging. Recommend `@code-repair repair - from migration`, then re-run `@db-migration verify`.

---

## Directory structure

```
REPLACE:APP_ROOT/
├── migrations/
│   ├── 001_init.sql              ← schemas, extensions, base tables
│   ├── 002_platform_audit_log.sql
│   ├── 003_identity_*.sql
│   ├── 004_domain_a_*.sql
│   ├── 005_domain_c_*.sql
│   ├── 006_domain_b_*.sql
│   ├── 007_triggers.sql          ← all CREATE OR REPLACE FUNCTION/TRIGGER
│   ├── 008_inserts.sql           ← idempotent reference data
│   └── 009_constraints.sql       ← ADD CONSTRAINT IF NOT EXISTS
├── src/
│   └── REPLACE:PLATFORM_PACKAGE/
│       └── migration_runner.py   ← executes scripts on startup
```

For schema-per-tenant (PostgreSQL with multiple schemas), the runner iterates tenants and executes each script with `SET search_path TO tenant_{slug}`.

---

## Anti-patterns

- Writing a script that is not idempotent (no `IF NOT EXISTS` guard).
- Renumbering or deleting existing scripts (breaks the append-only ledger).
- Putting multiple unrelated changes in one script.
- Using `CREATE TABLE` without `IF NOT EXISTS`.
- Using `INSERT` without `ON CONFLICT DO NOTHING` or `WHERE NOT EXISTS`.
- Embedding environment-specific values (use placeholders or environment variables).
- Putting secrets (passwords, keys, tokens) in migration scripts.
- Running scripts manually instead of through the runner (bypasses logging and error handling).
- Treating the script list as a version chain (there is no version - scripts are a ledger, not a linked list).
- Assuming scripts only run once (they run on every startup - idempotency is the contract).

---

## Integration with other skills

| Skill | Integration |
|-------|-------------|
| `plan-foundation` | At P5 (infrastructure), migration strategy choice is recorded |
| `plan-master` | M1 includes `migration_runner.py` as a task; M3 includes migration scripts |
| `session-control` | On close: if migration scripts were added, note in HANDOFF artifact table |

---

## Completion checklist (all modes)

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Mode detected correctly | pass/fail | |
| 2 | Database dialect detected (init mode) | pass/skip | from `REPLACE:TECH_STACK_DOC` (stack document from `.cursorrules`) |
| 3 | Alembic fully removed (init mode) | pass/skip | no remaining references |
| 4 | Scripts numbered in correct order | pass/skip | |
| 5 | Every statement is idempotent | pass/fail | |
| 6 | No secrets in scripts | pass/fail | |
| 7 | Runner executed successfully (run mode) | pass/skip | |
| 8 | Re-run produced no errors (verify mode) | pass/skip | |
| 8b | **Idempotency double-run after create/add** (`@db-migration verify` on the new script) | pass/fail/skip | exit code + run log; skip only when DB not reachable |
| 9 | All config files updated (init mode) | pass/skip | pyproject.toml, DOCS_TECH_STACK, .cursorrules, DIRECTORY_MAP |
| 10 | Application starts and runs migrations (init/run mode) | pass/skip | |
