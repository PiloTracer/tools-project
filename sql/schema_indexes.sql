-- tools-project — indexes, unique constraints, and other non-table DDL.
-- Applied on every API startup after schema_changes.sql (idempotent).

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users (email);

CREATE UNIQUE INDEX IF NOT EXISTS uq_projects_slug ON projects (slug);
CREATE INDEX IF NOT EXISTS ix_projects_owner_id ON projects (owner_id);
