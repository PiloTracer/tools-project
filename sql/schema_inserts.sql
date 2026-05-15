-- tools-project — configuration and optional demo rows (idempotent).
-- Runs after bootstrap so a seeded superuser from BOOTSTRAP_ADMIN_* exists when local auth is on.
-- Demo project attaches to the oldest superuser (no hard-coded email).

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
