# Tenancy model — users, projects, and login home

Canonical rules for how organizations (tenants), people, and projects relate in tools-project.

## Model (already in schema)

| Entity | Binding | Notes |
|--------|---------|--------|
| `tenants` | root org row (`slug`, `name`, `is_active`) | `default` is seeded on every API start |
| `users.tenant_id` | FK → tenant (nullable only for cross-tenant superusers) | **Isolation key** for that person |
| `projects.tenant_id` | FK → tenant (NOT NULL) | Set on create; child rows inherit via project |
| CRM / webhooks / API keys | each has `tenant_id` | Same org boundary |

Tasks, tickets, activities, members, GitHub links, etc. do **not** carry their own `tenant_id`. They inherit isolation through `projects.tenant_id`.

## Isolation invariant (always on)

A user with `users.tenant_id` set **only** sees and writes data for that tenant:

- Prospects / clients / webhooks lists filter by that tenant
- Projects list requires membership **and** matching `projects.tenant_id`
- Project access denies cross-org projects even if an old membership row exists

Moving a user to `logicbison` does **not** move default’s prospects/projects with them. The new org starts empty until you create or move data into it.

Cross-tenant superusers (`tenant_id IS NULL`) can see/manage all orgs.

## Feature flag

| `MULTI_TENANCY_ENABLED` | What it controls |
|------------------------|------------------|
| `false` | No subdomain picker / 300 multi-choice login. Bound users are **still** isolated to their `tenant_id`. Cross-tenant admins stamp new rows into `default` unless they pass an explicit `tenant_slug`. |
| `true` | Subdomain / `X-Tenant-Slug` / tenant picker for admins; multi-choice login when one email exists in several orgs |

## How a user “enters” a tenant on login

1. Bind the user: Admin → Users → **Tenant slug** (or create with `tenant_slug`).
2. Sign out and sign in again (JWT must carry the new binding).
3. They only see that org’s CRM and projects. Empty org ⇒ empty lists (expected).

## How projects belong to a tenant

- **New project:** stamped with the creator’s `tenant_id`, or (cross-tenant superuser) `tenant_slug` / `X-Tenant-Slug`.
- **Existing project:** cross-tenant superuser Project Settings → **Tenant slug**, or `PATCH /v1/projects/{id}` with `{ "tenant_slug": "…" }`.
- **Membership:** Admin → Users → add to project only when user and project share the same tenant.

Slug uniqueness for projects is **per tenant** (`uq_projects_slug_tenant`).

## Operator checklist (LogicBison example)

1. Admin → Tenants → create slug `logicbison`.
2. Admin → Users → set that user’s **Tenant slug** to `logicbison`.
3. User signs out / in → Prospects/Clients empty until you create them under LogicBison (or move projects via Settings).
4. Optionally set `MULTI_TENANCY_ENABLED=true` for subdomain/picker UX.

All DDL for tenancy runs idempotently on API startup (`sql/schema_*.sql`); no manual SQL.
