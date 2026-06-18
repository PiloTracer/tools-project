# db-migration - reference

Supplement to `skill.md`. Invocation examples, SQL templates, and edge cases.

---

## Invocation examples

| Action | Prompt |
|--------|--------|
| Init / bootstrap | `@db-migration init` |
| Init (alias) | `@db-migration implement` |
| Create a table | `@db-migration create - add orders table` |
| Add a column | `@db-migration add - add column email to master_parties` |
| Run migrations | `@db-migration run` |
| Check status | `@db-migration status` |
| Verify idempotency | `@db-migration verify` |
| Add a trigger | `@db-migration add - CREATE OR REPLACE FUNCTION validate_clave() …` |

### Cursor

```
@db-migration init
@db-migration implement
@db-migration create - users table with tenant_id, email, password_hash
@db-migration add - ADD COLUMN IF NOT EXISTS phone TEXT to users
@db-migration status
```

### Claude Code / opencode / Codex

```
Follow .ai/skills/db-migration/skill.md - create. Add items table.
Follow .ai/skills/db-migration/skill.md - verify.
```

---

## Mode comparison

| | init | create | add | run | status | verify |
|---|------|--------|-----|-----|--------|--------|
| Write .sql file | yes | yes | yes (append or new) | no | no | no |
| Write runner.py | yes | no | no | no | no | no |
| Execute against DB | no | no | no | yes | no | yes (twice) |
| Read-only | no | no | no | no | yes | no |
| Update config files | yes | no | no | no | no | no |
| Remove Alembic | yes | no | no | no | no | no |
| Check idempotency | - | yes (static) | yes (static) | yes (re-run) | spot-check | yes (full) |
| Output report | yes | yes | yes | yes | yes | yes |

---

## SQL templates

### Table creation

```sql
-- 004: Create commercial_documents table (idempotent)
CREATE TABLE IF NOT EXISTS commercial_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    doc_type TEXT NOT NULL,
    commercial_state TEXT NOT NULL DEFAULT 'Draft',
    party_id UUID,
    branch_id UUID NOT NULL,
    terminal_id UUID NOT NULL,
    consecutivo CHAR(20),
    currency TEXT NOT NULL DEFAULT 'CRC',
    subtotal NUMERIC(19,5) NOT NULL DEFAULT 0,
    tax_total NUMERIC(19,5) NOT NULL DEFAULT 0,
    total NUMERIC(19,5) NOT NULL DEFAULT 0,
    order_id UUID,
    clave CHAR(50),
    order_state TEXT,
    source_document_id UUID,
    idempotency_key UUID,
    interaction_profile TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    version INT NOT NULL DEFAULT 1
);

-- Indexes
CREATE INDEX IF NOT EXISTS ix_commercial_documents_tenant_state
    ON commercial_documents (tenant_id, commercial_state);
CREATE INDEX IF NOT EXISTS ix_commercial_documents_tenant_clave
    ON commercial_documents (tenant_id, clave);
```

### Add column

```sql
-- Append to schema_changes.sql or new numbered script
ALTER TABLE commercial_documents
    ADD COLUMN IF NOT EXISTS discount_total NUMERIC(19,5) NOT NULL DEFAULT 0;
```

### Trigger + function

```sql
-- 007_triggers.sql (append)
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_commercial_documents_updated_at ON commercial_documents;
CREATE TRIGGER trg_commercial_documents_updated_at
    BEFORE UPDATE ON commercial_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### Insert reference data (idempotent)

```sql
-- 008_inserts.sql (append)
INSERT INTO tax_tariffs (code, rate, description)
VALUES
    ('01', 0.13, 'IVA 13%'),
    ('02', 0.04, 'IVA 4%'),
    ('03', 0.02, 'IVA 2%'),
    ('04', 0.00, 'Exento'),
    ('05', 0.00, 'No Sujeto')
ON CONFLICT (code) DO NOTHING;
```

### Insert with conditional existence check

```sql
INSERT INTO tenant_settings (tenant_id, interaction_profile, in_contingency)
SELECT '00000000-0000-0000-0000-000000000000', 'counter', false
WHERE NOT EXISTS (
    SELECT 1 FROM tenant_settings
    WHERE tenant_id = '00000000-0000-0000-0000-000000000000'
);
```

### Add unique constraint

```sql
ALTER TABLE commercial_documents
    ADD CONSTRAINT IF NOT EXISTS uq_commercial_documents_tenant_clave
    UNIQUE (tenant_id, clave);
