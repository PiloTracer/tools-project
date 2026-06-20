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

-- M2: Seed prospects (50 companies across pipeline stages).
-- IDs are deterministic (md5 of seed key) so ON CONFLICT DO NOTHING is effective across restarts.
INSERT INTO prospects (id, company_name, pipeline_stage, pipeline_value, source, first_contact_date, notes, created_by, created_at, updated_at)
SELECT md5('prospect:' || v.company_name || ':' || u.id::text)::uuid,
       v.company_name, v.pipeline_stage, v.pipeline_value, v.source,
       now()::date - v.days_ago, v.notes, u.id, now(), now()
FROM (VALUES
  -- target (12)
  ('AeroDyne Systems',    'target',   18000,  'cold_outreach', 3,   'Cold outbound to CTO.'),
  ('BluePeak Analytics',  'target',   22000,  'conference',    5,   'Met at SaaStr booth.'),
  ('CoreBridge Tech',     'target',    9500,  'linkedin',      2,   'InMail response pending.'),
  ('DeltaStream Inc',     'target',   30000,  'cold_outreach', 1,   'Sequence started today.'),
  ('Echelon Data',        'target',   15000,  'referral',      4,   'Referred by Acme Corp.'),
  ('Fermion Labs',        'target',   12000,  'website',       6,   'Trial signup, no follow-up yet.'),
  ('GridPoint Energy',    'target',   40000,  'conference',    7,   'Enterprise prospect from AWS re:Invent.'),
  ('Helix Robotics',      'target',    8000,  'cold_outreach', 8,   'Outbound to head of engineering.'),
  ('IonForge Materials',  'target',   16000,  'linkedin',      3,   'Connected with VP Ops.'),
  ('Juno Payroll',        'target',   11000,  'partner',       5,   'Partner intro through Stripe.'),
  ('Kestrel Aviation',    'target',   27000,  'cold_outreach', 2,   'Targeting fleet management.'),
  ('Lumen Publishing',    'target',    6500,  'website',       9,   'Downloaded whitepaper.'),
  -- connected (8)
  ('Meridian Health',     'connected', 35000, 'referral',     12,   'Warm intro from board member. LinkedIn accepted.'),
  ('Nexa Capital',        'connected', 50000, 'conference',   15,   'Follow-up call booked after Money2020.'),
  ('Orbit Logistics',     'connected', 14000, 'linkedin',     10,   'Decision-maker engaged on thread.'),
  ('Pivot CRM',           'connected',  8000, 'cold_outreach', 11,   'Replied to sequence, interested.'),
  ('Quantum Signage',     'connected', 20000, 'website',      14,   'Demo request submitted.'),
  ('RidgeLine Security',  'connected', 28000, 'partner',      13,   'Introduced via Okta partnership.'),
  ('Saturn Payments',     'connected', 17000, 'referral',      8,   'Referral from Nexa Capital.'),
  ('TerraForm Energy',    'connected', 45000, 'conference',   18,   'CIO expressed interest at GreenTech summit.'),
  -- engaged (8)
  ('Umbra Software',      'engaged',   32000, 'referral',     25,   'POC agreed. Engineering reviewing API docs.'),
  ('Vector Aerospace',    'engaged',   60000, 'conference',   30,   'Completed technical deep-dive. Procurement involved.'),
  ('Wavelength Media',    'engaged',   10000, 'website',      20,   'Trial active, 4 seats. Weekly check-in cadence.'),
  ('Xenith Bio',          'engaged',   25000, 'cold_outreach',28,   'Passed champion to economic buyer.'),
  ('YieldMax Trading',    'engaged',   75000, 'referral',     35,   'Multiple stakeholders aligned. Legal review started.'),
  ('Zenith Consulting',   'engaged',   13000, 'linkedin',     22,   'Active evaluation against competitor.'),
  ('AlphaGrid Networks',  'engaged',   42000, 'partner',      27,   'Co-selling with AWS. Joint pitch delivered.'),
  ('BarrelHouse Brewing', 'engaged',    7000, 'cold_outreach',19,   'Owner loved the demo. Budget approval pending.'),
  -- call_scheduled (6)
  ('CipherTrust Bank',    'call_scheduled', 55000, 'referral', 40,   'Call with CISO and VP Eng on Thursday.'),
  ('Dune Capital Partners','call_scheduled', 38000, 'conference', 38,   'Partner call scheduled. Deck ready.'),
  ('Epoch AI',            'call_scheduled', 90000, 'website',  42,   'Enterprise evaluation call. SE assigned.'),
  ('Flux Semiconductor',  'call_scheduled', 26000, 'linkedin',  36,   'Director of Eng accepted meeting.'),
  ('GigaWatt Solutions',  'call_scheduled', 48000, 'cold_outreach', 44,   'Cold email → CTO booked 30 min.'),
  ('HyperLoop Transit',   'call_scheduled', 65000, 'partner',    33,   'Introduction through YC network.'),
  -- call_done (5)
  ('Island View Resorts', 'call_done',      12000, 'website',  50,   'Demo completed. Awaiting technical questionnaire.'),
  ('Jasper Materials',    'call_done',      31000, 'referral',  48,   'Call went well. Sending security review.'),
  ('KiloWatt Electric',   'call_done',      19000, 'cold_outreach', 55,   'Gatekeeper bypassed. Needs champion.'),
  ('Lattice BioPharma',   'call_done',      44000, 'conference', 52,   'VP impressed. Compliance review next.'),
  ('Monarch Insurance',   'call_done',      23000, 'partner',    46,   'Mutual customer reference call done.'),
  -- proposal_sent (5)
  ('NorthStar Shipping',  'proposal_sent',  58000, 'referral',  65,   'Proposal sent. Board reviews Friday.'),
  ('Opal Ventures',       'proposal_sent',  36000, 'conference', 60,   'Term sheet + proposal delivered.'),
  ('Phoenix Construction','proposal_sent',  72000, 'website',    70,   'RFP response submitted. 3 competitors.'),
  ('Quarry Digital',      'proposal_sent',  15000, 'linkedin',   58,   'SOW sent. Procurement reviewing.'),
  ('Redwood Analytics',   'proposal_sent',  41000, 'cold_outreach', 62,   'Custom pricing proposal sent.'),
  -- negotiating (4)
  ('SkyBridge Capital',   'negotiating',    85000, 'referral',   80,   'Final terms. Redlines on MSA.'),
  ('Titan Manufacturing', 'negotiating',    66000, 'conference',  75,   'Negotiating scope and pricing. Near close.'),
  ('Union Data Centers',  'negotiating',   120000,'partner',      90,   'Multi-year deal. Legal on v3 of contract.'),
  ('Vertex AI Labs',      'negotiating',    53000, 'website',     72,   'Discount request. Counter-offer sent.'),
  -- won (1)
  ('Waypoint Financial',  'won',            47000, 'referral',   100,   'Closed! Contract signed. Onboarding next week.'),
  -- lost (1)
  ('X-Ray Media Group',   'lost',           19000, 'website',     95,   'Chose competitor on price. Lost to Salesforce.')
) AS v(company_name, pipeline_stage, pipeline_value, source, days_ago, notes)
CROSS JOIN (SELECT u.id FROM users u WHERE u.is_superuser = TRUE ORDER BY u.created_at ASC LIMIT 1) u
ON CONFLICT DO NOTHING;

