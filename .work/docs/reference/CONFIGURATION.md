# Configuration Reference

All configuration is done via environment variables. Copy `.env.example` to `.env` and adjust.

## Stack Identity

| Variable | Default | Description |
|----------|---------|-------------|
| `COMPOSE_PROJECT_NAME` | `tools_project_dev` | Docker Compose project name (unique per clone) |
| `PUBLIC_HOST` | `localhost` | Browser-facing hostname |

## Ports

| Variable | Default | Description |
|----------|---------|-------------|
| `WEB_DEV_HOST_PORT` | `18513` | Next.js dev server port |
| `API_HOST_PORT` | `8300` | FastAPI port |
| `POSTGRES_HOST_PORT` | `55433` | PostgreSQL host port |

## Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_LOCAL_ENABLED` | `true` | Enable email/password login |
| `AUTH_OAUTH_ENABLED` | `true` | Enable OAuth 2.0 SSO |
| `JWT_SECRET` | `change_me...` | HMAC signing key for local JWT tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Token expiry in minutes (8h) |
| `BOOTSTRAP_ADMIN_EMAIL` | — | First superuser email (auto-created on empty DB) |
| `BOOTSTRAP_ADMIN_PASSWORD` | — | First superuser password |

## Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://prj:prj_dev_change_me@postgresql:5432/tools_project` | AsyncPG connection string |
| `SQL_SCHEMA_DIR` | `/sql` | Directory containing `schema_*.sql` files |
| `SQL_SCHEMA_APPLY` | `true` | Apply DDL on startup (set `false` for tests) |

## OAuth (SSO mode)

| Variable | Default | Description |
|----------|---------|-------------|
| `OAUTH_CLIENT_ID` | — | OAuth client ID |
| `OAUTH_CLIENT_SECRET` | — | OAuth client secret |
| `OAUTH_TOKEN_ENDPOINT` | — | Token exchange URL |
| `OAUTH_USER_INFO_ENDPOINT` | — | User info URL (API-side resolution) |
| `NEXT_PUBLIC_OAUTH_AUTHORIZATION_ENDPOINT` | — | Authorization URL (browser redirect) |
| `OAUTH_REDIRECT_URI` | — | Post-login redirect URI |
| `OAUTH_SCOPES` | `profile email` | OAuth scopes |
| `SESSION_COOKIE_NAME` | `prj_auth` | Session cookie name |
| `REFRESH_COOKIE_NAME` | `prj_refresh` | Refresh cookie name |

## Attachments

| Variable | Default | Description |
|----------|---------|-------------|
| `ATTACHMENTS_DIR` | `/data/attachments` | Filesystem path for uploaded files |
| `ATTACHMENT_MAX_PER_PROJECT` | `500` | Max files per project (0 = unlimited) |
| `ATTACHMENT_MAX_BYTES_PER_PROJECT` | `0` | Max total bytes per project (0 = unlimited) |
| `ATTACHMENT_RETENTION_DAYS` | `0` | Auto-delete files older than N days (0 = never) |

## GitHub Integration

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_SYNC_ENABLED` | `true` | Enable background commit polling |
| `GITHUB_POLL_INTERVAL_SECONDS` | `300` | Seconds between poll cycles |
| `GITHUB_POLL_INITIAL_DELAY_SECONDS` | `8` | Startup delay before first poll |
| `GITHUB_COMMITS_PER_SYNC` | `100` | Max commits per sync request |
| `GITHUB_TOKEN_ENCRYPTION_KEY` | — | Fernet key for PAT encryption (falls back to JWT_SECRET) |

## Health & Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `ATTACHMENT_RETENTION_PURGE_INTERVAL_SECONDS` | `3600` | Seconds between retention purge cycles |
