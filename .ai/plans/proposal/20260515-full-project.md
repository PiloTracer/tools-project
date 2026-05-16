# tools-project — Full Project Plan (MVP)

**Document date:** 2026-05-15
**Status:** Proposal / north-star for MVP. Supersedes nothing; complements `preliminary.md` and `estimate/plan.md`.
**Scope:** Greenfield delivery of the **project management hub** on the existing boilerplate (Next.js 16 + FastAPI + PostgreSQL 16, dual auth).

> TL;DR — A keyboard-first, low-friction PM hub: **Projects → Components → Tasks**, **Support tickets** with a separate lifecycle, an **activity stream** (text + images + threads) as the connective tissue, and **GitHub** signal in-context. Fast to scan, fast to capture, easy to scale.

---

## 1. Vision

A **project-management hub** that engineering, support and leads actually *want* to use because it is:

1. **Fast** — `⌘K` command palette, keyboard-first task capture, "type and go" notes with `/`-commands.
2. **Calm** — A clear hierarchy (Project → Component → Task) with one **Activity** stream gluing tickets, tasks, GitHub events and human notes together.
3. **In-context** — Linked **GitHub** commits/PRs appear next to the work they describe, not in a separate tab.
4. **Honest about state** — Auto-computed **project health badges** (open work, aging tickets, last activity, blocked-by) instead of stale "status: green" labels.
5. **Deployable two ways** — Standalone with local users, or integrated behind **tools-dashboard** OAuth (already wired).

---

## 2. What makes the MVP "cool" (the opinionated bits)

| # | Feature | Why it matters |
|---|---------|----------------|
| 1 | **`⌘K` command palette** | Jump to any project/component/task, run actions ("new task in X", "assign to me", "close ticket"), search everywhere. |
| 2 | **Quick Capture inbox** | `c` from anywhere → write a thought / drop an image → triage later into project/task/ticket. Zero-friction is the whole point. |
| 3 | **Markdown + `/`-commands everywhere** | `/task`, `/todo`, `/img`, `/mention`, `/code`. Notes are first-class but compose to structured items. |
| 4 | **Live Activity stream** | Tasks, tickets, commits, comments — chronological, threaded, with image attachments. SSE for live updates (no full WebSocket infra needed for MVP). |
| 5 | **Project Health Card** | Auto-derived signals: open vs done tasks, ticket age P50/P95, days since last activity, "blocked" count, last commit on linked repo. No manual status fields. |
| 6 | **Kanban + Table dual view** | Tasks board for ICs, table view for leads. Same data, different lens. Saved views per user. |
| 7 | **Cross-refs `#PRJ-123` / `@user`** | Auto-linked in any markdown body. Mentions create activity entries. |
| 8 | **GitHub commit lane** | Per-project (or per-component) feed of recent commits; click → diff link on GitHub. Polling first, webhooks later. |
| 9 | **"Today" / "My Focus" page** | Personal home: assigned tasks due ≤ today, mentions, watched tickets, recent activity. The page most users will live on. |
| 10 | **Dark + light themes** out of the box | Aligned visually with `tools-dashboard` / `tools-rizervox` so the org feels like one product family. |

---

## 3. Users & primary jobs

| Persona | Top job-to-be-done | "Done" looks like |
|---------|--------------------|-------------------|
| **IC engineer** | "What do I owe today?" + "Capture this idea before I lose it." | `/today` shows their plate; `c` to capture in <3s. |
| **Lead / PM** | "Which projects are healthy? Where is risk?" | Project list with health badges; ticket-age table; per-project activity. |
| **Support** | "Triage and progress tickets without losing context." | Ticket queue with SLA-style age, internal vs external notes, fast image paste. |
| **Admin / Ops** | "Who can do what, and is the deployment healthy?" | `/admin/users` (extend with forms), `/healthz`, audit log. |

---

## 4. Domain model (MVP)

Entities and the relationships we will actually build. *Italicised fields are MVP "nice but optional"; everything else is in scope.*

