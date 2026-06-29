# API Reference

tools-project exposes a REST API at `/v1`. Full OpenAPI documentation is available at `/docs` when the server is running.

## Authentication

All API requests require an `Authorization: Bearer <token>` header (local JWT or OAuth token).

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/auth/config` | GET | Get auth mode configuration |
| `/v1/auth/local/login` | POST | Sign in with email + password |
| `/v1/auth/me` | GET | Get current user profile |

## Projects

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/projects` | GET | List projects |
| `/v1/projects` | POST | Create project |
| `/v1/projects/{id}` | GET | Get project details |
| `/v1/projects/{id}` | PATCH | Update project settings |
| `/v1/projects/{id}/members` | GET | List project members |
| `/v1/projects/{id}/members` | POST | Add member |
| `/v1/projects/{id}/components` | GET | List components |
| `/v1/projects/{id}/components` | POST | Create component |

## Tasks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/projects/{id}/tasks` | GET | List tasks (supports `?status=`, `?assignee_id=`, `?limit=`, `?offset=`) |
| `/v1/projects/{id}/tasks` | POST | Create task |
| `/v1/tasks/{id}` | GET | Get task detail |
| `/v1/tasks/{id}` | PATCH | Update task |
| `/v1/tasks/{id}/transition` | POST | Change task status |
| `/v1/tasks/batch` | PATCH | Batch update tasks |
| `/v1/tasks/{id}/attachments` | POST | Upload attachment |

## Tickets

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/projects/{id}/tickets` | GET | List tickets (supports `?queue_slug=`, `?status=`, `?limit=`, `?offset=`) |
| `/v1/projects/{id}/tickets` | POST | Create ticket |
| `/v1/tickets/{id}` | GET | Get ticket detail |
| `/v1/tickets/{id}` | PATCH | Update ticket |
| `/v1/tickets/{id}/transition` | POST | Change ticket status |

## Activity

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/projects/{id}/activities` | GET | List activities (supports `?kind=`, `?subject_type=`, `?limit=`, `?offset=`) |
| `/v1/projects/{id}/activities` | POST | Create activity comment |

## Inbox

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/inbox` | GET | List inbox items |
| `/v1/inbox` | POST | Create inbox item |
| `/v1/inbox/{id}/triage` | POST | Triage into task or ticket |

## GitHub

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/projects/{id}/github/links` | GET | List linked repos |
| `/v1/projects/{id}/github/links` | POST | Link a repo |
| `/v1/projects/{id}/github/links/{link_id}` | PATCH | Update token or poll interval |
| `/v1/projects/{id}/github/links/{link_id}` | DELETE | Unlink a repo |
| `/v1/projects/{id}/github/links/{link_id}/sync` | POST | Trigger manual sync |
| `/v1/projects/{id}/github/links/{link_id}/test` | POST | Test token validity |
| `/v1/projects/{id}/github/commits` | GET | List cached commits (supports `?q=`, `?link_id=`, `?limit=`, `?offset=`) |
| `/v1/projects/{id}/github/sync-backfill` | POST | Re-sync historical commits |
| `/v1/projects/{id}/github/token-health` | GET | Check token health |
| `/v1/projects/{id}/github/sync-status` | GET | Per-link sync status |
| `/v1/projects/{id}/github/readiness` | GET | Commit association readiness checklist |

## CRM

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/prospects` | GET | List prospects (supports `?stage=`, `?limit=`, `?offset=`) |
| `/v1/prospects` | POST | Create prospect |
| `/v1/prospects/{id}` | GET | Get prospect detail |
| `/v1/prospects/{id}` | PATCH | Update prospect |
| `/v1/prospects/{id}` | DELETE | Delete prospect |
| `/v1/prospects/{id}/stage` | PATCH | Change pipeline stage |
| `/v1/prospects/{id}/promote` | POST | Promote won prospect to client |
| `/v1/clients` | GET | List clients (supports `?limit=`, `?offset=`) |
| `/v1/clients` | POST | Create client |
| `/v1/clients/{id}` | GET | Get client detail |
| `/v1/clients/{id}` | PATCH | Update client |
| `/v1/clients/{id}/contacts` | GET | List client contacts |
| `/v1/clients/{id}/contacts` | POST | Add client contact |

## Admin

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/admin/users` | GET | List users (superuser only) |
| `/v1/admin/users` | POST | Create user (superuser only) |
| `/v1/admin/users/{id}` | PATCH | Update user (superuser only) |

## Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthz` | GET | Health check (DB liveness, version, uptime) |
