# Foundation doc 04 — Architecture foundation

**Brownfield synthesis 2026-06-18:** Synthesized from code tree, `CONTEXT.md`, `docker-compose.yml`, and model files. Labeled **Inference** where inferred from code patterns.

## Bounded contexts

```
┌─────────────────────────────────────────────────────────────┐
│                   tools-project (monolith)                    │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Auth   │  │ Projects │  │  GitHub  │  │   CRM    │   │
│  │          │  │          │  │          │  │ (planned)│   │
│  │ local +  │  │ tasks    │  │ link     │  │          │   │
│  │ OAuth    │  │ tickets  │  │ commits  │  │ clients  │   │
│  │ JWT      │  │ activity │  │ poll     │  │ contacts │   │
│  │          │  │ inbox    │  │          │  │ pipeline │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Shared infrastructure                 │   │
│  │  DB (PostgreSQL), Auth (JWT/OAuth), API (FastAPI),   │   │
│  │  Web (Next.js 16), Docker Compose                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Tech stack

| Layer | Technology | Path |
|-------|-----------|------|
| Web | Next.js 16 App Router, React 19, TypeScript | `web/` |
| API | FastAPI, SQLAlchemy 2 async, asyncpg, httpx | `api/` |
| DB | PostgreSQL 16 | `sql/` schema files |
| Auth | JWT (local) + OAuth 2.0 PKCE (tools-dashboard) | Env-driven |
| Infra | Docker Compose (profile: dev) | `docker-compose.yml` |
| Dev script | `bin/start.sh` (Compose wrapper with menu) | `bin/start.sh` |

## Key architectural decisions (current)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| DB schema | Idempotent SQL files (`schema_*.sql`), no Alembic | Simpler than migration framework; re-runnable on every startup |
| Auth tokens | Local JWT (HMAC) or OAuth access token resolved via user-info endpoint | Flexible deployment: standalone without OAuth IdP |
| Project membership | Role-based (owner/maintainer/contributor/viewer) via `project_members` join | Simple, enough for internal teams |
| PAT storage | Fernet-at-rest encryption using `GITHUB_TOKEN_ENCRYPTION_KEY` or JWT-derived key | No plaintext tokens in DB |
| GitHub polling | Background httpx loop with configurable interval; webhooks deferred | MVP pragmatism: fewer moving parts |
| Activity stream | SSE hints (not full WebSocket) for live updates | Simpler infra; hints trigger client re-fetch |

## Architectural decisions needed (CRM domain)

| Question | Options | Status |
|----------|---------|--------|
| Client contact identity | Same `users` table with flag vs separate `client_contacts` table | **Decided** — separate `client_contacts` with optional `user_id` FK (ADR-0001) |
| Project-client relationship | `project.client_id` FK vs many-to-many join table | **Decided** — `project_clients` many-to-many join table (ADR-0001) |
| Client access model | New `project_client_access` table vs extending `project_members` with type flag | **Decided** — dedicated `project_client_access` table (ADR-0001) |
| Sales pipeline entity | `clients` table with `pipeline_stage` vs separate `prospects` table | **Decided** — separate `prospects` table; auto-create `clients` on `won` (ADR-0001) |
| Client contact auth | System user account per contact vs shared access | **Decided** — individual `users` account per contact (ADR-0001) |

## Bounded context boundaries

### Auth context
- **Models:** `users` table
- **API:** `api/app/routers/auth.py`, `api/app/routers/admin_users.py`
- **Services:** `api/app/services/auth_local.py`
- **Deps:** `api/app/deps.py` (current user resolution, superuser check)

### Projects context
- **Models:** `projects`, `project_members`, `components`, `tasks`, `tickets`
- **API:** `api/app/routers/projects.py`, `tasks.py`, `tickets.py`
- **Services:** `api/app/services/project_access.py` (role resolution, membership checks)

### Activity context
- **Models:** `activities`, `mentions`, `attachments`, `inbox_items`, `watchers`
- **API:** `api/app/routers/activities.py`, `inbox.py`
- **Services:** `api/app/services/activity_writer.py`

### GitHub context
- **Models:** `github_links`, `github_commits`
- **API:** `api/app/routers/github.py`
- **Services:** `api/app/services/github_sync.py`, `api/app/services/github_token_crypto.py`
- **Background:** `api/app/github_background.py`

### CRM context (planned)
- **Models:** `prospects`, `clients`, `client_contacts`, `project_clients`, `project_client_access`, `client_referrals`, `client_onboarding_items` (not yet created)
- **API:** Not yet created
- **Services:** Not yet created