-- M2: Seed client and contacts

INSERT INTO clients (id, name, slug, industry, notes, created_by, created_at, updated_at)
SELECT gen_random_uuid(), 'Umbrella Corp', 'umbrella-corp', 'Pharmaceuticals', 'Existing client from seed data.', u.id, now(), now()
FROM users u WHERE u.is_superuser = TRUE ORDER BY u.created_at ASC LIMIT 1
ON CONFLICT (slug) DO NOTHING;

INSERT INTO client_contacts (id, client_id, name, email, phone, title, role, is_primary, notes, created_at, updated_at)
SELECT gen_random_uuid(), c.id, 'Alice Johnson', 'alice@umbrella-corp.test', '+1-555-0101', 'VP of Engineering', 'contact', TRUE, 'Primary contact for technical discussions.', now(), now()
FROM clients c WHERE c.slug = 'umbrella-corp'
ON CONFLICT (email) DO NOTHING;

-- Demo client user (password: "client-demo") linked to the client_contact for client portal testing.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
INSERT INTO users (id, email, password_hash, display_name, auth_source, is_active, is_superuser, created_at, updated_at)
SELECT gen_random_uuid(), 'alice@umbrella-corp.test', crypt('client-demo', gen_salt('bf')), 'Alice Johnson', 'local', TRUE, FALSE, now(), now()
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'alice@umbrella-corp.test');

-- Link the alice@umbrella-corp.test user to its client_contact row (idempotent).
UPDATE client_contacts cc
SET user_id = u.id, updated_at = now()
FROM users u
WHERE u.email = 'alice@umbrella-corp.test'
  AND cc.email = 'alice@umbrella-corp.test'
  AND cc.user_id IS NULL;

-- Grant the demo client contact view-level access to the demo workspace and sandbox projects.
INSERT INTO project_client_access (id, project_id, client_contact_id, role, can_view_tasks, can_view_tickets, can_create_tasks, created_by, created_at)
SELECT gen_random_uuid(), p.id, cc.id, 'view', TRUE, TRUE, FALSE, admin.id, now()
FROM projects p
CROSS JOIN client_contacts cc
CROSS JOIN LATERAL (SELECT u.id FROM users u WHERE u.is_superuser = TRUE ORDER BY u.created_at ASC LIMIT 1) admin
WHERE cc.email = 'alice@umbrella-corp.test'
  AND p.slug IN ('demo-workspace', 'demo-sandbox')
  AND NOT EXISTS (
      SELECT 1 FROM project_client_access pca
      WHERE pca.project_id = p.id AND pca.client_contact_id = cc.id
  );

INSERT INTO client_contacts (id, client_id, name, email, phone, title, role, is_primary, notes, created_at, updated_at)
SELECT gen_random_uuid(), c.id, 'Bob Williams', 'bob@umbrella-corp.test', '+1-555-0102', ' procurement lead', 'contact', FALSE, 'Handles procurement and contracts.', now(), now()
FROM clients c WHERE c.slug = 'umbrella-corp'
ON CONFLICT (email) DO NOTHING;
