# Foundation doc 01 — Product scope

**Brownfield synthesis 2026-06-18:** Synthesized from `README.md`, `preliminary.md`, `CONTEXT.md`, and `20260515-full-project.md`. Labeled **Inference** where not directly cited.
**See also:** [`20260618-04-architecture.md`](20260618-04-architecture.md) — architecture foundation, bounded contexts, ADR register.

## Product intent (one sentence)

A **project management hub with integrated CRM** that replaces the current internal work-tracking toolchain. Users organize work into projects (optional client-scoped), track tasks and tickets, collaborate via threaded activity, and manage client relationships through a sales-to-delivery pipeline.

## In scope

| Domain | What it includes | Evidence |
|--------|-----------------|----------|
| **Project management** | Projects, components, tasks, Kanban, task detail, refs (`#PROJ-123`) | Code: `web/src/components/KanbanBoard.tsx`, `api/app/routers/projects.py` |
| **Support tickets** | Ticket lifecycle, queues, assignments, status | Code: `api/app/routers/tickets.py` |
| **Activity stream** | Threaded activity, attachments, mentions, SSE hints | Code: `api/app/routers/activities.py`, `api/app/services/activity_writer.py` |
| **Collaboration** | Markdown editor, `@mention`, `#ref`, watch, inbox | Code: `web/src/components/MarkdownEditor.tsx` |
| **GitHub integration** | Link repos, cache commits, background poll, activity feed | Code: `api/app/routers/github.py`, `api/app/github_background.py` — see NEXT.md § Batch I |
| **CRM / Clients** (planned) | Client companies, contacts, sales pipeline stages, project-client linking, limited client access to projects | Proposal: `.work/plans/proposals/tracking-system-spec.md` |
| **Auth** | Dual local + OAuth, JWT, superuser admin | Code: `api/app/routers/auth.py`, `api/app/services/auth_local.py` |

## Out of scope (initial)

- Generic public SaaS signup
- Full GitHub replacement (issues, PRs, CI)
- Replacing tools-dashboard for identity
- Multi-tenant isolation (single-org tool)
- Mobile native apps

## Audience / personas

| Persona | Needs |
|---------|-------|
| **IC (engineer)** | Today's tasks, quick notes, images on tickets, speed |
| **Lead** | Project health per component, ticket aging, GitHub signal, team activity |
| **Admin** | User management, deployment config, OAuth setup |
| **Client stakeholder** (planned) | Project progress, own tasks, limited visibility, contact management |
| **Sales/biz dev** (planned) | Pipeline stages, prospect tracking, weekly metrics, referrals |

## Assumption ledger

| # | Assumption | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Single-org deployment (no multi-tenant) | **Confirmed** | No tenant_id in any table, flat user model |
| 2 | Client CRM is the same product, not separate | **Confirmed** | User chose "same product — expand tools-project" |
| 3 | Clients have limited project access distinct from team members | **Confirmed** | ADR-0001 + clients-participants SPEC define `project_client_access` separate from `project_members` |
| 4 | Sales pipeline stages (1-9) match the tracking-system-spec proposal | **Confirmed** | clients-participants SPEC defines `target` → `won`/`lost` stages matching the proposal |

## Risks

- Permission model becomes significantly more complex when adding client-scoped access alongside internal team roles
- GitHub integration (Batch I) is still partial — the web UI is not built, which may conflict with CRM priorities
