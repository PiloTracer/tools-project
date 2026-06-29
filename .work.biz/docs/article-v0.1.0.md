# tools-project v0.1.0: Self-Hosted Project Management with Built-In CRM

**TL;DR:** tools-project is a free, self-hosted project management platform that combines Kanban task tracking, GitHub commit integration, and a full sales pipeline — all in one Docker Compose stack. No SaaS fees, no data leaving your servers.

---

## The Problem

Most teams juggle multiple tools: Jira or Linear for tasks, a separate CRM for sales, GitHub for code, Slack for discussions. This fragmentation means context is constantly lost. A sales rep closes a deal but the engineering team doesn't know the client is onboarded. A developer fixes a bug but the commit isn't linked to the ticket. Everyone is piecing together information from half a dozen windows.

## What tools-project Does

tools-project replaces that stack with a single, self-hosted application:

### 1. Project Management

Kanban boards for tasks, support ticket queues with triage workflows, threaded activity feeds, @mentions, and a centralized inbox. Every task and ticket gets a human-readable reference (e.g., `PROJ-123`) that works across the system.

### 2. GitHub Integration (The Killer Feature)

Link any number of GitHub repositories to a project. The system polls GitHub for new commits, displays them in the activity feed, and — crucially — automatically links commits to tasks and tickets when the commit message contains the reference (e.g., "Fixes PROJ-123"). The PAT is encrypted at rest. No webhooks required, no external services.

### 3. CRM Pipeline

Track prospects through a 9-stage pipeline from first contact to won/lost. When a deal closes, promote the prospect to a full client record with a single click. Manage client contacts, link clients to projects, grant granular access permissions, and let clients log in to see their project's progress via a restricted portal.

### 4. Dual Authentication

Works standalone (email/password with JWT) or integrated with any OAuth 2.0 provider. Both can run simultaneously for gradual migration.

## Architecture

The stack is deliberately simple:

- **Next.js 16** frontend (server components, App Router)
- **FastAPI** backend (async, SQLAlchemy 2.0)
- **PostgreSQL 16** (single database, no caching layer)
- **Docker Compose** (dev and production profiles)

Schema changes are idempotent SQL scripts — no Alembic, no migration headaches. The entire application starts in under 30 seconds on a fresh machine.

## What's Included in v0.1.0

- Full project CRUD with Kanban boards
- Task and ticket management with auto-generated refs
- Threaded activity feeds with @mentions and markdown
- GitHub repository linking with automatic commit sync
- Commit-to-task/ticket association (auto-detect refs in messages)
- 9-stage CRM pipeline with prospect-to-client promotion
- Client company and contact management
- Client portal with restricted project access
- Inbox for notifications and triage
- Watch/unwatch projects, tasks, and tickets
- Attachment upload with quotas and retention policies
- Admin panel for user management
- Dual auth (local + OAuth 2.0)
- Health checks, request tracing, structured logging
- CI pipeline with lint, type-check, and build
- Comprehensive documentation in-repo

## Getting Started

```bash
git clone <repo-url>
cd tools-project
cp .env.example .env
docker compose --profile dev up --build
```

That's it. Open http://localhost:18513, sign in with `admin@example.com` / `dev-bootstrap-change-me`, and start creating projects.

## Why Self-Host?

- **Data sovereignty** — everything stays on your infrastructure
- **No per-seat pricing** — add as many users as you need
- **Full control** — modify, extend, integrate however you want
- **Offline-capable** — no internet dependency for core functionality

## Future Directions

- Webhook-based GitHub sync (replacing polling for instant updates)
- Email notifications
- Calendar integration for pipeline follow-ups
- Rich reporting and dashboards
- OpenAPI-first plugin system

## Try It

The full source code, documentation, and setup guides are in the repository. All documentation lives in `.work/docs/` — quick start guides, feature overviews, tutorials, and complete configuration references.