### 4.1 Core entities

| Entity | Key fields | Notes |
|--------|------------|-------|
| **User** | `id`, `email`, `display_name`, `is_superuser`, `is_active`, `auth_source` (`local`/`oauth`), `avatar_url?` | Exists; extend with `display_name`, `avatar_url`. |
| **Project** | `id`, `key` (e.g. `PRJ`, used in refs), `name`, `slug`, `description_md`, `status` (`active`/`archived`), `created_by`, timestamps | `key` is the human-facing prefix for `#PRJ-123`. |
| **ProjectMember** | `project_id`, `user_id`, `role` (`owner`/`maintainer`/`contributor`/`viewer`) | RBAC scope #1. |
| **Component** | `id`, `project_id`, `key` (e.g. `WEB`), `name`, `description_md`, `lead_user_id?` | Optional sub-grouping within a project. |
| **Task** | `id`, `project_id`, `component_id?`, `ref` (`PRJ-123`), `title`, `body_md`, `status` (`todo`/`in_progress`/`blocked`/`done`/`cancelled`), `priority` (`low`/`med`/`high`/`urgent`), `assignee_id?`, `reporter_id`, `due_at?`, `parent_task_id?`, `is_todo` (bool), `created_at`, `updated_at`, `closed_at?` | Single `Task` table covers both **tasks** and **TODOs** (the latter is just `is_todo=true`, lighter weight, optionally orphaned at project level). |
| **Ticket** | `id`, `project_id`, `ref` (`PRJ-T-45`), `title`, `body_md`, `status` (`open`/`in_progress`/`waiting_customer`/`resolved`/`closed`), `priority`, `requester_email?`, `assignee_id?`, `opened_at`, `first_response_at?`, `resolved_at?`, `closed_at?` | Separate lifecycle from `Task` so support policy can diverge. |
| **Activity** | `id`, `actor_user_id?` (null = system), `kind` (`comment`/`status_change`/`assignment`/`attachment`/`github_commit`/`mention`/`system`), `subject_type` (`project`/`component`/`task`/`ticket`), `subject_id`, `parent_activity_id?` (threaded replies), `body_md?`, `meta_json?`, `created_at` | The connective tissue. |
| **Attachment** | `id`, `activity_id?` *or* `task_id?` / `ticket_id?`, `filename`, `mime`, `size_bytes`, `storage_key`, `created_by`, `created_at` | MVP: filesystem volume (`/data/attachments`) behind API; design leaves room for S3/MinIO later. |
| **Mention** | `id`, `activity_id`, `mentioned_user_id` | Drives "Today / My Focus". |
| **Watcher** | `subject_type`, `subject_id`, `user_id` | "Watch this project/task/ticket" for notifications/focus. |
| **GithubLink** | `id`, `project_id?`, `component_id?`, `owner`, `repo`, `installation_token_ref?`, `last_synced_at?`, `last_seen_sha?` | One repo can be linked to a project or, more granularly, a component. |
| **GithubCommit** *(cache)* | `id`, `github_link_id`, `sha`, `author_name`, `author_email`, `message`, `committed_at`, `html_url` | Local mirror so the activity stream is fast and offline-friendly. |
| **AuditLog** | `id`, `actor_user_id?`, `action`, `target_type`, `target_id`, `meta_json?`, `created_at` | Admin actions, auth events, destructive ops. |

### 4.2 Identifiers

- Human refs are **`{PROJECT_KEY}-{N}`** for tasks (`PRJ-123`) and **`{PROJECT_KEY}-T-{N}`** for tickets (`PRJ-T-45`).
- Per-project monotonic counters in a small `project_counters` table (separate counters for tasks vs tickets) keep refs readable even under concurrency.

### 4.3 Diagram (text)

```
User ── ProjectMember ──► Project ──► Component ──► Task ──► Activity ──► Attachment
                          │            │           │           ▲              
                          │            └──► Task ──┘           │              
                          ├──► Ticket ─────────────────────────┤              
                          └──► GithubLink ──► GithubCommit ────┘              
```

