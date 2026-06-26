-- tools-project — indexes, unique constraints, and other non-table DDL.
-- Applied on every API startup after schema_changes.sql (idempotent).

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users (email);

CREATE UNIQUE INDEX IF NOT EXISTS uq_projects_slug ON projects (slug);
CREATE INDEX IF NOT EXISTS ix_projects_owner_id ON projects (owner_id);
CREATE INDEX IF NOT EXISTS ix_projects_status ON projects (status);

CREATE UNIQUE INDEX IF NOT EXISTS uq_project_members_project_user ON project_members (project_id, user_id);
CREATE INDEX IF NOT EXISTS ix_project_members_project_id ON project_members (project_id);
CREATE INDEX IF NOT EXISTS ix_project_members_user_id ON project_members (user_id);

CREATE INDEX IF NOT EXISTS ix_components_project_id ON components (project_id);
CREATE INDEX IF NOT EXISTS ix_components_lead_user_id ON components (lead_user_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_components_project_key ON components (project_id, key) WHERE key IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_tasks_project_id ON tasks (project_id);
CREATE INDEX IF NOT EXISTS ix_tasks_component_id ON tasks (component_id);
CREATE INDEX IF NOT EXISTS ix_tasks_assignee_id ON tasks (assignee_id);
CREATE INDEX IF NOT EXISTS ix_tasks_reporter_id ON tasks (reporter_id);
CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks (status);
CREATE INDEX IF NOT EXISTS ix_tasks_parent_task_id ON tasks (parent_task_id);
CREATE INDEX IF NOT EXISTS ix_tasks_is_todo ON tasks (is_todo);

CREATE INDEX IF NOT EXISTS ix_activities_project_id ON activities (project_id);
CREATE INDEX IF NOT EXISTS ix_activities_subject ON activities (subject_type, subject_id);
CREATE INDEX IF NOT EXISTS ix_activities_created_at ON activities (created_at);
CREATE INDEX IF NOT EXISTS ix_activities_actor_id ON activities (actor_id);
CREATE INDEX IF NOT EXISTS ix_activities_parent ON activities (parent_activity_id);
CREATE INDEX IF NOT EXISTS ix_activities_kind ON activities (kind);
-- Quick filter for "external (customer-visible) notes only" on ticket cases.
CREATE INDEX IF NOT EXISTS ix_activities_subject_internal
  ON activities (subject_type, subject_id, is_internal);

CREATE UNIQUE INDEX IF NOT EXISTS uq_mentions_activity_user ON mentions (activity_id, mentioned_user_id);
CREATE INDEX IF NOT EXISTS ix_mentions_mentioned_user_id ON mentions (mentioned_user_id);
CREATE INDEX IF NOT EXISTS ix_mentions_project_id ON mentions (project_id);

CREATE INDEX IF NOT EXISTS ix_tickets_project_id ON tickets (project_id);
CREATE INDEX IF NOT EXISTS ix_tickets_queue_slug ON tickets (queue_slug);
CREATE INDEX IF NOT EXISTS ix_tickets_status ON tickets (status);
CREATE INDEX IF NOT EXISTS ix_tickets_assignee_id ON tickets (assignee_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_project_counters_project_type ON project_counters (project_id, counter_type);

CREATE UNIQUE INDEX IF NOT EXISTS uq_attachments_storage_key ON attachments (storage_key);
CREATE INDEX IF NOT EXISTS ix_attachments_project_id ON attachments (project_id);
CREATE INDEX IF NOT EXISTS ix_attachments_ticket_id ON attachments (ticket_id);
CREATE INDEX IF NOT EXISTS ix_attachments_task_id ON attachments (task_id);
CREATE INDEX IF NOT EXISTS ix_attachments_activity_id ON attachments (activity_id);

CREATE INDEX IF NOT EXISTS ix_inbox_items_owner_id ON inbox_items (owner_id);
CREATE INDEX IF NOT EXISTS ix_inbox_items_created_at ON inbox_items (created_at);

CREATE UNIQUE INDEX IF NOT EXISTS uq_watchers_user_subject ON watchers (user_id, subject_type, subject_id);
CREATE INDEX IF NOT EXISTS ix_watchers_user_id ON watchers (user_id);

CREATE INDEX IF NOT EXISTS ix_github_links_project_id ON github_links (project_id);
CREATE INDEX IF NOT EXISTS ix_github_links_component_id ON github_links (component_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_github_links_project_owner_repo
    ON github_links (project_id, lower(owner), lower(repo));

CREATE UNIQUE INDEX IF NOT EXISTS uq_github_commits_link_sha ON github_commits (github_link_id, sha);
CREATE INDEX IF NOT EXISTS ix_github_commits_link_committed ON github_commits (github_link_id, committed_at DESC);

-- Batch J: CRM
CREATE UNIQUE INDEX IF NOT EXISTS uq_clients_slug ON clients (slug);
CREATE INDEX IF NOT EXISTS ix_clients_created_by ON clients (created_by);
CREATE INDEX IF NOT EXISTS ix_prospects_pipeline_stage ON prospects (pipeline_stage);
CREATE INDEX IF NOT EXISTS ix_prospects_created_by ON prospects (created_by);
CREATE INDEX IF NOT EXISTS ix_client_contacts_client_id ON client_contacts (client_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_client_contacts_user_id ON client_contacts (user_id) WHERE user_id IS NOT NULL;
-- Deduplicate before adding unique index (cleanup from prior seed runs without email constraint).
WITH ranked AS (
    SELECT id,
           ROW_NUMBER() OVER (PARTITION BY email ORDER BY created_at, id::text) AS rn
    FROM client_contacts
)
DELETE FROM client_contacts
WHERE id IN (SELECT id FROM ranked WHERE rn > 1);
CREATE UNIQUE INDEX IF NOT EXISTS uq_client_contacts_email ON client_contacts (email);
CREATE UNIQUE INDEX IF NOT EXISTS uq_project_clients_project_client ON project_clients (project_id, client_id);
CREATE INDEX IF NOT EXISTS ix_project_clients_client_id ON project_clients (client_id);
CREATE INDEX IF NOT EXISTS ix_project_client_access_project_id ON project_client_access (project_id);
CREATE INDEX IF NOT EXISTS ix_project_client_access_contact_id ON project_client_access (client_contact_id);

-- I10f: commit_subject_refs
CREATE INDEX IF NOT EXISTS ix_commit_subject_refs_github_commit_id ON commit_subject_refs (github_commit_id);
CREATE INDEX IF NOT EXISTS ix_commit_subject_refs_subject ON commit_subject_refs (subject_type, subject_id);
CREATE INDEX IF NOT EXISTS ix_commit_subject_refs_sha ON commit_subject_refs (sha);
CREATE INDEX IF NOT EXISTS ix_commit_subject_refs_project_id ON commit_subject_refs (project_id);
-- Uniqueness: resolved refs (with github_commit_id) are unique on commit+subject.
-- Pending refs (null github_commit_id) fall back to project+sha uniqueness.
DROP INDEX IF EXISTS uq_commit_subject_refs_commit_subject;
CREATE UNIQUE INDEX IF NOT EXISTS uq_commit_subject_refs_commit_subject
    ON commit_subject_refs (github_commit_id, subject_type, subject_id)
    WHERE github_commit_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_commit_subject_refs_pending
    ON commit_subject_refs (project_id, sha, subject_type, subject_id)
    WHERE github_commit_id IS NULL;
