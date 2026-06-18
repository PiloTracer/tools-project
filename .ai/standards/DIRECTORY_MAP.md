# Directory map — tools-project

**Brownfield synthesis 2026-06-18:** Inferred from code tree.

## Repository layout

```
/
├── .ai/                    # Agent OS framework (skills, standards, concepts)
│   ├── skills/             # Portable agent skill definitions
│   ├── standards/          # CONVENTIONS, FEATURE_STANDARD, DIRECTORY_MAP
│   └── concepts/           # MOD-01–MOD-06 concept prompts
├── .work/                  # Project-specific working artifacts
│   ├── context/            # HANDOFF.md, CONTEXT.md
│   ├── plans/              # NEXT.md, foundation/, full/, registries
│   ├── decisions/          # ADRs
│   ├── features/           # Feature SPECs
│   └── proposals/          # Proposals under evaluation
├── api/                    # FastAPI backend
│   └── app/
│       ├── models/         # SQLAlchemy models (one per entity)
│       ├── routers/        # API route handlers (one per context)
│       ├── services/       # Business logic
│       └── main.py         # FastAPI app entrypoint
├── web/                    # Next.js 16 frontend
│   └── src/
│       ├── app/            # App Router pages + API BFF routes
│       ├── components/     # Reusable React components
│       └── shared/         # Shared types, server utilities
├── sql/                    # Idempotent DDL/DML schema files
├── bin/                    # Dev scripts (start.sh)
├── docker-compose.yml
└── .cursorrules
```

## Bounded contexts → directories

| Context | API dir | Web dir | Key models |
|---------|---------|---------|------------|
| Auth | `api/app/routers/auth.py` | `web/src/app/login/`, `oauth/` | `users` |
| Projects | `api/app/routers/projects.py` | `web/src/app/projects/` | `projects`, `project_members`, `components` |
| Tasks | `api/app/routers/tasks.py` | `web/src/app/projects/[id]/tasks/` | `tasks` |
| Tickets | `api/app/routers/tickets.py` | `web/src/app/projects/[id]/tickets/` | `tickets` |
| Activity | `api/app/routers/activities.py` | `web/src/components/MarkdownEditor.tsx` | `activities`, `mentions`, `attachments` |
| Inbox | `api/app/routers/inbox.py` | `web/src/app/inbox/` | `inbox_items`, `watchers` |
| GitHub | `api/app/routers/github.py` | (not yet built) | `github_links`, `github_commits` |
| CRM | (planned) | (planned) | `clients`, `client_contacts` (planned) |
