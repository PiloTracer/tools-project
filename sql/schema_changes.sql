-- tools-project — additive DDL (tables, columns). Applied on every API startup.
-- Hand-edit when ORM models change; keep in sync with api/app/models/*.py
-- Use IF NOT EXISTS / ADD COLUMN IF NOT EXISTS so existing databases upgrade safely.

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(320) NOT NULL,
    password_hash VARCHAR(255),
    display_name VARCHAR(200),
    avatar_url VARCHAR(800),
    auth_source VARCHAR(20) NOT NULL DEFAULT 'local',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- additive columns for existing deploys
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(800);
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_source VARCHAR(20) NOT NULL DEFAULT 'local';

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(80) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- additive columns (existing DBs)
ALTER TABLE projects ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active';
ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_key VARCHAR(32);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS github_task_registry_enabled BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS auto_prefix_enabled BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS template_key VARCHAR(32);

CREATE TABLE IF NOT EXISTS project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    key VARCHAR(20),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    lead_user_id UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE components ADD COLUMN IF NOT EXISTS key VARCHAR(20);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    component_id UUID REFERENCES components (id) ON DELETE SET NULL,
    ref VARCHAR(40) UNIQUE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(40) NOT NULL DEFAULT 'todo',
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    assignee_id UUID REFERENCES users (id) ON DELETE SET NULL,
    reporter_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    due_at TIMESTAMPTZ,
    parent_task_id UUID REFERENCES tasks (id) ON DELETE SET NULL,
    is_todo BOOLEAN NOT NULL DEFAULT FALSE,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS ref VARCHAR(40) UNIQUE;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ;

-- Batch F: activity feed (per project), support tickets, @mention rows (from activity body).
CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    subject_type VARCHAR(40) NOT NULL,
    subject_id UUID NOT NULL,
    kind VARCHAR(40) NOT NULL DEFAULT 'comment',
    actor_id UUID REFERENCES users (id) ON DELETE CASCADE,
    parent_activity_id UUID REFERENCES activities (id) ON DELETE SET NULL,
    body TEXT NOT NULL,
    meta_json JSONB,
    is_internal BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE activities ADD COLUMN IF NOT EXISTS kind VARCHAR(40) NOT NULL DEFAULT 'comment';
ALTER TABLE activities ADD COLUMN IF NOT EXISTS parent_activity_id UUID REFERENCES activities (id) ON DELETE SET NULL;
ALTER TABLE activities ADD COLUMN IF NOT EXISTS meta_json JSONB;
-- Plan §5.1 / §11.4: internal vs external (customer-visible) note distinction on ticket / task threads.
ALTER TABLE activities ADD COLUMN IF NOT EXISTS is_internal BOOLEAN NOT NULL DEFAULT FALSE;
-- System-generated activities (e.g. github_commit) have no human actor.
DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'activities' AND column_name = 'actor_id' AND is_nullable = 'NO'
  ) THEN
    ALTER TABLE activities ALTER COLUMN actor_id DROP NOT NULL;
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    activity_id UUID NOT NULL REFERENCES activities (id) ON DELETE CASCADE,
    mentioned_user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    ref VARCHAR(40) UNIQUE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(40) NOT NULL DEFAULT 'open',
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    queue_slug VARCHAR(80) NOT NULL DEFAULT 'default',
    requester_email VARCHAR(320),
    reporter_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    assignee_id UUID REFERENCES users (id) ON DELETE SET NULL,
    first_response_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE tickets ADD COLUMN IF NOT EXISTS ref VARCHAR(40) UNIQUE;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS requester_email VARCHAR(320);
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS first_response_at TIMESTAMPTZ;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS project_counters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    counter_type VARCHAR(20) NOT NULL,
    next_value INT NOT NULL DEFAULT 1
);

-- Ticket images/files (MVP: images only; stored on API volume under ATTACHMENTS_DIR).
CREATE TABLE IF NOT EXISTS attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    ticket_id UUID NOT NULL REFERENCES tickets (id) ON DELETE CASCADE,
    activity_id UUID REFERENCES activities (id) ON DELETE SET NULL,
    filename VARCHAR(500) NOT NULL,
    mime VARCHAR(200) NOT NULL,
    size_bytes INT NOT NULL,
    storage_key VARCHAR(512) NOT NULL,
    created_by UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_attachments_size_bytes CHECK (size_bytes > 0 AND size_bytes <= 26214400)
);

-- Task + inbox + project-level attachments; watchers (Batch G/H parity).
DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'attachments' AND column_name = 'ticket_id' AND is_nullable = 'NO'
  ) THEN
    ALTER TABLE attachments ALTER COLUMN ticket_id DROP NOT NULL;
  END IF;
END $$;
ALTER TABLE attachments ADD COLUMN IF NOT EXISTS task_id UUID REFERENCES tasks (id) ON DELETE CASCADE;

CREATE TABLE IF NOT EXISTS inbox_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    body_md TEXT NOT NULL,
    meta_json JSONB,
    triaged_to_type VARCHAR(20),
    triaged_to_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS watchers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    subject_type VARCHAR(40) NOT NULL,
    subject_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Batch I: GitHub repo links + cached commits (html_url required for deep-link verification).
CREATE TABLE IF NOT EXISTS github_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    component_id UUID REFERENCES components (id) ON DELETE CASCADE,
    owner VARCHAR(200) NOT NULL,
    repo VARCHAR(200) NOT NULL,
    token_cipher TEXT NOT NULL,
    poll_interval_seconds INT NOT NULL DEFAULT 300,
    last_synced_at TIMESTAMPTZ,
    last_seen_sha VARCHAR(40),
    created_by UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_github_links_poll_interval CHECK (poll_interval_seconds >= 60 AND poll_interval_seconds <= 86400)
);

CREATE TABLE IF NOT EXISTS github_commits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_link_id UUID NOT NULL REFERENCES github_links (id) ON DELETE CASCADE,
    sha VARCHAR(40) NOT NULL,
    message TEXT NOT NULL,
    author_name VARCHAR(400),
    author_email VARCHAR(320),
    committed_at TIMESTAMPTZ NOT NULL,
    html_url TEXT NOT NULL,
    raw_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_github_commits_sha_len CHECK (char_length(sha) >= 7 AND char_length(sha) <= 40),
    CONSTRAINT ck_github_commits_html_url_nonempty CHECK (char_length(trim(html_url)) > 0)
);

-- Batch J: CRM / clients-participants

CREATE TABLE IF NOT EXISTS prospects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(200) NOT NULL,
    pipeline_stage VARCHAR(20) NOT NULL DEFAULT 'target',
    pipeline_value NUMERIC(12, 2),
    source VARCHAR(30),
    first_contact_date DATE,
    last_interaction TIMESTAMPTZ,
    next_action TEXT,
    next_action_date DATE,
    notes TEXT,
    created_by UUID NOT NULL REFERENCES users (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id UUID REFERENCES prospects (id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(80) NOT NULL,
    industry VARCHAR(100),
    notes TEXT,
    created_by UUID NOT NULL REFERENCES users (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS client_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients (id) ON DELETE CASCADE,
    prospect_id UUID REFERENCES prospects (id) ON DELETE SET NULL,
    user_id UUID REFERENCES users (id) ON DELETE SET NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(320) NOT NULL,
    phone VARCHAR(50),
    title VARCHAR(200),
    role VARCHAR(30) NOT NULL DEFAULT 'contact',
    is_primary BOOLEAN NOT NULL DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS project_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients (id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS project_client_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    client_contact_id UUID NOT NULL REFERENCES client_contacts (id) ON DELETE CASCADE,
    role VARCHAR(30) NOT NULL DEFAULT 'view',
    can_view_tasks BOOLEAN NOT NULL DEFAULT true,
    can_view_tickets BOOLEAN NOT NULL DEFAULT false,
    can_create_tasks BOOLEAN NOT NULL DEFAULT false,
    created_by UUID NOT NULL REFERENCES users (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- I10f: commit_subject_refs (normalized cross-link table)
CREATE TABLE IF NOT EXISTS commit_subject_refs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_commit_id UUID REFERENCES github_commits (id) ON DELETE SET NULL,
    subject_type VARCHAR(40) NOT NULL,
    subject_id UUID NOT NULL,
    created_by UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Link-now, resolve-later columns: sha + project_id let us create refs before
-- the commit syncs back from GitHub.  github_commit_id became nullable above.
ALTER TABLE commit_subject_refs ADD COLUMN IF NOT EXISTS sha VARCHAR(40);
ALTER TABLE commit_subject_refs ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects (id) ON DELETE CASCADE;

-- Backfill existing rows from the github_commits → github_links chain.
UPDATE commit_subject_refs r
SET sha = gc.sha,
    project_id = gl.project_id
FROM github_commits gc
JOIN github_links gl ON gl.id = gc.github_link_id
WHERE r.github_commit_id = gc.id
  AND (r.sha IS NULL OR r.project_id IS NULL);

-- Sync health: error-tracking columns for github_links (2026-06-26)
ALTER TABLE github_links ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) NOT NULL DEFAULT 'idle';
ALTER TABLE github_links ADD COLUMN IF NOT EXISTS last_error TEXT;
ALTER TABLE github_links ADD COLUMN IF NOT EXISTS last_error_at TIMESTAMPTZ;
ALTER TABLE github_links ADD COLUMN IF NOT EXISTS error_count INT NOT NULL DEFAULT 0;

-- User API keys: personal persistent tokens for agent/MCP access.
-- key_hash stores SHA-256(plaintext); key_prefix stores the first 8 chars for UI display.
CREATE TABLE IF NOT EXISTS user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    key_hash VARCHAR(64) NOT NULL,
    key_prefix VARCHAR(8) NOT NULL,
    label VARCHAR(100),
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Mod 3: External refs (generalized commit_subject_refs)
ALTER TABLE commit_subject_refs ADD COLUMN IF NOT EXISTS source_app VARCHAR(30) NOT NULL DEFAULT 'github';
ALTER TABLE commit_subject_refs ADD COLUMN IF NOT EXISTS external_id VARCHAR(200);
ALTER TABLE commit_subject_refs ADD COLUMN IF NOT EXISTS external_url TEXT;
ALTER TABLE commit_subject_refs ADD COLUMN IF NOT EXISTS label VARCHAR(200);

-- Mod 1: Webhook subscriptions for outbound event dispatcher
CREATE TABLE IF NOT EXISTS webhook_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label VARCHAR(100),
    url TEXT NOT NULL,
    events TEXT[] NOT NULL DEFAULT '{}',
    hmac_secret TEXT NOT NULL,
    max_retries INTEGER NOT NULL DEFAULT 3,
    last_delivered_at TIMESTAMPTZ,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Multi-tenancy: tenants table + tenant_id columns on isolated tables.
-- tenant_id is added nullable first; backfill + NOT NULL constraint applied in schema_backfill.sql.

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    settings JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
ALTER TABLE prospects ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
ALTER TABLE client_contacts ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
ALTER TABLE webhook_subscriptions ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
ALTER TABLE user_api_keys ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);

-- Plan-sync: milestones (sequence dimension) for plan imports (SPEC plan-sync R1, R27).
-- Idempotent — re-run on every API start (schema_sql lifespan runner).

CREATE TABLE IF NOT EXISTS milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    key VARCHAR(32),
    name VARCHAR(200) NOT NULL,
    summary TEXT,
    description TEXT,
    status VARCHAR(40) NOT NULL DEFAULT 'pending',
    plan_state VARCHAR(16) NOT NULL DEFAULT 'active',
    sort_order INT NOT NULL DEFAULT 0,
    start_at TIMESTAMPTZ,
    due_at TIMESTAMPTZ,
    plan_ref VARCHAR(64),
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Plan-sync: plan provenance on tasks (SPEC plan-sync R27). Additive; existing rows untouched.
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS milestone_id UUID REFERENCES milestones (id) ON DELETE SET NULL;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS plan_ref VARCHAR(64);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS plan_state VARCHAR(16) NOT NULL DEFAULT 'active';

-- Work types: the kind of effort (programming, legal, research, …).
-- Orthogonal to components, which name a product area. Existing rows stay valid:
-- the column is added nullable here; schema_backfill.sql fills it and sets NOT NULL.
CREATE TABLE IF NOT EXISTS work_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    key VARCHAR(32) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS work_type_id UUID;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS work_type_id UUID;

-- Present before the seed function runs. schema_indexes.sql repeats these.
CREATE UNIQUE INDEX IF NOT EXISTS uq_work_types_project_key ON work_types (project_id, key);
CREATE UNIQUE INDEX IF NOT EXISTS uq_work_types_one_default ON work_types (project_id) WHERE is_default;

-- Remembers that a starter key was offered. Deleting the type leaves this row,
-- so the next API start does not put that type back.
CREATE TABLE IF NOT EXISTS work_type_starter_grants (
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    key VARCHAR(32) NOT NULL,
    PRIMARY KEY (project_id, key)
);

-- Empty catalogs receive the full starter set. Catalogs that already exist
-- receive only starter keys added after the first three, and only once.
-- A deleted starter is not recreated. ON CONFLICT guards a race between the
-- project trigger and the backfill.
CREATE OR REPLACE FUNCTION seed_work_types_for_project(p_project_id UUID) RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM work_types WHERE project_id = p_project_id) THEN
    INSERT INTO work_types (project_id, key, name, description, is_default)
    VALUES
      (p_project_id, 'programming', 'Programming', 'Software implementation and engineering.', TRUE),
      (p_project_id, 'administrative', 'Administrative', 'Operations, coordination, and business administration.', FALSE),
      (p_project_id, 'documentation', 'Documentation', 'Writing and maintaining documents.', FALSE),
      (p_project_id, 'legal', 'Legal', 'Contracts, compliance, privacy, and intellectual property.', FALSE),
      (p_project_id, 'miscellaneous', 'Miscellaneous', 'Work that does not fit another type.', FALSE),
      (p_project_id, 'research', 'Research', 'Discovery, spikes, and feasibility before a commitment.', FALSE),
      (p_project_id, 'design', 'Design', 'Interface, visual, and experience work.', FALSE),
      (p_project_id, 'testing', 'Testing', 'Checks that behavior matches what was agreed.', FALSE),
      (p_project_id, 'defect', 'Defect', 'Fixing something that is broken.', FALSE),
      (p_project_id, 'support', 'Support', 'Helping a user or customer with a problem.', FALSE),
      (p_project_id, 'operations', 'Operations', 'Deploys, incidents, and the environments the system runs in.', FALSE),
      (p_project_id, 'planning', 'Planning', 'Scope, estimates, and the order of work.', FALSE),
      (p_project_id, 'security', 'Security', 'Access, hardening, and review of risk.', FALSE),
      (p_project_id, 'data', 'Data', 'Analysis, migration, and reporting.', FALSE),
      (p_project_id, 'finance', 'Finance', 'Billing, invoices, and budgets.', FALSE)
    ON CONFLICT (project_id, key) DO NOTHING;

    INSERT INTO work_type_starter_grants (project_id, key)
    SELECT p_project_id, v.key
    FROM (VALUES
      ('programming'),
      ('administrative'),
      ('documentation'),
      ('legal'),
      ('miscellaneous'),
      ('research'),
      ('design'),
      ('testing'),
      ('defect'),
      ('support'),
      ('operations'),
      ('planning'),
      ('security'),
      ('data'),
      ('finance')
    ) AS v(key)
    ON CONFLICT (project_id, key) DO NOTHING;
  END IF;

  INSERT INTO work_types (project_id, key, name, description, is_default)
  SELECT p_project_id, v.key, v.name, v.description, FALSE
  FROM (VALUES
    ('legal', 'Legal', 'Contracts, compliance, privacy, and intellectual property.'),
    ('miscellaneous', 'Miscellaneous', 'Work that does not fit another type.'),
    ('research', 'Research', 'Discovery, spikes, and feasibility before a commitment.'),
    ('design', 'Design', 'Interface, visual, and experience work.'),
    ('testing', 'Testing', 'Checks that behavior matches what was agreed.'),
    ('defect', 'Defect', 'Fixing something that is broken.'),
    ('support', 'Support', 'Helping a user or customer with a problem.'),
    ('operations', 'Operations', 'Deploys, incidents, and the environments the system runs in.'),
    ('planning', 'Planning', 'Scope, estimates, and the order of work.'),
    ('security', 'Security', 'Access, hardening, and review of risk.'),
    ('data', 'Data', 'Analysis, migration, and reporting.'),
    ('finance', 'Finance', 'Billing, invoices, and budgets.')
  ) AS v(key, name, description)
  WHERE NOT EXISTS (
    SELECT 1 FROM work_type_starter_grants g
    WHERE g.project_id = p_project_id AND g.key = v.key
  )
  AND NOT EXISTS (
    SELECT 1 FROM work_types w
    WHERE w.project_id = p_project_id AND w.key = v.key
  )
  ON CONFLICT (project_id, key) DO NOTHING;

  INSERT INTO work_type_starter_grants (project_id, key)
  SELECT p_project_id, v.key
  FROM (VALUES
    ('legal'),
    ('miscellaneous'),
    ('research'),
    ('design'),
    ('testing'),
    ('defect'),
    ('support'),
    ('operations'),
    ('planning'),
    ('security'),
    ('data'),
    ('finance')
  ) AS v(key)
  ON CONFLICT (project_id, key) DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION seed_project_work_types() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  -- Null and basic keep today's work-type seed. Any other template copies its
  -- own columns and types in the application, in the same transaction.
  IF NEW.template_key IS NOT NULL AND NEW.template_key <> 'basic' THEN
    RETURN NEW;
  END IF;
  PERFORM seed_work_types_for_project(NEW.id);
  RETURN NEW;
END;
$$;

-- Process templates. A project with no board-column rows keeps the global
-- task statuses. Rows exist only when a non-basic template was applied.
CREATE TABLE IF NOT EXISTS project_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(32) NOT NULL,
    name VARCHAR(200) NOT NULL,
    team VARCHAR(80),
    description TEXT,
    is_builtin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS project_template_columns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES project_templates (id) ON DELETE CASCADE,
    key VARCHAR(32) NOT NULL,
    label VARCHAR(80) NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    is_finished BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS project_template_work_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES project_templates (id) ON DELETE CASCADE,
    key VARCHAR(32) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS project_template_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES project_templates (id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    column_key VARCHAR(32) NOT NULL,
    work_type_key VARCHAR(32) NOT NULL,
    sort_order INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS project_board_columns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    key VARCHAR(32) NOT NULL,
    label VARCHAR(80) NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    is_finished BOOLEAN NOT NULL DEFAULT FALSE
);

DROP TRIGGER IF EXISTS tr_projects_seed_work_types ON projects;
CREATE TRIGGER tr_projects_seed_work_types
AFTER INSERT ON projects
FOR EACH ROW
EXECUTE FUNCTION seed_project_work_types();

-- Fills a missing type from the project default, then rejects a type from another project.
CREATE OR REPLACE FUNCTION assign_default_work_type() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  type_project UUID;
BEGIN
  IF NEW.work_type_id IS NULL THEN
    SELECT id INTO NEW.work_type_id
    FROM work_types
    WHERE project_id = NEW.project_id AND is_default
    LIMIT 1;
  END IF;
  IF NEW.work_type_id IS NULL THEN
    RAISE EXCEPTION 'project % has no default work type', NEW.project_id;
  END IF;
  SELECT project_id INTO type_project FROM work_types WHERE id = NEW.work_type_id;
  IF type_project IS DISTINCT FROM NEW.project_id THEN
    RAISE EXCEPTION 'work type % does not belong to project %', NEW.work_type_id, NEW.project_id;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS tr_tasks_assign_work_type ON tasks;
CREATE TRIGGER tr_tasks_assign_work_type
BEFORE INSERT OR UPDATE ON tasks
FOR EACH ROW
EXECUTE FUNCTION assign_default_work_type();

DROP TRIGGER IF EXISTS tr_tickets_assign_work_type ON tickets;
CREATE TRIGGER tr_tickets_assign_work_type
BEFORE INSERT OR UPDATE ON tickets
FOR EACH ROW
EXECUTE FUNCTION assign_default_work_type();

-- Immediate, not deferred: a deferred check stays pending and then blocks
-- ALTER COLUMN ... SET NOT NULL in the same startup transaction.
DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'fk_tasks_work_type' AND condeferrable
  ) THEN
    ALTER TABLE tasks DROP CONSTRAINT fk_tasks_work_type;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_tasks_work_type') THEN
    ALTER TABLE tasks
      ADD CONSTRAINT fk_tasks_work_type
      FOREIGN KEY (work_type_id) REFERENCES work_types (id)
      ON DELETE RESTRICT;
  END IF;
END $$;

DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'fk_tickets_work_type' AND condeferrable
  ) THEN
    ALTER TABLE tickets DROP CONSTRAINT fk_tickets_work_type;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_tickets_work_type') THEN
    ALTER TABLE tickets
      ADD CONSTRAINT fk_tickets_work_type
      FOREIGN KEY (work_type_id) REFERENCES work_types (id)
      ON DELETE RESTRICT;
  END IF;
END $$;

-- CRM intake profile (prospects + clients): org/contact details for flexible acquisition.
-- Additive and idempotent — existing rows keep NULL for new columns; re-run safe on every start.
-- Organization Name remains prospects.company_name / clients.name.
-- Contact Name/Email/Phone on prospects are the primary lead contact; clients keep
-- multi-contact detail on client_contacts (name/email/phone already present).

ALTER TABLE prospects ADD COLUMN IF NOT EXISTS contact_name VARCHAR(200);
ALTER TABLE prospects ADD COLUMN IF NOT EXISTS contact_email VARCHAR(320);
ALTER TABLE prospects ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50);
ALTER TABLE prospects ADD COLUMN IF NOT EXISTS org_email VARCHAR(320);
ALTER TABLE prospects ADD COLUMN IF NOT EXISTS org_phone VARCHAR(50);
ALTER TABLE prospects ADD COLUMN IF NOT EXISTS working_schedule TEXT;
ALTER TABLE prospects ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE prospects ADD COLUMN IF NOT EXISTS service VARCHAR(200);
ALTER TABLE prospects ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE prospects ADD COLUMN IF NOT EXISTS latitude NUMERIC(10, 7);
ALTER TABLE prospects ADD COLUMN IF NOT EXISTS longitude NUMERIC(10, 7);

ALTER TABLE clients ADD COLUMN IF NOT EXISTS email VARCHAR(320);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS working_schedule TEXT;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS service VARCHAR(200);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS latitude NUMERIC(10, 7);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS longitude NUMERIC(10, 7);



