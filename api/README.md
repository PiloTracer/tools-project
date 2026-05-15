# tools-project API

FastAPI service for the internal project hub. Run in Docker (see repo root).

## Endpoints (bootstrap)

| Path | Purpose |
|------|---------|
| `GET /healthz` | Liveness |
| `GET /v1/auth/config` | Which auth methods are enabled (`local_enabled`, `oauth_enabled`) |
| `POST /v1/auth/local/login` | Email + password → JWT (`token_typ: local`) |
| `GET /v1/auth/me` | Current user (Bearer **local** JWT) |
| `GET/POST/PATCH /v1/admin/users` | User CRUD (**local superuser** only) |
| `GET /docs` | OpenAPI |

## Auth modes (env)

| Variable | Meaning |
|----------|---------|
| `AUTH_LOCAL_ENABLED` | Email/password users + JWT + `/v1/admin/users` |
| `AUTH_OAUTH_ENABLED` | For the Next app: tools-dashboard OAuth flows (**web** enforces; API still accepts local JWT) |
| `JWT_SECRET` | HMAC key for local JWTs — **rotate in production** |
| `BOOTSTRAP_ADMIN_*` | If DB is empty and local auth on, create first superuser (optional) |

**Standalone** deploy: `AUTH_LOCAL_ENABLED=true`, `AUTH_OAUTH_ENABLED=false`.  
**Integrated** (tools-dashboard): OAuth on; usually `AUTH_LOCAL_ENABLED=false` unless you want **hybrid** (both).

Projects / tickets APIs should accept **local** JWTs first; validating **dashboard** OAuth tokens against JWKS is a follow-up for unified `Authorization` handling.
