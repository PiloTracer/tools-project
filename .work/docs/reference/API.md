# API Reference — curated REST map

tools-project exposes a REST API at `/v1`. **The deployed build's `GET /docs` / `GET /openapi.json` is
authoritative**; this page is a curated map for orientation and is not exhaustive.

| Integration question | Read |
|----------------------|------|
| Another **application** integrates (identity, events, external refs, inbound automation) | [`APP_INTEGRATION.md`](APP_INTEGRATION.md) |
| A **coding agent** reads projects/tickets/comments/screenshots | [`../agent-query-api.md`](../agent-query-api.md) |
| **Repository** linking, commit sync, plan import | [`../tutorials/REPO_INTEGRATION.md`](../tutorials/REPO_INTEGRATION.md) |
| Which path do I need? | [`../guides/quick-reference-to-connect-agent-with-tools-project.md`](../guides/quick-reference-to-connect-agent-with-tools-project.md) |

## Authentication

| Surface | Credential |
|---------|-----------|
| Most `/v1/**` routes | `Authorization: Bearer <JWT>` (local login or OAuth) |
| `/v1/agent/**` | `X-Api-Key: tools_project_…` (superuser owner) **or** superuser Bearer |
| `/v1/platform/whoami` | personal API key **or** Bearer |
| `POST /v1/integrations/rfp/award` | `X-Webhook-Signature: sha256=<hmac>` (shared secret) |
| `POST /v1/admin/webhook-subscriptions` | **superuser** Bearer |

