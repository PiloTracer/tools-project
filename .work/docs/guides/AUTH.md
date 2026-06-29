# Authentication Guide

tools-project supports three authentication modes, controlled by environment variables.

## Modes

### Standalone (Local Auth)

Uses email/password with JWT tokens. No external dependencies.

```env
AUTH_LOCAL_ENABLED=true
AUTH_OAUTH_ENABLED=false
JWT_SECRET=generate_a_long_random_secret
```

- Users are managed via the admin panel (`/admin/users`) or API (`/v1/admin/users`).
- Passwords are hashed with bcrypt.
- JWT tokens use HS256 with configurable expiry (default 8 hours).

### Integrated (OAuth/SSO)

Uses an external OAuth 2.0 provider with PKCE. Designed for tools-dashboard but compatible with any OAuth 2.0 provider.

```env
AUTH_LOCAL_ENABLED=false
AUTH_OAUTH_ENABLED=true
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
OAUTH_TOKEN_ENDPOINT=https://your-idp.com/oauth/token
OAUTH_USER_INFO_ENDPOINT=https://your-idp.com/api/users/me
```

- The login page shows an SSO button instead of a local login form.
- User info is resolved from the OAuth provider on every request (no local session).
- Users are auto-provisioned (upserted) on first login.

### Hybrid

Both local and OAuth auth enabled simultaneously. The login page shows both options.

```env
AUTH_LOCAL_ENABLED=true
AUTH_OAUTH_ENABLED=true
```

## API Auth

All API requests must include an `Authorization: Bearer <token>` header, where the token is either:
- A **local JWT** obtained from `POST /v1/auth/local/login`
- An **OAuth access token** from the configured provider

The login flow sets `prj_auth` (session) and `prj_refresh` (refresh) cookies automatically.

## Client Portal Auth

Client stakeholders have a separate login at `/client/login`. They authenticate the same way (local or OAuth) but are scoped to only see projects they have been granted access to.
