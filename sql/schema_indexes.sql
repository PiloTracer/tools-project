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
CREATE INDEX IF NOT EXISTS ix_attachments_activity_id ON attachments (activity_id);