Full matrix and rules: [`APP_INTEGRATION.md` §2](APP_INTEGRATION.md#2-authentication-matrix).

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/auth/config` | GET | Auth mode configuration |
| `/v1/auth/local/login` | POST | Sign in with email + password (`200`, `300` on ambiguous tenant) |
| `/v1/auth/me` | GET | Current user profile |
| `/v1/me/keys` | GET/POST | List / create personal API keys (`plaintext` once) |
| `/v1/me/keys/{id}` | DELETE | Revoke a personal API key |

## Projects

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/projects` | GET/POST | List / create projects |
| `/v1/projects/{id}` | GET/PATCH | Project detail / settings (project key, GitHub registry) |
| `/v1/projects/{id}/members` | GET/POST | List / add members |
| `/v1/projects/{id}/members/{user_id}` | PATCH/DELETE | Change role / remove member |
| `/v1/projects/{id}/components` | GET/POST | Components |

## Tasks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/projects/{id}/tasks` | GET/POST | List (`?status=`, `?assignee_id=`, `?milestone_id=`, `?plan_state=`, `?limit=`, `?offset=`) / create |
| `/v1/tasks/{id}` | GET/PATCH/DELETE | Task detail / update / delete |
| `/v1/tasks/{id}/transition` | POST | Change status |
| `/v1/tasks/batch` | POST | Batch update |
| `/v1/projects/{id}/tasks/{task_id}/attachments` | POST | Upload to a task |

## Tickets

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/projects/{id}/tickets` | GET/POST | List (`?queue_slug=`, `?status=`, `?q=`, `?limit=`, `?offset=`) / create |
| `/v1/tickets/{id}` | GET/PATCH/DELETE | Ticket detail / update / delete |
| `/v1/tickets/{id}/transition` | POST | Change status |
| `/v1/tickets/batch` | POST | Batch update |
| `/v1/projects/{id}/tickets/{ticket_id}/attachments` | POST | Upload to a ticket |

## Attachments

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/projects/{id}/attachments` | POST | Upload a project-level file |
| `/v1/attachments/{id}` | GET | Download (JWT; streamed, mime allowlist, no `storage_key` exposed) |
| `/v1/attachments?ids=a,b,c` | GET | Batch metadata for feed rendering (max 50) |

Agents use the read-only equivalents in [`../agent-query-api.md`](../agent-query-api.md)
(`/v1/agent/attachments/{id}` — implemented, pending deployment).

## Activity

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/projects/{id}/activities` | GET/POST | List (`?subject_type=`, `?subject_id=`, `?kind=`, `?visibility=`, `?limit=`, `?offset=`) / post a comment |
| `/v1/projects/{id}/activities/stream` | GET (SSE) | Live feed hint (latest activity id, ~4 s poll) |

## Platform identity & ecosystem

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/platform/whoami` | GET | Caller + linked client companies |
| `/v1/projects/{id}/external-refs` | GET/POST | List / link an external object to a task or ticket |
| `/v1/projects/{id}/external-refs/{ref_id}` | DELETE | Remove the link |
| `/v1/admin/webhook-subscriptions` | GET/POST | List / create outbound webhook subscriptions (superuser) |
| `/v1/admin/webhook-subscriptions/{sub_id}` | DELETE | Remove a subscription |
| `/v1/integrations/rfp/award` | POST | Signed inbound award → prospect → client + onboarding project |

Event catalogue, signature contract and caveats: [`APP_INTEGRATION.md`](APP_INTEGRATION.md).

## CRM

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/prospects` | GET/POST | List (`?stage=`, `?limit=`, `?offset=`) / create |
| `/v1/prospects/{id}` | GET/PATCH/DELETE | Prospect detail / update / delete |
| `/v1/prospects/{id}/stage` | PATCH | Change pipeline stage |
| `/v1/prospects/{id}/promote` | POST | Promote a won prospect to client |
| `/v1/clients` | GET/POST | List / create clients |
| `/v1/clients/{id}` | GET/PATCH/DELETE | Client detail / update / delete |
| `/v1/clients/{id}/contacts` | GET/POST | Client contacts |

## GitHub

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/projects/{id}/github/links` | GET/POST | List / link repositories |
| `/v1/projects/{id}/github/links/{link_id}` | PATCH/DELETE | Update token/poll interval / unlink |
| `/v1/projects/{id}/github/links/{link_id}/sync` | POST | Trigger a sync |
| `/v1/projects/{id}/github/links/{link_id}/test` | POST | Test token validity |
| `/v1/projects/{id}/github/commits` | GET | Cached commits (`?q=`, `?link_id=`, `?limit=`, `?offset=`) |
| `/v1/projects/{id}/github/sync-backfill` | POST | Re-sync history |
| `/v1/projects/{id}/github/token-health` | GET | Token health |
| `/v1/projects/{id}/github/sync-status` | GET | Per-link sync status |
| `/v1/projects/{id}/github/readiness` | GET | Commit association readiness |
| `/v1/projects/{id}/github/task-registry` | GET | Current task-registry payload pushed to GitHub |

## Plans & milestones

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/projects/{id}/milestones` | GET/POST | List / create milestones |
| `/v1/milestones/{id}` | PATCH | Update a milestone |
| `/v1/projects/{id}/plan-import` | POST | Transactional plan import (milestones + tasks; dry-run supported) |

## Inbox, stats, reports

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/inbox` | GET/POST | List / create inbox items |
| `/v1/inbox/{id}/triage` | POST | Triage into a task or ticket |
| `/v1/inbox/{id}` | DELETE | Delete an inbox item |
| `/v1/stats/pipeline` · `/v1/stats/global` · `/v1/stats/me` | GET | Pipeline / deployment / personal stats |
| `/v1/reports/pipeline` · `/v1/reports/clients` · `/v1/reports/projects/{id}/tasks` · `/v1/reports/projects/{id}/tickets` | GET | Reports |
| `/healthz` | GET | Health check (DB liveness, version, uptime) |

## Admin

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/admin/users` | GET/POST | List / create users (superuser) |
| `/v1/admin/users/{id}` | PATCH | Update a user (superuser) |
| `/v1/admin/tenants` | GET/POST | List / create tenants (multi-tenant deployments) |
| `/v1/admin/tenants/{id}` | PATCH | Update a tenant |

## Errors

- `4xx` bodies are `{"detail": "…"}` (a string, or an array of `{loc, msg, type}` for 422 validation).
- New agent routes (1.1.0) use stable codes in `detail` (`ticket_not_found`, `attachment_not_found`);
  legacy routes use prose.
- Every response includes **`X-Request-Id`**; log and quote it when reporting failures.
- Retry only `429`/`5xx`/timeouts (backoff); do not retry `401`/`403`/`404`/`422` unchanged.

Full error contract, MCP error shape and retry table: [`../agent-query-api.md` §8](../agent-query-api.md#8-troubleshooting)
and [`APP_INTEGRATION.md` §7](APP_INTEGRATION.md#7-errors).