```

### Add RLS policy (schema-per-tenant)

```sql
ALTER TABLE commercial_documents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON commercial_documents;
CREATE POLICY tenant_isolation ON commercial_documents
    FOR ALL
    TO app
    USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

### Create enum type

```sql
DO $$ BEGIN
    CREATE TYPE document_state AS ENUM (
        'Draft', 'Confirmed', 'Voided',
        'Pending', 'Accepted', 'Rejected'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;
```

---

## Migration runner (reference implementation)

```python
# REPLACE:MIGRATION_RUNNER_PATH (example: src/platform/migration_runner.py)
import os
import logging
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent.parent.parent / "migrations"

async def run_migrations(engine: AsyncEngine) -> None:
    """Execute all .sql files in MIGRATIONS_DIR in alphanumeric order."""
    scripts = sorted(
        [f for f in MIGRATIONS_DIR.glob("*.sql") if f.name[0].isdigit()]
    )
    logger.info("migration.runner.start", count=len(scripts))

    for script in scripts:
        sql = script.read_text()
        try:
            async with engine.begin() as conn:
                await conn.execute(text(sql))
            logger.info("migration.run", script=script.name, result="ok")
        except Exception:
            logger.error("migration.run", script=script.name, result="fail")
            raise

    logger.info("migration.runner.complete", count=len(scripts))
```

---

## Edge cases

| Situation | Behavior |
|-----------|----------|
| Gap in numbering (001, 003 - no 002) | Runner executes 001 then 003. Acceptable if 002 was intentionally removed or merged. |
| Script was run manually before the runner existed | Script is idempotent - re-running is harmless. |
| Script fails on second run (not truly idempotent) | Verify mode catches this. Fix the script; never skip. |
| New script added between environments | Runner picks it up on next restart. No version conflict because no version table. |
| Production schema drifts from scripts | The scripts are the source of truth. Fix the script to match reality or fix reality to match the script. |
| Need to roll back a change | Scripts don't support rollback. Write a new script that reverses the change (e.g., `DROP COLUMN IF EXISTS` - with caution). |
| Multi-tenant schema-per-tenant | Runner iterates tenants: `for tenant in tenants: SET search_path TO tenant_{slug}; execute scripts;` |
| Concurrent startups (multiple pods) | Use an advisory lock: `SELECT pg_try_advisory_lock(12345)` at the start of the runner. Only one pod runs migrations. |

---

## Wrong prompts

| Prompt | Problem | Use instead |
|--------|---------|-------------|
| `@db-migration create - drop users table` | Destructive; not idempotent-safe | Write a script that soft-deprecates (rename, add `active=false`) or use `DROP TABLE IF EXISTS` with extreme caution |
| `@db-migration run - only script 003` | Skips ordering contract | Run all scripts - they're idempotent, so re-running is safe |
| `@db-migration create` without describing what | Ambiguous | Describe the change: `create - add items table with cabys_code` |
| `alembic upgrade head` | Wrong tool | Use `@db-migration run` - Alembic has been removed from this project |

---

## Project layout convention

```
.ai/skills/db-migration/
├── skill.md          ← canonical workflow
└── reference.md      ← this file

(Project migrations - not in .ai/)
REPLACE:MIGRATIONS_DIR/
├── 001_init.sql
├── 002_*.sql
└── ...
```

---

## Application startup wiring

Moved from `skill.md` § I5 to keep the protocol lean. Adapt to the framework in your stack doc.

### FastAPI ≥ 0.93 (lifespan - preferred)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from REPLACE:PLATFORM_PACKAGE.migration_runner import run_migrations
from REPLACE:PLATFORM_PACKAGE.database import get_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_migrations(get_engine())
    yield

app = FastAPI(lifespan=lifespan)
```

### FastAPI < 0.93 (deprecated `on_event` - avoid on new projects)

```python
@app.on_event("startup")
async def startup():
    await run_migrations(get_engine())
```

### Schema-per-tenant (iterate tenants first)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = get_engine()
    for tenant in list_tenant_schemas(engine):
        await run_migrations(engine, schema=tenant)
    yield
```

### Flask / Starlette / other frameworks

Invoke `run_migrations(get_engine())` from the framework's startup hook (or before `app.run()`), **before** the server accepts requests. The runner is synchronous-friendly; wrap with `asyncio.run(...)` if your framework is sync.
