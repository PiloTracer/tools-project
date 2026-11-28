# Blueprint increment — 2026-11-27

## Build now (current API, Postgres, web UI)

Additive only. Existing create, board, status, and export paths keep their current results when the new fields are left empty.

| Feature | How |
|---|---|
| More boards | Idempotent template seeds: support queue, implementation, renewal |
| CRM edit history | Append-only `crm_field_changes` written on prospect/client PATCH |
| Custom fields | `custom_fields` JSON object on prospects and clients |
| Saved views | `users.ui_preferences.saved_views`, same account prefs API |
| Calendar | `/calendar` reads task due dates the user can already see |
| Gantt | `/projects/{id}/gantt` draws existing tasks; it does not move dates |
| Workload | `/workload` counts open tasks by assignee |
| Customer timeline | Client page lists recent activity on linked projects |
| Dependencies | `task_dependencies` rows; a cycle is rejected; dates stay put |
| Recurring tasks | Optional `weekly` or `monthly`. Closing a task once creates the next copy |
| Time and profitability | Time rows plus an optional project budget. No rates are assumed until a budget is saved |
| Report builder | Allowlisted group-by over prospects and clients. Unknown fields return 400 |
| Search | ⌘K keeps the current name match and also matches Postgres full text |

## Deferred (new runtime or outside account)

- Email and calendar sync (Gmail / Microsoft account)
- A workflow runner that must finish after the API process restarts
- A separate search server (OpenSearch, Elasticsearch, Typesense)

A workflow that only copies a project template when a prospect is won stays as it is today.
