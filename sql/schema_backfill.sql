-- tools-project — data backfill / corrective updates for existing rows.
-- Runs after bootstrap (local superuser may exist). Keep statements idempotent.
-- Example patterns:
--   UPDATE ... WHERE ... AND old_column IS NULL;
--   INSERT ... SELECT ... WHERE NOT EXISTS (...);

-- Multi-tenancy backfill: create default tenant and assign all existing rows.
-- tenant_id columns were added nullable in schema_changes.sql; we backfill here
-- and then apply NOT NULL constraints on non-users tables.

INSERT INTO tenants (slug, name) VALUES ('default', 'Default Organization') ON CONFLICT DO NOTHING;

-- Backfill existing non-superuser rows. Cross-tenant superusers (is_superuser=true in existing
-- single-tenant data) remain tenant_id IS NULL after backfill — they become cross-tenant superusers.
UPDATE users
SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default')
WHERE tenant_id IS NULL AND is_superuser = false;

UPDATE projects SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default') WHERE tenant_id IS NULL;
UPDATE prospects SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default') WHERE tenant_id IS NULL;
UPDATE clients SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default') WHERE tenant_id IS NULL;
UPDATE client_contacts SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default') WHERE tenant_id IS NULL;
UPDATE webhook_subscriptions SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default') WHERE tenant_id IS NULL;
UPDATE user_api_keys SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default') WHERE tenant_id IS NULL;

-- Apply NOT NULL constraints on non-users tables (users allows NULL for cross-tenant superusers).
-- The users CHECK constraint must run AFTER backfill so existing rows are valid.
-- Drop first (from any prior partial run), backfill, then re-add.
ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_tenant_or_superuser;

ALTER TABLE users ADD CONSTRAINT ck_users_tenant_or_superuser
  CHECK (is_superuser = true OR tenant_id IS NOT NULL);

ALTER TABLE projects ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE prospects ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE clients ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE client_contacts ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE webhook_subscriptions ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE user_api_keys ALTER COLUMN tenant_id SET NOT NULL;

-- Dedup prospects: keep only the LATEST row per (company_name, created_by).
-- Seed inserts used gen_random_uuid() before 2026-06-19 which created duplicates on every
-- API restart (ON CONFLICT DO NOTHING with no unique key to conflict on).
DELETE FROM prospects
WHERE id NOT IN (
  SELECT DISTINCT ON (company_name, created_by) id
  FROM prospects
  ORDER BY company_name, created_by, updated_at DESC
);

-- Ensure legacy owner-only projects have an explicit owner membership row (idempotent).
INSERT INTO project_members (id, project_id, user_id, role, created_at)
SELECT gen_random_uuid(),
       p.id,
       p.owner_id,
       'owner',
       now()
FROM projects p
WHERE NOT EXISTS (
    SELECT 1
    FROM project_members pm
    WHERE pm.project_id = p.id AND pm.user_id = p.owner_id
);

-- Backfill auth_source for existing users that have a password_hash (local auth users).
-- OAuth-upserted users without password_hash default to 'oauth'.
UPDATE users
SET auth_source = 'local'
WHERE password_hash IS NOT NULL AND auth_source != 'local';

UPDATE users
SET auth_source = 'oauth'
WHERE password_hash IS NULL AND auth_source != 'oauth';

-- Seed project counters for existing projects that lack a task counter row.
INSERT INTO project_counters (id, project_id, counter_type, next_value)
SELECT gen_random_uuid(), p.id, 'task', 1
FROM projects p
WHERE NOT EXISTS (
    SELECT 1 FROM project_counters pc
    WHERE pc.project_id = p.id AND pc.counter_type = 'task'
);

-- Move a task counter past refs that already exist, such as TPR-4 while
-- next_value is still 2. Never lowers a counter. Does not change task rows.
UPDATE project_counters AS pc
SET next_value = src.next_needed
FROM (
    SELECT p.id AS project_id,
           MAX(substring(t.ref FROM length(p.project_key) + 2)::int) + 1 AS next_needed
    FROM tasks AS t
    JOIN projects AS p ON p.id = t.project_id
    WHERE p.project_key IS NOT NULL
      AND p.project_key <> ''
      AND t.ref ~ ('^' || p.project_key || '-[0-9]+$')
    GROUP BY p.id
) AS src
WHERE pc.project_id = src.project_id
  AND pc.counter_type = 'task'
  AND src.next_needed > pc.next_value;

-- Seed project counters for existing projects that lack a ticket counter row.
INSERT INTO project_counters (id, project_id, counter_type, next_value)
SELECT gen_random_uuid(), p.id, 'ticket', 1
FROM projects p
WHERE NOT EXISTS (
    SELECT 1 FROM project_counters pc
    WHERE pc.project_id = p.id AND pc.counter_type = 'ticket'
);

-- Same repair for ticket refs (TPR-T-10 while the ticket counter is still 1).
UPDATE project_counters AS pc
SET next_value = src.next_needed
FROM (
    SELECT p.id AS project_id,
           MAX(substring(t.ref FROM length(p.project_key) + 4)::int) + 1 AS next_needed
    FROM tickets AS t
    JOIN projects AS p ON p.id = t.project_id
    WHERE p.project_key IS NOT NULL
      AND p.project_key <> ''
      AND t.ref ~ ('^' || p.project_key || '-T-[0-9]+$')
    GROUP BY p.id
) AS src
WHERE pc.project_id = src.project_id
  AND pc.counter_type = 'ticket'
  AND src.next_needed > pc.next_value;

-- Work types. An empty catalog gets the full starter set. A catalog that
-- already exists gains starter keys added later, once; a deleted starter is
-- not recreated. Untyped tasks and tickets become Programming.
SELECT seed_work_types_for_project(id) FROM projects;

UPDATE tasks AS t
SET work_type_id = w.id
FROM work_types AS w
WHERE t.work_type_id IS NULL
  AND w.project_id = t.project_id
  AND w.is_default;

UPDATE tickets AS t
SET work_type_id = w.id
FROM work_types AS w
WHERE t.work_type_id IS NULL
  AND w.project_id = t.project_id
  AND w.is_default;

ALTER TABLE tasks ALTER COLUMN work_type_id SET NOT NULL;
ALTER TABLE tickets ALTER COLUMN work_type_id SET NOT NULL;
