# Product brief — tools-project (project management hub)

## Summary

**tools-project** is an internal **project management system** that makes it easy to plan work, capture feedback, and track support—without heavy ceremony. Users sign in through the existing **tools-dashboard** identity (OAuth 2.0); the app does not replace the org IdP.

## Goals

1. **Structure work** — **Projects** contain **components** (streams of work, teams, or subsystems) and **tasks** / **TODOs** with clear ownership and status.
2. **Support intake** — **Support tickets** with lifecycle separate from internal tasks when policies require it; unified **tracking** (queues, dates, assignee, outcomes).
3. **Low-friction collaboration** — Fast entry for **text**, **images**, **feedback**, and **follow-ups** (threaded activity, attachments, minimal clicks).
4. **GitHub** — Link repositories to a **project** or **component**; show **recent commits** / messages in context (MVP scope: read-only listing or polling; webhooks later).
5. **Strategic design** — Clean domain boundaries (project vs component vs task vs ticket vs activity); APIs and UI that stay maintainable as scope grows.

## Authentication (deployment)

- **Standalone:** **Local users** only — email/password, bcrypt, JWT; **superuser** manages accounts via **`/v1/admin/users`** (and future UI).
- **Integrated:** **tools-dashboard** OAuth (PKCE); typically no local user store, or **hybrid** if both flags are on.
- Configuration: **`AUTH_LOCAL_ENABLED`**, **`AUTH_OAUTH_ENABLED`**, **`JWT_SECRET`**, optional **`BOOTSTRAP_ADMIN_*`**. See **`.ai/context/CONTEXT.md`**.

## Non-goals (initial)

- Replacing **tools-dashboard** for authentication or user administration.
- Full GitHub replacement (issues-only duplication, heavy CI orchestration) — integrate where it reduces context switching.
- Generic public SaaS signup; this is an **org-internal** tool unless product direction changes.

## Personas (typical)

- **IC** — Needs today’s tasks, quick notes, and images on tickets; cares about speed.
- **Lead** — Needs project/component health, ticket ageing, and GitHub signal per initiative.
- **Support** — Needs ticket queues, customer-safe notes vs internal notes (policy TBD in implementation).

## Experience principles

- **Ease of use first** — Default flows are short; power features don’t block basics.
- **Traceability** — Activity history is first-class; audits where the org requires them.
- **Consistent with sibling tools** — OAuth, env conventions, and Docker patterns align with **tools-rizervox** / dashboard docs.

## Technical anchors

- **Authentication:** **Configurable** — **local** users (bcrypt + JWT + `/v1/admin/users`) for **standalone** deploys; **tools-dashboard OAuth** (PKCE) when **`AUTH_OAUTH_ENABLED=true`**. Hybrid supported. See **`AUTH_LOCAL_ENABLED`**, **`JWT_SECRET`**, **`BOOTSTRAP_ADMIN_*`** in `.env.example`.
- **Fully Dockerized** local development; distinct **host ports** from other stacks on the same machine.
- **Stack in repo:** **Next.js 16** (`web/`) + **FastAPI** + SQLAlchemy async + **PostgreSQL 16** (Compose). **Schema:** declarative **`sql/`** scripts on startup (**no Alembic** — see `.cursorrules`). GitHub integration remains follow-on work; see `.ai/context/CONTEXT.md`.

## References

- IdP repo path: `/mnt/data/Projects/EPIC/tools-dashboard`
- Reference client: `/mnt/work/Projects/tools-rizervox`
- Stable context: `.ai/context/CONTEXT.md`
