# Changelog

## v0.1.2 — 2026-06-29 (first public release)

This is the first public, tagged release of tools-project. It is a **first draft** that will be improved consistently and regularly.

### What is included in v0.1.2

- **Project management:** Projects, Kanban boards, tasks, support tickets, threading, @mentions, activity feeds, inbox, watches.
- **CRM pipeline:** 9-stage prospect pipeline, prospect-to-client promotion, client contacts, client portal, granular access roles (view/contribute/decision-maker/billing).
- **GitHub integration:** Multi-repo linking per project, encrypted PAT storage (Fernet), background commit sync, commit picker, commit-to-task auto-association, backfill (365 days), sync health dashboard.
- **AI-agent-friendly commits:** `prepare-commit-msg` git hook + `commit_subject_refs` — commits by humans **and** AI coding agents auto-link to tasks/tickets.
- **Auth:** Dual-mode — local (email/password + JWT) or OAuth 2.0 + PKCE; both can run simultaneously.
- **Platform:** Health checks, request tracing, pagination on all lists, structured logging, CI pipeline (lint + type-check + build).
- **Documentation:** Quick start, feature overview, architecture, 4 guides (auth/github/crm/admin), 2 tutorials, 3 reference docs (config/docker/api).
- **Agent OS frameworks:** Built using `.ai` (Agent OS), `.ai.ui` (UI Design OS), `.ai.biz` (Business OS) for structured planning, spec, implementation, and verification.

### What is deliberately not here (next on the roadmap)

- GitHub webhook integration (replacing polling for instant updates)
- Email and calendar notifications
- Mobile-friendly surfaces
- Reporting dashboards
- Richer onboarding checklists
- OpenAPI-first plugin system

### License

MIT — free for personal and commercial use.

**Live demo:** <https://logicbison.com/work/tools-project-hub>  
**Repository:** <https://github.com/PiloTracer/tools-project>

---

## 2026-06-29 — Admin tools & GitHub association

### Admin page overhaul
- New single-page user administration with role review — manage users, roles, and permissions from one screen.
- Contact linking and project membership management added to admin page.
- Fixed bugs: API returning 422 on some admin actions, self-deactivation allowed, theme colors inconsistent, checkboxes too small.

### GitHub commit association pipeline
- Commits can now be linked to tasks and tickets. The system auto-detects refs (e.g. `PROJ-123`) in commit messages and creates links.
- GitHub Sync Health Dashboard: per-link error tracking, sync-status endpoint, and a dashboard view that shows token validity and sync health.
- Token health checks are cached (5 min) and resilient to transient GitHub failures (rate limits, timeouts).
- Commit card components show linked refs in activity feeds and detail views.
- `LinkedCommitsList` added to task and ticket detail pages.
- Backfill sync lets admins re-sync all repos looking back up to 365 days.
- Commit-to-task linking works with local-first pending refs (works even before GitHub sync completes).

### UI polish
- Copy-Ref button added to all task and ticket list views for quick reference copying.
- Board/Table toggle added to tickets view, reusing the KanbanBoard component.
- CRM dashboard widget added to the home page for at-a-glance pipeline status.
- GitHub tab dates now render in the browser's local timezone instead of server timezone.
- GitHub commit activity cards show rich metadata (SHA, repo, preview, html_url).
- "Convert to client" button and dialog added on prospect promotion (won stage).
- Linked items dialog shows full subject details (description, priority, status).

### GitHub task registry
- Task registry (`GET /v1/projects/{id}/github/task-registry`) exposes all tracked tasks/tickets to the AI agent for automatic commit ref detection.
- Registry supports task and ticket types with configurable auto-prefix.
- `prepare-commit-msg` git hook automatically prepends task refs to commit subjects.

### API & schema
- Sync error state is now persisted on manual sync failures (not just background poll).
- `commit_subject_refs` table and router for normalized cross-linking.
- `subject_refs` are enriched with description, priority, and status in API responses.
- Registry fallback for cross-environment ref resolution.
- Project key uniqueness enforced on PATCH (409 on conflict).

## 2026-06-23 — CRM promotion flow

- Prospect-to-client promotion: stage transition now returns the created client record on "won". Frontend shows a success dialog with "View client" link.
- Both board view and detail view handle promotion flow.
- All mock/seed data inserts removed — clean production-ready fixtures.

## 2026-06-20 — GitHub integration (Batch I)

- Full GitHub integration: link multiple repos per project, background polling, commit caching.
- GitHub tab on project page with paginated commit history table.
- Commit activity cards in the activity feed with rich SHA/preview rendering.
- Commit picker component ("Cite commit") in activity composer and reply forms.
- GitHub settings section in project settings: add/remove repos with PAT authentication.
- Tokens encrypted at rest using Fernet symmetric encryption.
- Sync backfill endpoint for re-syncing historical commits.
- Background poll loop with configurable interval, error handling, and per-link transactions.

## 2026-06-19 — CRM clients & contacts

- Client companies, contacts, and project-client linking implemented.
- Client portal: separate login, limited project view (tasks + public activity only).
- Client participant access control: `is_internal = false` visibility boundary enforced.
- Company-scoped visibility: client participants see tasks/tickets from all contacts in their company (SPEC FR-5).
- API endpoints for clients, client contacts, project-client links, and access grant/revoke.
- Seed data for demo client user (Alice, Umbrella Corp) with project grants.

## 2026-06-18 — CRM prospects pipeline

- Prospects CRUD with stage transitions (`target` → `won`/`lost`).
- Business rules: `lost` is terminal, cannot skip stages.
- Pipeline service for prospect-to-client promotion.
- 5 new database tables: `prospects`, `clients`, `client_contacts`, `project_clients`, `project_client_access`.
- Schema indexes and constraints for data integrity.

## 2026-06-15 — Activity & GitHub polish

- GitHub commit activity deduplication — only genuinely new commits generate activity entries.
- `q` search param on `GET /v1/projects/{id}/github/commits`.
- Attachment retention purge hook wired (runs on background poll cycle).
- App logger startup markers added for observability.
