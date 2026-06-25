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
ALTER TABLE activities ALTER COLUMN actor_id DROP NOT NULL;

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
ALTER TABLE attachments ALTER COLUMN ticket_id DROP NOT NULL;
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
    github_commit_id UUID NOT NULL REFERENCES github_commits (id) ON DELETE CASCADE,
    subject_type VARCHAR(40) NOT NULL,
    subject_id UUID NOT NULL,
    created_by UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