---

## 5. Feature set — what's in MVP vs after

### 5.1 In MVP

**Auth & users** *(already partly built)*
- Local login + OAuth login (existing).
- Extend `User` with `display_name`, `avatar_url`.
- `/admin/users` form-based create/edit/deactivate (today: read-only table).

**Projects & components**
- Create / edit / archive **Project** with `key`, `name`, `slug`, description (markdown).
- Add / remove **members** with roles (`owner` / `maintainer` / `contributor` / `viewer`).
- Create / edit **Components** under a project.

**Tasks & TODOs**
- Create task with title, optional body, component, assignee, priority, due date, parent.
- Status flow with keyboard shortcuts (`1` todo, `2` in-progress, `3` blocked, `4` done).
- **Kanban view** (drag between statuses) and **Table view** (sortable, filterable).
- Sub-tasks (one level deep is enough for MVP).
- Lightweight **TODOs** at project level (`is_todo=true`) for jot-it-down items.

**Tickets**
- Create / list / detail with status flow and priority.
- **Queue view** sorted by age + priority.
- Internal vs external note distinction on activity entries (boolean `is_internal` on `Activity`).
- Simple **age signals** (color when > N days without movement; N configurable per project, defaults reasonable).

**Activity stream**
- Per subject (project / component / task / ticket) and a project-wide rollup.
- Markdown body, **paste-image-to-upload**, `@mentions`, `#ref` autolinks, **threaded replies** (one level deep).
- Server-Sent Events for live updates on the active screen.

**Quick capture & command palette**
- `⌘K` palette: search projects / components / tasks / tickets / users / settings; run a curated set of actions.
- `c` quick capture modal anywhere → inbox; triage later into project + (task or ticket).

**My Focus / Today**
- Personal home: assigned & due today/overdue, recent mentions, watched items, last 20 activity entries across my projects.

**GitHub (read-only MVP)**
- Link a repo to a project or component (PAT-based for MVP; GitHub App later).
- Polled commit fetch (default 5 min) → `GithubCommit` cache → appear in activity stream as `github_commit` entries with `[owner/repo@sha]` and click-through.

**Admin & ops**
- `/healthz` + `/v1/auth/config` (exist).
- `/admin/users` forms (create / activate / deactivate / set superuser / reset password for local users).
- **Audit log** for admin actions and login events.
- **Declarative PostgreSQL DDL/DML**: repo **`sql/`** (`schema_changes.sql`, `schema_indexes.sql`, `schema_backfill.sql`, `schema_inserts.sql`) applied on API startup (**no Alembic** — see `.cursorrules`).

**UX baseline**
- Dark + light themes, system default; per-user override.
- Mobile-tolerant (responsive read views; capture works on phone).
- Accessibility: keyboard navigation through all primary surfaces, semantic landmarks, focus rings.

### 5.2 Explicitly **not** MVP (parking lot)

- Time tracking / timesheets.
- Gantt / dependency timelines.
- Email-to-ticket ingestion (SMTP/IMAP).
- Slack / Teams notifications.
- GitHub webhooks + PR review surfacing (polling first; webhooks in Phase 3).
- File storage on S3/MinIO (filesystem volume for MVP, **interface designed for S3** behind a single `AttachmentStorage` port).
- Public / customer-facing portal.
- Reporting dashboards & CSV export.
- Custom workflows per project (statuses are fixed enums in MVP).
- Full-text search via Postgres FTS or external index (basic `ILIKE` + trigram in MVP is enough; FTS in Phase 4).

---

## 6. API surface (proposed)

All under `/v1`. Bearer token = local JWT *or* dashboard OAuth JWT (the "unified Bearer" item from `HANDOFF.md` lands here). All write endpoints require an authenticated user; project-scoped endpoints check `ProjectMember.role`.

