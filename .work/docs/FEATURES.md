# Features

tools-project is a project management hub with integrated CRM. All features are included in v0.1.0.

## Project Management

| Feature | Description |
|---------|-------------|
| **Projects** | Create and manage projects with custom keys (e.g., `PROJ`) for auto-generated task/ticket refs. |
| **Kanban Board** | Drag-and-drop task management with status columns (todo, in-progress, review, done). |
| **Task Detail** | Full task view with description, assignee, priority, due dates, comments, and linked commits. |
| **Task Refs** | Auto-generated human-readable refs (`PROJ-123`) for every task and ticket. |
| **Components** | Organize tasks within a project into components (e.g., Frontend, API, Docs). |
| **Tickets** | Support ticket queue with triage workflow, status tracking, and assignment. |

## Collaboration

| Feature | Description |
|---------|-------------|
| **Activity Feed** | Real-time activity stream per project with comments, mentions, and system events. |
| **Threaded Replies** | Nested comments on activities and ticket discussions (1 level deep). |
| **Mentions** | `@mention` users in comments — they get notified via their inbox. |
| **Markdown Editor** | Rich text editor with `@mention` autocomplete and `#ref` suggestions. |
| **Inbox** | Centralized inbox for mentions, triage-able items, and quick task/ticket creation. |
| **Watches** | Watch projects, tasks, or tickets to track changes. |

## GitHub Integration

| Feature | Description |
|---------|-------------|
| **Link Repos** | Connect multiple GitHub repositories per project using a personal access token. |
| **Commit Sync** | Background polling syncs commits from GitHub (configurable interval, default 5 min). |
| **Commit History** | Browse cached commits with SHA, message preview, author, and direct link to GitHub. |
| **Activity Cards** | GitHub commits appear in the activity feed with rich previews. |
| **Commit Picker** | "Cite commit" in comments and activity posts via a search-as-you-type picker. |
| **Task Linking** | Auto-link commits to tasks/tickets when commit messages contain refs (e.g., `PROJ-123`). |
| **Sync Health Dashboard** | Per-link error tracking, token validation, and sync status indicators. |
| **Backfill Sync** | Re-sync repos looking back up to 365 days. |
| **Token Encryption** | PATs encrypted at rest using Fernet symmetric encryption. |

## CRM Pipeline

| Feature | Description |
|---------|-------------|
| **Prospects** | Track sales leads through pipeline stages: target → connected → engaged → call scheduled → call done → proposal sent → negotiating → won/lost. |
| **Stage Transitions** | Validated transitions with business rules (e.g., `lost` is terminal). |
| **Prospect-to-Client** | Promote won prospects to full client records with a single click. |
| **Clients** | Company records with slug-based URL and industry classification. |
| **Client Contacts** | Manage contacts per client company with roles (contact, admin). |
| **Project Linking** | Link clients to projects for client-scoped work. |
| **Client Access Control** | Granular permissions per project: view, contribute, decision-maker, billing roles. |
| **Client Portal** | Separate login for client stakeholders with limited project visibility (tasks + public activity only). |

## Administration

| Feature | Description |
|---------|-------------|
| **User Management** | Single-page admin panel for managing users, roles, and project memberships. |
| **Auth Modes** | Standalone (local email/password), SSO (OAuth 2.0 + PKCE), or hybrid. |
| **Superuser Roles** | Admin users with elevated permissions for system-wide operations. |

## Attachments

| Feature | Description |
|---------|-------------|
| **File Uploads** | Attach files to tasks, tickets, and activities. |
| **Type Detection** | Content-type sniffing for security (images, PDFs, text). |
| **Quotas** | Per-project file count and byte total limits (configurable). |
| **Retention** | Automatic cleanup of expired attachments (configurable retention period). |

## Platform

| Feature | Description |
|---------|-------------|
| **Health Checks** | `/healthz` endpoint with database liveness verification. |
| **Request Tracing** | Every API response includes `X-Request-Id` for debugging. |
| **Pagination** | All list endpoints return `total` and `has_more` with offset support. |
| **Structured Logging** | Request logging with method, path, status, and duration. |
| **CI Pipeline** | Automated lint, type-check, and build on every push. |
