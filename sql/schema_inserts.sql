-- tools-project — configuration and optional demo rows (idempotent).
-- Runs after bootstrap so a seeded superuser from BOOTSTRAP_ADMIN_* exists when local auth is on.
-- Demo projects attach to the oldest superuser (no hard-coded email).
-- If AUTH_LOCAL_ENABLED=false or bootstrap vars are unset, these INSERTs insert 0 rows until a superuser exists.

INSERT INTO projects (id, name, slug, description, owner_id, created_at, updated_at)
SELECT gen_random_uuid(),
       'Demo workspace',
       'demo-workspace',
       'Sample project so you can open /projects after first login (dev seed).',
       u.id,
       now(),
       now()
FROM users u
WHERE u.is_superuser = TRUE
ORDER BY u.created_at ASC
LIMIT 1
ON CONFLICT (slug) DO NOTHING;

INSERT INTO projects (id, name, slug, description, owner_id, created_at, updated_at)
SELECT gen_random_uuid(),
       'Sandbox demo',
       'demo-sandbox',
       'Second idempotent demo project for exercises and UI smoke tests.',
       u.id,
       now(),
       now()
FROM users u
WHERE u.is_superuser = TRUE
ORDER BY u.created_at ASC
LIMIT 1
ON CONFLICT (slug) DO NOTHING;

-- Membership rows for seeded demo projects (backfill runs before these INSERTs).
INSERT INTO project_members (id, project_id, user_id, role, created_at)
SELECT gen_random_uuid(),
       p.id,
       p.owner_id,
       'owner',
       now()
FROM projects p
WHERE p.slug IN ('demo-workspace', 'demo-sandbox')
  AND NOT EXISTS (
      SELECT 1
      FROM project_members pm
      WHERE pm.project_id = p.id AND pm.user_id = p.owner_id
  );
