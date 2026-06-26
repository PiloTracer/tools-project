# tools-project — project management

Internal **project hub**: projects, components, tasks/TODOs, support tickets, lightweight activity, and **GitHub** linkage.

## Authentication

| Deploy | `AUTH_LOCAL_ENABLED` | `AUTH_OAUTH_ENABLED` | Behavior |
|--------|----------------------|----------------------|-----------|
| **Standalone** | `true` | `false` | Email/password, bcrypt, JWT; superuser **local user admin** (`/v1/admin/users`, `/admin/users` in web). |
| **Integrated (SSO)** | `false` | `true` | **tools-dashboard** OAuth only (see **tools-rizervox** patterns). |
| **Hybrid** | `true` | `true` | User chooses SSO or local sign-in on `/login`. |

Public **`GET /v1/auth/config`** exposes which methods are active. Optional **`BOOTSTRAP_ADMIN_*`** seeds the first superuser when the DB is empty (use a valid email such as **`admin@example.com`**).

OAuth reference: **tools-rizervox** at `/mnt/work/Projects/tools-rizervox`, IdP at `/mnt/data/Projects/EPIC/tools-dashboard`.

## Tech stack

| Layer | Technology | Path |
|--------|------------|------|
| Web | Next.js 16, React 19, TypeScript | `web/` |
| API | Python 3.11, FastAPI, SQLAlchemy 2 async | `api/` |
| DB | PostgreSQL 16 | Compose service `postgresql` |
| Dev | Docker Compose (`profile: dev`) | `docker-compose.yml` |

## Quick start (Docker only)

```bash
cd /mnt/work/Projects/tools-project
# Optional: cp .env.example .env — set AUTH_*, JWT_SECRET, OAuth secrets
docker compose --profile dev up --build
```

- **App:** http://localhost:18513  
- **API:** http://localhost:8300/healthz — OpenAPI: http://localhost:8300/docs  
- **Postgres:** `localhost:55433` (default; see `POSTGRES_HOST_PORT`)

Default compose dev bootstrap (change in production): **`admin@example.com`** / **`dev-bootstrap-change-me`**.

### CI-style checks (web only, no API/DB)

```bash
docker compose run --rm --no-deps web sh -lc "npm ci --no-audit --no-fund && npm run check && npm run build"
```

### Shells

```bash
docker compose run --rm web sh
docker compose run --rm api sh
```

## OAuth notes (when enabled)

- Redirect URI registered in dashboard must match **`OAUTH_REDIRECT_URI`** (default `http://localhost:18513/oauth/complete`).
- **`PUBLIC_ORIGIN`** must match the hostname users type (avoid mixing `localhost` and `127.0.0.1`).
- PKCE uses **signed `state`** (no Redis). Use a real client secret (or `OAUTH_PKCE_STATE_SECRET`) outside toy dev.

## Documentation

| File | Contents |
|------|----------|
| `.work/context/CONTEXT.md` | Ports, stack, auth modes, OAuth |
| `.work/context/HANDOFF.md` | What exists + next steps |
| `.work/plans/legacy-plans/proposal/preliminary.md` | Product / UX brief |
| `api/README.md` | Auth API summary |

## Secrets

Never commit `.env`, `credentials/`, or tokens. Rotate **`JWT_SECRET`** and bootstrap passwords in production.

## Prueba de enlace de commit

Commit de prueba para verificar asociación automática con TPR-T-8.