```
GET    /v1/auth/config                       (exists)
POST   /v1/auth/local/login                  (exists)
GET    /v1/auth/me                           (exists)
POST   /v1/auth/logout                       (exists/expand)

GET    /v1/admin/users                       (exists)
POST   /v1/admin/users
PATCH  /v1/admin/users/{id}
POST   /v1/admin/users/{id}/reset-password
GET    /v1/admin/audit                       (new)

GET    /v1/projects                          ?status=active&q=…
POST   /v1/projects
GET    /v1/projects/{id}
PATCH  /v1/projects/{id}
POST   /v1/projects/{id}/archive

GET    /v1/projects/{id}/members
POST   /v1/projects/{id}/members             { user_id, role }
PATCH  /v1/projects/{id}/members/{user_id}
DELETE /v1/projects/{id}/members/{user_id}

GET    /v1/projects/{id}/components
POST   /v1/projects/{id}/components
PATCH  /v1/components/{id}
DELETE /v1/components/{id}

GET    /v1/projects/{id}/tasks               ?status=&assignee=&component=&due_before=&q=
POST   /v1/projects/{id}/tasks
GET    /v1/tasks/{id}
PATCH  /v1/tasks/{id}
POST   /v1/tasks/{id}/transition             { to: "in_progress" }
DELETE /v1/tasks/{id}

GET    /v1/projects/{id}/tickets             ?status=&priority=&age_gt=
POST   /v1/projects/{id}/tickets
GET    /v1/tickets/{id}
PATCH  /v1/tickets/{id}
POST   /v1/tickets/{id}/transition

GET    /v1/{subject_type}/{id}/activity      ?cursor=
POST   /v1/{subject_type}/{id}/activity      { body_md, parent_activity_id?, is_internal? }
PATCH  /v1/activity/{id}
DELETE /v1/activity/{id}
GET    /v1/activity/stream                   (SSE; filter by ?project_id=)

POST   /v1/attachments                       (multipart; returns storage_key + meta)
GET    /v1/attachments/{id}                  (streamed)

GET    /v1/me/focus                          (today + mentions + watched)
POST   /v1/me/watch                          { subject_type, subject_id }
DELETE /v1/me/watch                          { subject_type, subject_id }

GET    /v1/inbox                             (quick-capture entries to triage)
POST   /v1/inbox                             { body_md, image? }
POST   /v1/inbox/{id}/triage                 { into: "task"|"ticket", project_id, … }
DELETE /v1/inbox/{id}

GET    /v1/projects/{id}/github
POST   /v1/projects/{id}/github              { owner, repo, token_secret_ref }
DELETE /v1/projects/{id}/github/{link_id}
POST   /v1/github/links/{link_id}/sync       (manual kick)

GET    /v1/search?q=…&types=project,task,ticket
```

OpenAPI is auto-generated by FastAPI; the existing `/docs` route is the contract.

---

## 7. Web surface (Next.js App Router)

```
src/app/
  (marketing)/                      ← optional public landing for standalone deploys
  login/                            (exists)
  sign-in/route.ts                  (exists)
  oauth/complete/route.ts           (exists)

  (app)/                            ← authenticated shell with sidebar + ⌘K
    layout.tsx
    today/                          ← /today : My Focus
    inbox/                          ← Quick Capture inbox + triage
    projects/
      page.tsx                      ← list with health badges
      [projectId]/
        layout.tsx                  ← project tabs
        page.tsx                    ← overview (health, recent activity, members, GitHub)
        components/
          [componentId]/page.tsx
        tasks/
          page.tsx                  ← board (default) + table toggle
          [taskId]/page.tsx
        tickets/
          page.tsx                  ← queue
          [ticketId]/page.tsx
        activity/page.tsx           ← full project stream
        github/page.tsx             ← linked repos + commit log
        settings/page.tsx           ← members, components, GitHub link, danger zone

    admin/
      users/page.tsx                (exists; extend with forms)
      audit/page.tsx
      settings/page.tsx             ← auth flags (read-only), version, healthz
```

Shared:

