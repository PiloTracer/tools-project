# Tenancy model — users, projects, and login home

Canonical rules for how organizations (tenants), people, and projects relate in tools-project.

## Model (already in schema)

| Entity | Binding | Notes |
|--------|---------|--------|
| `tenants` | root org row (`slug`, `name`, `is_active`) | `default` is seeded on every API start |
| `users.tenant_id` | FK → tenant (nullable only for cross-tenant superusers) | Login JWT carries this tenant |
| `projects.tenant_id` | FK → tenant (NOT NULL) | Set on create; child rows inherit via project |
| CRM / webhooks / API keys | each has `tenant_id` | Same org boundary |

Tasks, tickets, activities, members, GitHub links, etc. do **not** carry their own `tenant_id`. They inherit isolation through `projects.tenant_id`.

## How a user “enters” a tenant on login

1. Bind the user: `users.tenant_id` = that tenant (Admin → Users → **Tenant slug**, or create with `tenant_slug`).
2. Turn on multi-tenant mode: `MULTI_TENANCY_ENABLED=true` in the env file for that compose mode (`.env.prd` / `.env.dev`).
3. On login, the API issues a JWT with that `tenant_id`. The web client stores the tenant cookie / `X-Tenant-Slug` so list/create calls stay inside the org.
4. Cross-tenant bootstrap admins keep `tenant_id IS NULL` and pick a tenant via subdomain or the tenant picker.

Without step 2, extra tenant rows exist but every write still resolves to `default` — isolation is not enforced.

## How projects belong to a tenant

- **New project:** stamped with the creator’s `tenant_id`, or (cross-tenant superuser) `tenant_slug` on `POST /v1/projects` / `X-Tenant-Slug`.
- **Existing project:** cross-tenant superuser `PATCH /v1/projects/{id}` with `{ "tenant_slug": "logicbison" }`.
- **Membership:** Admin → Users → add to project only works when user and project share the same tenant.

Slug uniqueness for projects is **per tenant** (`uq_projects_slug_tenant`).

## Operator checklist (LogicBison example)

1. Admin → Tenants → create slug `logicbison` (display name as needed).
2. Admin → Users → set that user’s **Tenant slug** to `logicbison` (or create the user with that slug).
3. Move or create projects under `logicbison` (`tenant_slug` on create/patch).
4. Add the user as a project member if they are not already.
5. Set `MULTI_TENANCY_ENABLED=true` and restart the stack so login/scoping enforce the binding.
6. User signs in → lands in LogicBison and only sees that org’s data.

All DDL for tenancy runs idempotently on API startup (`sql/schema_*.sql`); no manual SQL.

## Feature flag

| `MULTI_TENANCY_ENABLED` | Behavior |
|------------------------|----------|
| `false` (default) | Schema still has tenants; writes go to `default` unless an explicit `tenant_slug` is supplied on admin create/update |
| `true` | Subdomain / `X-Tenant-Slug` / JWT required; cross-tenant leak guards active |

Protected env files (`.env.prd`, compose) are not edited by agents unless you approve in-message.
