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

-- M2: Seed prospects, client, and contacts
INSERT INTO prospects (id, company_name, pipeline_stage, pipeline_value, source, first_contact_date, notes, created_by, created_at, updated_at)
SELECT gen_random_uuid(), 'Acme Corp', 'negotiating', 25000.00, 'referral', now()::date - 14, 'Hot lead from existing customer referral.', u.id, now(), now()
FROM users u WHERE u.is_superuser = TRUE ORDER BY u.created_at ASC LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO prospects (id, company_name, pipeline_stage, pipeline_value, source, first_contact_date, notes, created_by, created_at, updated_at)
SELECT gen_random_uuid(), 'Globex Inc', 'engaged', 15000.00, 'website', now()::date - 30, 'Initial demo completed, follow-up scheduled.', u.id, now(), now()
FROM users u WHERE u.is_superuser = TRUE ORDER BY u.created_at ASC LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO prospects (id, company_name, pipeline_stage, pipeline_value, source, first_contact_date, notes, created_by, created_at, updated_at)
SELECT gen_random_uuid(), 'Initech', 'target', 5000.00, 'cold_outreach', now()::date - 7, 'Cold outbound, awaiting response.', u.id, now(), now()
FROM users u WHERE u.is_superuser = TRUE ORDER BY u.created_at ASC LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO clients (id, name, slug, industry, notes, created_by, created_at, updated_at)
SELECT gen_random_uuid(), 'Umbrella Corp', 'umbrella-corp', 'Pharmaceuticals', 'Existing client from seed data.', u.id, now(), now()
FROM users u WHERE u.is_superuser = TRUE ORDER BY u.created_at ASC LIMIT 1
ON CONFLICT (slug) DO NOTHING;

INSERT INTO client_contacts (id, client_id, name, email, phone, title, role, is_primary, notes, created_at, updated_at)
SELECT gen_random_uuid(), c.id, 'Alice Johnson', 'alice@umbrella-corp.test', '+1-555-0101', 'VP of Engineering', 'contact', TRUE, 'Primary contact for technical discussions.', now(), now()
FROM clients c WHERE c.slug = 'umbrella-corp'
ON CONFLICT DO NOTHING;

INSERT INTO client_contacts (id, client_id, name, email, phone, title, role, is_primary, notes, created_at, updated_at)
SELECT gen_random_uuid(), c.id, 'Bob Williams', 'bob@umbrella-corp.test', '+1-555-0102', ' procurement lead', 'contact', FALSE, 'Handles procurement and contracts.', now(), now()
FROM clients c WHERE c.slug = 'umbrella-corp'
ON CONFLICT DO NOTHING;