- `src/components/cmdk/` — `⌘K` palette (using a lightweight headless library like `cmdk`).
- `src/components/editor/` — markdown editor with `/`-commands, paste-image upload, `@`/`#` autocomplete.
- `src/components/activity/` — entry, thread, attachment renderer.
- `src/components/kanban/` — DnD board (HTML5 dnd or `@dnd-kit`).
- `src/lib/sse.ts` — typed SSE client.

---

## 8. Architecture & cross-cutting concerns

### 8.1 Auth (unifying)

- Keep `AUTH_LOCAL_ENABLED` / `AUTH_OAUTH_ENABLED` flags.
- Promote `HANDOFF.md` priority #1 to **MVP**: API accepts **either** local HS256 JWT *or* dashboard RS256 JWT (via JWKS). One dependency `get_current_user()` picks the validator by `token_typ` / `iss`. Map dashboard users to local `users` rows on first login (`auth_source='oauth'`, `email` is the key).
- RBAC starts simple:
  - `is_superuser` → admin endpoints.
  - `ProjectMember.role` → project-scoped read/write.
  - `viewer` is read-only; `owner` can delete the project.

### 8.2 Data

- PostgreSQL 16 (Compose service `postgresql`, exists).
- **SQLAlchemy 2 async** + **hand-maintained `sql/schema_*.sql`** (applied on startup; not Alembic).
- Soft delete only where it earns its keep (`Task`, `Ticket`, `Project` archive; activity is append-only and immutable except edit-window).

### 8.3 Real-time

- **SSE** endpoint per project + global "my feed". Cheap, proxy-friendly, no extra infra. Client falls back to polling if EventSource is unavailable.
- A tiny in-process pub/sub on the API (asyncio), with a future migration path to Redis/Postgres `LISTEN/NOTIFY` if we scale beyond one API replica.

### 8.4 Storage

- `AttachmentStorage` Protocol with **LocalDir** implementation (Docker volume `attachments_data` mounted at `/data/attachments`) for MVP.
- Same interface admits an **S3/MinIO** backend later — no API contract change.
- 25 MB per file MVP cap; mime allow-list (images + common docs).

### 8.5 GitHub

- Per-project encrypted PAT (`token_secret_ref` resolves to env or a secrets file; never in DB plaintext). GitHub App is the upgrade path.
- Background poller (Phase 3) runs every 5 min: fetch last 100 commits per linked repo, upsert to `GithubCommit`, emit `Activity{kind=github_commit}`.
- Webhooks deferred until polling proves the UX; webhook handler will reuse the same upsert path.

### 8.6 Search

- Phase 1: `ILIKE` on title + body, `pg_trgm` index for fuzzy.
- Phase 4: Postgres full-text (`tsvector` columns + GIN), filterable by project/type.

### 8.7 Observability

- Structured logs (JSON to stdout) with request id middleware.
- `/healthz` (exists), add `/readyz` that pings the DB.
- Web: simple `/api/internal/health` for uptime probes.

### 8.8 Security

- `JWT_SECRET` rotation runbook; refresh cookies marked `HttpOnly; SameSite=Lax; Secure` in production.
- CSRF: same-site cookies + SameSite=Lax + explicit `Origin` check on mutating routes.
- Rate-limit login (per IP + per email) and attachment upload.
- Pin file uploads to mime allow-list; scan magic bytes; serve via API (not via web) so we can authorize per request.
- Strict CSP on the web app (Next.js headers); no third-party scripts in MVP.
- All admin destructive actions write `AuditLog`.

### 8.9 Docker (already canonical)

- `docker compose --profile dev up --build` is the only supported dev runner.
- Add an `attachments` named volume.
- CI: a single `make check` (or equivalent compose run) that runs `web` lint + build and `api` lint + pytest in containers — no host Node/Python.

---

## 9. UX & visual design

