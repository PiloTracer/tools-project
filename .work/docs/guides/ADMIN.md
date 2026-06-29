# Admin Guide

## User Management

Access the admin panel at `/admin/users` (superuser only).

### Creating users

From the admin panel:
1. Enter the user's email, display name, and password.
2. Assign a role (admin/member).
3. The user can sign in immediately.

Via API:
```bash
POST /v1/admin/users
Authorization: Bearer <superuser-token>
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "secure-password",
  "display_name": "New User",
  "is_superuser": false
}
```

### Managing roles

| Role | Permissions |
|------|------------|
| superuser | Full system access, admin panel, user management |
| owner | Project-level: configure settings, manage members, delete |
| maintainer | Project-level: edit, manage links, moderate |
| member | Project-level: create and edit tasks/tickets |
| viewer | Project-level: read-only access |
| client_contact | Client portal: limited project view |

### Contact linking

From the admin panel, you can link an existing user to a client contact. This enables client portal access for existing team members.

## Project Settings

Each project has configurable settings:

| Setting | Description |
|---------|-------------|
| Project key | Prefix for auto-generated refs (e.g., `PROJ` → `PROJ-123`) |
| Task registry | Enable GitHub task registry for auto-linking commits |
| Auto-prefix | Automatically generate refs for new tasks/tickets |

## Attachment Configuration

Configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ATTACHMENT_MAX_PER_PROJECT` | 500 | Max files per project (0 = unlimited) |
| `ATTACHMENT_MAX_BYTES_PER_PROJECT` | 0 | Max total bytes per project (0 = unlimited) |
| `ATTACHMENT_RETENTION_DAYS` | 0 | Auto-delete files older than N days (0 = never) |
| `ATTACHMENTS_DIR` | `/data/attachments` | Filesystem path for stored files |

## GitHub Token Encryption

GitHub PATs are encrypted at rest. The encryption key is derived from (in order):
1. `GITHUB_TOKEN_ENCRYPTION_KEY` env var
2. SHA-256 of `GITHUB_TOKEN_ENCRYPTION_KEY`  
3. SHA-256 of `JWT_SECRET`

## Monitoring

| Endpoint | Description |
|----------|-------------|
| `GET /healthz` | Health check with DB liveness, version, uptime |
| `GET /v1/projects/{id}/github/sync-status` | Per-link sync health (no auth required) |
| `GET /v1/projects/{id}/github/token-health` | Token validity check (cached 5 min) |
