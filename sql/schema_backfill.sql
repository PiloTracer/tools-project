-- tools-project — data backfill / corrective updates for existing rows.
-- Runs after bootstrap (local superuser may exist). Keep statements idempotent.
-- Example patterns:
--   UPDATE ... WHERE ... AND old_column IS NULL;
--   INSERT ... SELECT ... WHERE NOT EXISTS (...);

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

-- Seed project counters for existing projects that lack a ticket counter row.
INSERT INTO project_counters (id, project_id, counter_type, next_value)
SELECT gen_random_uuid(), p.id, 'ticket', 1
FROM projects p
WHERE NOT EXISTS (
    SELECT 1 FROM project_counters pc
    WHERE pc.project_id = p.id AND pc.counter_type = 'ticket'
);