- **Layout:** persistent left sidebar (Today / Inbox / Projects list / Admin if superuser) + top bar with breadcrumb, search, `⌘K` hint, avatar menu.
- **Density:** comfortable by default, "compact" toggle that ICs will turn on day one.
- **Color:** neutral grays + one accent. Status colors only on small chips, never on full rows.
- **Typography:** system stack; `JetBrains Mono` (or any monospace) for refs `PRJ-123` and code.
- **Empty states:** every list has a curated empty state with the next obvious action (`Create your first project`, `Capture a thought`, …).
- **Latency feel:** optimistic updates on status transitions and kanban moves; server confirms within 1 RTT.

---

## 10. Phased delivery (concrete)

Each phase ends in a demo-able state. Times are working estimates; sequence is the contract.

| Phase | Theme | Deliverables (definition of done) |
|-------|-------|-----------------------------------|
| **0 — Foundations (mostly done)** | Boilerplate stands up. | `docker compose --profile dev up --build` works end-to-end; local + OAuth login verified; `/admin/users` read-only table; `JWT_SECRET` configurable; this plan committed. |
| **1 — Domain core** | Projects, components, tasks. | Keep **`sql/`** in sync with models; `User.display_name`+`avatar_url`; CRUD APIs for projects/components/tasks with RBAC; web Projects list, Project overview, Components, Tasks **Kanban + Table**; refs `PRJ-N`; unified Bearer dependency on API. |
| **2 — Activity & tickets** | The PM hub feels alive. | Activity model + SSE; markdown editor with `/`-commands, `@`/`#`, paste-image upload; Tickets CRUD + queue; threaded replies; per-user **My Focus** (`/today`); Quick-Capture inbox + triage; Watchers. |
| **3 — GitHub & polish** | Context lands next to work. | `GithubLink` + PAT storage; commit poller; commit lane in project & component; `⌘K` palette with actions; saved views & filters; light/dark themes finalized; mobile capture verified. |
| **4 — Hardening & admin** | Production-ready. | Admin forms on `/admin/users` (create/edit/reset/deactivate); `AuditLog` UI; Postgres FTS; backup runbook; CSP/headers; load-test script; deployment manifests (compose prod + sketch K8s manifests per org standard). |

**MVP launch gate** = Phase 3 complete + all Phase 1/2 acceptance criteria green. Phase 4 can ship incrementally after.

---

## 11. Acceptance criteria (MVP)

A user with a fresh local install or an integrated SSO sign-in can:

1. **Sign in** via SSO or local form (per `AUTH_*` flags).
2. **Create a project** with a `key`, add 2 members with roles, create 2 components.
3. **Create tasks** including a sub-task, drag one across the Kanban, and see the activity entry.
4. **Open a ticket**, post an internal note + an external note with a pasted screenshot, transition to `resolved`.
5. **Quick-capture** a thought from anywhere with `c`, triage it into a task on the right project.
6. **`⌘K`** and jump to that task by typing its ref or words from its title.
7. See **`/today`** populated with their assigned/overdue/watched items.
8. Link a **GitHub** repo (PAT) and within 5 minutes see the latest commit appear in the project activity.
9. As a superuser, **create, deactivate and reset** a local user from `/admin/users`.
10. Reload — everything persists via **`sql/`** upgrades + idempotent **`schema_*.sql`** applied at startup (no ORM **`create_all`**, **no Alembic**).

---

## 12. Risks & mitigations

| Risk | Likelihood | Mitigation |
|------|------------|-----------|
| Auth divergence between local and dashboard JWTs | Medium | Implement unified Bearer dependency in Phase 1; integration tests for both paths. |
| Attachment growth blows up the volume | Medium | Per-file cap, soft per-project quota counter, retention policy hook ready before launch; abstract storage so S3 is a swap. |
| GitHub polling rate limits | Low | Per-link 5 min cadence, conditional requests (`If-None-Match`), exponential backoff; degrade gracefully if limited. |
| Activity stream becomes noisy | Medium | Per-subject filters; per-user mute on subjects; only mentions and assignments enter "My Focus". |
| Scope creep into time-tracking / Gantt | High | Parking-lot list in §5.2 is explicit; defer ruthlessly. |
| SSE behind a corporate proxy | Low | Polling fallback already designed in the client. |

---

## 13. Success metrics (MVP launch + 30 days)

- **Time to create a project + first task** (new user, instrumented) — **< 90 s** median.
- **Quick-capture usage** — ≥ 30 % of weekly active users use `c` at least once a week.
- **`/today` adoption** — ≥ 60 % of weekly active users land there in their first session of the day.
- **Stale-ticket detection** — 0 tickets > 14 days without movement go unflagged in the queue view.
- **API p95 latency** for list endpoints — **< 250 ms** on dev hardware, **< 150 ms** on prod-class.
- **OAuth + local login** both pass an automated smoke test in CI every commit.

---

## 14. Open questions (decide before/early in Phase 1)

1. **Project visibility** — Is "private to members" the only mode for MVP, or do we want a "visible to all org users (read-only)" tier? *(Suggested: members-only for MVP, visibility tier in Phase 4.)*
2. **Ticket policy** — Are external requesters ever directly authoring tickets in MVP, or only staff on behalf of customers? *(Suggested: staff-only in MVP; portal in a later phase.)*
3. **Email** — Any outbound notifications in MVP (e.g. mention email), or strictly in-app? *(Suggested: in-app only; add SMTP in Phase 4.)*
4. **RBAC granularity** — Are 4 roles per project enough, or do we need component-level roles in MVP? *(Suggested: project-level roles only.)*
5. **Attachment retention** — Any compliance window we need to plan for now (e.g. 90 / 365 days)?

---

## 15. References inside this repo

- Stable tech context: `.ai/context/CONTEXT.md`
- Session handoff: `.ai/context/HANDOFF.md`
- Product brief (authoritative direction): `.ai/plans/proposal/preliminary.md`
- Phased delivery (rough): `.ai/plans/estimate/plan.md`
- IdP repo: `/mnt/data/Projects/EPIC/tools-dashboard`
- Reference OAuth client: `/mnt/work/Projects/tools-rizervox`

---

*This document is internal planning for `tools-project`. Update as scope changes; keep `preliminary.md` as the short product brief and this file as the buildable plan.*

---

## 16. Repository alignment (implementation notes)

These notes exist so **UI and schema do not silently drift** from §4–§5 while the stack is still mid-delivery.

| Plan (§4.1) | Current repo | Notes |
|-------------|--------------|--------|
| `Task.body_md` / `Ticket.body_md` | `tasks.description`, `tickets.description` (`TEXT`) | Same role: long-form issue / work description. Rename to `body_md` only when the markdown editor pipeline is wired; until then treat `description` as markdown-capable plain text. |
| `Activity.body_md` | `activities.body` (`TEXT`) | Same role: comments, threaded replies, future paste-image. |
| `Activity.is_internal` | *not in DB yet* | MVP acceptance (§11.4) expects internal vs external notes; add a boolean column + API when the ticket detail thread is hardened. |
| `Attachment` | `attachments` table + `POST /v1/projects/{id}/tickets/{ticket_id}/attachments` + `GET /v1/attachments/{id}`; `ATTACHMENTS_DIR` (Compose volume `tpr_attachments` → `/data/attachments`) | Ticket-scoped image uploads (PNG/JPEG/GIF/WebP, 25 MB); linked to activity via `meta_json.attachment_ids`. Task uploads and S3-backed `AttachmentStorage` port still TBD. |
| Ticket vs Task | Two tables + shared `Activity` with `subject_type` `task` \| `ticket` | Correct split per plan: different status enums and SLA-style fields on **Ticket** only; engineering workflow stays on **Task**. |

**Ticket queue (API):** list ordering targets support triage: non-terminal tickets first, then **oldest `created_at` first**, then priority (see `api/app/routers/tickets.py`).

**Web:** `/projects/[id]/tickets` is the **queue**; `/projects/[id]/tickets/[ticketId]` is the **case** view (description + discussion via Activity). That mirrors §7 (`tickets/page.tsx` queue + `[ticketId]/page.tsx` detail).
