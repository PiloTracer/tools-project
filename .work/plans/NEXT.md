# Next batch — tools-project (prioritized work)

**Purpose:** Backlog derived from **`.work/plans/legacy-plans/proposal/20260515-full-project.md`** (phases §10–§11) and repo reality.  
**North star:** Phase **1** (domain core) → **2** (activity & tickets depth) → **3** (GitHub & polish) — see **§ Batch I — GitHub integration** below for the **active** specification.  
**Run dev stack:** `.cursorrules` / `docker compose --profile dev up --build` or `./bin/start.sh`.

**Schema:** declarative **`sql/`** only — no Alembic. On API startup: `schema_changes.sql` → `schema_indexes.sql` → bootstrap → `schema_backfill.sql` → `schema_inserts.sql`.

**Latest (repo):** **2026-06-18** — Repo restructured: `.work/` now holds project-specific content (CONTEXT, HANDOFF, NEXT, legacy plans); `.ai/` holds Agent OS framework (skills, standards, templates); `.cursorrules` updated to generic template. **Product scope unchanged:** Phases **1–2** (**Batch G**, **Batch H**, carryovers **P2–P5**) **complete** on `main`. **Batch I (GitHub) — partial:** API + sync done; web tab + activity feed + ref attach still open (see **§ I12**). **Batch J (CRM / clients-participants) — starting:** SPEC Approved, ADR-0001 Decided, schema + model slice is next (see **§ Batch J**). **Still deferred:** attachment **retention purge** cron; optional Inbox **`c`** shortcut.

### Status at a glance (visual)

```text
Phase 1 (G)     ████████████████████  5/5   Done
Carryovers P    ████████████████████  3/3   Done (P2, P4, P5)
Phase 2 (H)     ████████████████████  5/5   Done (H1–H5)
Phase 3 (I)     ██████░░░░░░░░░░░░░░  ~30% API slice (DB + sync + REST); web + activity TBD
────────────────────────────────────────────────
Matrix (G+H+P)  ████████████████████  14/14 Done

Open: Batch I web + github_commit activity + github_ref · retention cron · optional Inbox "c"
Active: Batch J — CRM (M1: schema + prospects) — next task: M1-T1 (prospects DDL + model)
```

---

## Implementation status — Phases 1–2 (verified 2026-05-16)

| ID | Scope | Status | Evidence / notes |
|----|-------|--------|------------------|
| **G1** | Kanban + drag-drop | **Done** | `web/src/components/KanbanBoard.tsx` (HTML5 DnD); `TasksView` in `TasksClient.tsx`; transition via `/api/tasks/[id]/transition`. |
| **G2** | Task detail route | **Done** | `web/src/app/projects/[id]/tasks/[taskId]/page.tsx`. |
| **G3** | Human refs in UX | **Done** | Task refs on **`/today`**; **`CmdkPalette`** search by title/ref; tasks table already had Ref column. |
| **G4** | ⌘K command palette | **Done** | `web/src/components/CmdkPalette.tsx` + `AppShell.tsx`. |
| **G5** | Project list health | **Done** | `GET /v1/projects` adds `ProjectHealth`; `web/src/app/projects/page.tsx` pills. |
| **P2** | Threaded replies (1 level) | **Done** | Ticket **`TicketDiscussion`**: Reply + thread; **project** **`ActivityClient`**: Reply + thread + `MarkdownEditor`; API rejects nested **`parent_activity_id`**. |
| **P4** | Task attachment parity | **Done** | `POST .../tasks/{id}/attachments`; activity validation for `subject_type=task`. |
| **P5** | Non-image uploads + caps | **Done** | **`file_sniff`** (pdf, txt); per-file **25 MiB** limit (**`413`**); **per-project file count** cap (**`429`**, `Settings.attachment_max_per_project`, **`ATTACHMENT_MAX_PER_PROJECT`**); **per-project byte total** quota when set above zero (**`429`**, `Settings.attachment_max_bytes_per_project`, **`ATTACHMENT_MAX_BYTES_PER_PROJECT`**); **retention hook** (`retention_cutoff()` + **`ATTACHMENT_RETENTION_DAYS`** — purge job deferred). |
| **H1** | Inbox + triage | **Done** | **`/v1/inbox`**, triage → task or ticket; web **`/inbox`** + BFF. |
| **H2** | Watchers + Today | **Done** | Watch API; **`/v1/me/today`** `watched_tickets`; Today UI. |
| **H3** | Richer SSE payload | **Done** | Stream JSON + **`ActivityStreamHint`** shows `kind`. |
| **H4** | Markdown-ish editor | **Done** | **`MarkdownEditor`** on **project** composer + threaded replies and **ticket** discussion with **`mentionSuggestions`** and **`refSuggestions`** (BFF + API). |
| **H5** | Activity on task mutations | **Done** | `api/app/services/activity_writer.py`; **`tasks`** router calls **`write_activity`** on create, assignee change, status patch, transition. |

**Earlier (2026-05-15, unchanged):** **P1** `activities.is_internal` end-to-end + ticket UI; **P3** ticket queue stale-age badges + legend.

### Open / follow-up (non–Batch I)

| # | Item |
|---|---|
| **P5** | Wire **retention** purge cron job (hook `retention_cutoff()` exists); admin surfacing for caps (optional). |
| **H1** | Optional global **`c`** quick-capture shortcut. |
| **J0** | **Batch J — CRM clients-participants:** schema + models; prospects CRUD + pipeline transitions; clients, contacts, project linking; client access/permission resolution; `/client/login` + limited project view. |

**Batch I (GitHub) — shipped vs next:** see **§ I10** (sub-track status) and **§ I12** (how to add repo + PAT **today** without a web form). **`20260515-full-project.md`** Phase **3** / §11 item **8** remain **open** until the **GitHub** web tab and **`github_commit`** activity feed land.

---

## Batch G — Phase 1 (reference)

Original acceptance: Kanban, task detail URL, ⌘K, health on projects list — **met** (see matrix).

---

## Batch H — Phase 2 (reference)

Inbox, watches, richer SSE, task activity, markdown editor — **met** (see matrix).

---

## Batch I — GitHub integration (Phase 3) — **specification**

This section **extends** **`20260515-full-project.md`** §4.1 / §5.1 / §6 / §8.5 with product choices that stay **easy to integrate** and **loosely coupled** to multiple UI surfaces (project overview, activity feed, task detail, ticket thread, Today, ⌘K, future watcher digests, etc.).

### I0 — Alignment with the existing plan (unchanged intent)

- **Read-only MVP first:** link repos → poll GitHub → cache commits → surface in **Activity** as `kind = github_commit` (already allowed in `api/app/schemas.py` activity kinds).
- **Auth for GitHub API:** **PAT** per link for MVP; **GitHub App** as the documented upgrade path (same tables; different credential column / flow).
- **No plaintext tokens in DB:** store **`token_cipher`** (Fernet-at-rest; key from **`GITHUB_TOKEN_ENCRYPTION_KEY`** or derived from **`JWT_SECRET`** — see **`.env.example`**); never return or log token values. Aligns with plan’s “no plaintext PAT in DB”; GitHub App remains the upgrade path.
- **Polling before webhooks:** default **interval** (e.g. **5 minutes**, configurable); **conditional requests** / **ETag** where possible; **backoff** on `403`/`429`.
- **Webhooks later:** reuse the same **upsert commit** pipeline the poller uses.

### I1 — Ease of integration (design principles)

1. **Single write pipeline** — All GitHub API results normalize into **`github_commits`** (cache). Optional derived **`activities`** rows for stream visibility; **do not** teach the UI to scrape GitHub directly.
2. **Stable read DTO** — Expose a small **`CommitSummary`** (and optional **`CommitDetail`**) JSON shape from **`GET /v1/.../commits`** so **any** widget (cards, tables, pickers, markdown previews) consumes one contract.
3. **Reference, don’t fork** — “Attach commit to task / comment / ticket” stores a **pointer** (`github_commit_id` or `{ owner, repo, sha }` + resolved `link_id`) in **`activities.meta_json`** and/or a dedicated **`commit_subject_refs`** table (see **I7**). Never duplicate the full message body in five places; join to cache.
4. **Project-scoped RBAC** — All link and commit routes go through existing **`require_project_access`** / mutation rules (maintainers configure links; viewers read commits).

### I2 — Linking model: multiple repositories per project (and optional component)

| Concept | Rule |
|--------|------|
| **Anchor unit** | **Primary:** `project_id` (required). **Optional:** `component_id` for finer grouping (matches plan’s `GithubLink` with nullable `component_id`). |
| **Cardinality** | **Many links per project** — each row is one GitHub repo connection. |
| **User input** | Accept **`https://github.com/owner/repo`** (or `owner/repo`); **normalize** to `owner`, `repo`. Validate with a lightweight **HEAD** or **repo metadata** call on save. |
| **Credential** | **PAT** at link create; stored as **`token_cipher`** (Fernet). Upgrade path: external secret ref / GitHub App (plan). |

**Implemented DDL (see `sql/schema_changes.sql`):** `github_links` — `id`, `project_id`, `component_id` NULL, **`owner`**, **`repo`**, **`token_cipher`** (encrypted PAT), **`poll_interval_seconds`**, `last_synced_at`, `last_seen_sha`, `created_by`, timestamps. **`github_commits`** — `github_link_id`, **`sha`**, **`message`**, author fields, **`committed_at`**, **`html_url` NOT NULL**, optional `raw_json`.

### I3 — Sync behavior: on start + periodic

| Trigger | Behavior |
|---------|----------|
| **API lifespan** | If **`github_sync_enabled`**, starts **`github_poll_loop`** (**`app/github_background.py`**): waits **`github_poll_initial_delay_seconds`**, then syncs **each link** in its own DB transaction on every **`github_poll_interval_seconds`** interval. |
| **Per-link interval** | Column **`github_links.poll_interval_seconds`** is stored for future per-link scheduling; **current** loop uses the **global** env interval only. |
| **Manual** | **`POST /v1/projects/{project_id}/github/links/{link_id}/sync`** (maintainer/owner). |

**Ingestion:** GitHub **`/repos/{owner}/{repo}/commits`** (or compare API if you branch-scope later). Upsert into **`github_commits`**; for **each new** row optionally insert **`activities`** (`kind=github_commit`, `subject_type=project`, `subject_id=project_id`, `actor_user_id=NULL` system, `meta_json` holds `{ link_id, sha, html_url, message_head }`).

### I4 — Commit cache: full history + “what to show in lists”

**Table sketch:** `github_commits` — `id`, `github_link_id`, `sha` (40 hex), `short_sha` generated or computed, `author_name`, `author_email` NULL, `message` TEXT, `committed_at`, `html_url`, `parents_json` optional, `raw_json` optional (debug / forward-compat), unique `(github_link_id, sha)`.

**List / enumerate contract (UX + API):** every row returned to the client **must** allow the user to identify:

| Field | Requirement |
|-------|----------------|
| **Which project** | Implicit from route (`project_id`) **or** explicit `project_id` + `project_key` / name in DTO when listing cross-project (e.g. admin or future global search). |
| **Which repo** | `owner`, `repo` (from link join). |
| **Commit identity** | **Full `sha`** in API payloads; UI may show **7-char** abbreviation **only alongside** access to full SHA (tooltip, copy button, or expand row). |
| **Commit message** | Return **full `message`** from cache for detail views. For **dense lists**, provide **`message_preview`** — **at least 120 characters** (meets “≥ 100 chars” ask with margin); suffix with ellipsis when truncated. **Recommendation:** 120 list / full in drawer. |
| **Verify on GitHub** | Persist GitHub’s **`html_url`** for every commit (see plan **`GithubCommit.html_url`** and “**click → diff link on GitHub**”). **Every** list row, activity card, and `github_ref` chip **must** expose it (e.g. “Open commit” / link on SHA). Developers verify **diff and files on GitHub** in the browser — **no embedded code or diff preview** in-app for MVP unless you explicitly expand scope later. |

**Pagination:** cursor-based (`sha` + `committed_at`) for “full history” browsing on **`/projects/{id}/github`** and API.

### I4.1 — Action checklist: `html_url` required + verification UX

Execute these when implementing Batch I (check off in PRs). **Goal:** any widget can render **“Open on GitHub”** with **no extra DB/API round-trip** beyond the payload it already holds.

| # | Layer | Exact action |
|---|--------|--------------|
| 1 | **`sql/schema_changes.sql`** | Add column **`html_url` TEXT NOT NULL** on **`github_commits`**. If you must allow legacy rows during rollout, use `NOT NULL` only after backfill; **never** ship new ingests without a URL. |
| 2 | **Ingest / upsert** | When mapping GitHub API commit → row, set **`html_url`** from the payload’s **`html_url`** field. **If absent** (rare), **derive** `https://github.com/{owner}/{repo}/commit/{sha}` and store that — still satisfies NOT NULL and deep-link contract. |
| 3 | **`api/app/schemas.py` (or equivalent)** | Define **`CommitSummary`** (and **`CommitDetail`** if split) with **`html_url: AnyHttpUrl | str`** **required** (no optional). Same for any **`GithubCommitOut`** used by routers. |
| 4 | **List/detail routes** | **`GET .../github/commits`** and **`GET .../github/commits/{sha}`** always **serialize `html_url`** from the row; do not omit for size — previews are already truncated separately via **`message_preview`**. |
| 5 | **`activities.meta_json` (system `github_commit`)** | On insert, always include **`html_url`** alongside `sha`, `owner`, `repo`, `link_id`, `commit_id` (see **§ I5**). |
| 6 | **`github_ref` validation (writes)** | On POST/PATCH of activities/tasks/tickets that include **`github_ref`**: require **`html_url`** **or** accept omit only if server **re-resolves** `commit_id` and **injects** `html_url` before save (prefer **require** on client for fewer round-trips). |
| 7 | **`body_md` for `github_commit` rows** | Use Markdown link target = stored **`html_url`** for the short SHA anchor (see **§ I5**). |
| 8 | **Web — GitHub table** | **SHA** cell: `<a href={html_url} target="_blank" rel="noopener noreferrer">` (abbrev label + `title` with full SHA). Add **external-link icon** consistent with design system. |
| 9 | **Web — message preview** | Make preview **also** clickable to **`html_url`** **or** add adjacent **“Open on GitHub”** control; **same** `html_url` for both (primary verification path). |
| 10 | **Web — activity card `kind=github_commit`** | Read **`meta_json.html_url`**; render **SHA + “Open on GitHub”** without fetching commit again. |
| 11 | **Web — commit chips / picker output** | When inserting a chip or markdown snippet, include **`html_url`** in the stored structure so rendered chips link out. |
| 12 | **Tests** | API contract tests: list + detail responses **assert** `html_url` matches expected `https://github.com/.../commit/...` pattern. Web smoke (optional): link `href` present in DOM fixture. |
| 13 | **Docs / OpenAPI** | Mark **`html_url`** **required** in OpenAPI schema + one example row in `/docs`. |

**Optional later (do not block MVP):** add **`parents_json`** (or first parent SHA) on **`github_commits`** and a small helper **`compare_url(parent, sha)`** → `https://github.com/{owner}/{repo}/compare/{parent}...{sha}`; **PR link** via separate integration. **Still** link-out only unless you explicitly choose embedded previews.

---

### I5 — Activity stream integration (`github_commit`)

- **Automatic stream entries** for newly discovered commits (system actor).
- **`body_md`:** short human line, e.g. ``[`abc123f`](url) **owner/repo** first line of message…`` — keeps Today / rollup readable.
- **`meta_json`:** machine-friendly `{ "link_id", "commit_id", "sha", "owner", "repo", "html_url", "message_preview" }` for widgets and SSE clients (already have `kind` in SSE hints).

### I6 — Attaching a commit to tasks, comments, and other feedback

**Goal:** user can **cite** any cached commit on a **task**, **activity comment** / **reply**, **ticket** note, or future types — without hard-wiring GitHub into every composer.

**Recommended approach (loose coupling):**

1. **`CommitReference` in `meta_json`** (MVP, fast): convention `github_ref: { "commit_id": "<uuid>", "sha": "<40>", "owner", "repo", "html_url" }` (include **`html_url`** so chips stay deep-linkable even if join is skipped). Validated on POST/PATCH: commit must belong to same `project_id` as the subject.
2. **Optional normalized table** `commit_subject_refs` (scalable): `id`, `github_commit_id`, `subject_type` (`task` / `ticket` / `activity` / …), `subject_id`, `created_by`, `created_at` — powers “all tasks referencing this commit”, watcher notifications, and deduplication. **Architecture should allow adding this table without breaking I6.1.**

**UI:** picker modal or ⌘K entry “Insert commit…” → searches **`GET /v1/projects/{id}/github/commits?q=`** → inserts markdown snippet or structured chip stored as above.

**Not required in first slice:** inline diff or **source code preview** inside tools-project; PR objects; status checks. **Verification** = **open `html_url` on GitHub** (commit page / compare as GitHub provides).

### I7 — Loose integration layer (for watchers, collaborators, developers)

| Layer | Responsibility |
|-------|----------------|
| **`GitHubSyncPort` (protocol)** | `fetch_commits_since(link, cursor) -> list[NormalizedCommit]` — swappable test fake / live httpx client. |
| **`CommitRepository` (DB)** | Upsert commits; list by project / link; resolve `sha` → row. |
| **`ActivityWriter` extension** | `write_github_commit_activity(...)` beside existing `write_activity`. |
| **`CommitSummary` DTO** | Shared JSON schema documented in OpenAPI; **must** include **`html_url`** (and `sha`, `owner`, `repo`, `message_preview`, timestamps). Imported by web types codegen or hand mirror. |

**Widgets** (non-exhaustive) should depend **only** on **`CommitSummary`** + **`github_ref` meta** — not on Octokit-specific shapes:

- Project **GitHub** tab — full history table.
- **Activity** card renderer for `kind=github_commit`.
- **Task detail** sidebar — “Linked commits”.
- **TicketDiscussion** — commit chips in thread.
- **Today** — optional “recent commits in watched projects” (later).

### I8 — API surface (extends plan §6)

Keep the plan’s routes; extend for **many links** and **history**:

```
GET    /v1/projects/{project_id}/github/links
POST   /v1/projects/{project_id}/github/links     { github_repo_url?, owner?, repo?, github_token, component_id?, poll_interval_seconds? }
DELETE /v1/projects/{project_id}/github/links/{link_id}
POST   /v1/projects/{project_id}/github/links/{link_id}/sync

GET    /v1/projects/{project_id}/github/commits   ?link_id=&limit=
```

**Not implemented yet:** `PATCH …/links/{link_id}`; `GET …/github/commits/{sha}` detail; cursor/`q` filters (extend as needed).

### I9 — Web surface (extends plan §7) — **not implemented yet**

- **`/projects/[id]/github`** — linked repos + **paginated** commit table (columns: time, repo, SHA copy, **120+ char preview**, author).
- **Settings sub-section** — add / remove repo links (owner/repo URL + token), test connection, poll interval override per link (advanced).
- **Reuse** `Activity` feed component for auto `github_commit` rows; **separate** rich history table for “full log” browsing.

### I10 — Phased delivery (Batch I sub-tracks)

| Sub | Scope | Status |
|-----|-------|--------|
| **I10a** | `sql/` + models **`github_links`**, **`github_commits`** | **Done** — indexes + **`html_url` NOT NULL**; **§ I4.1** row **1**. |
| **I10b** | Link CRUD API + encrypted token | **Done** — `POST/GET/DELETE …/github/links` (no **`PATCH`** link yet). |
| **I10c** | Poller + upsert | **Partial** — **httpx** sync + **lifespan** background loop + manual **`POST …/sync`**; **no** `activities` rows with `kind=github_commit` yet (**§ I4.1** rows **5–7** deferred). |
| **I10d** | `GET …/github/commits` + GitHub page UI | **Partial** — **API + `CommitSummary`** (`html_url` required) **done**; **Next.js** **`/projects/[id]/github`** + table UI **not started** (**§ I4.1** rows **8–11** web). |
| **I10e** | **`github_ref`** validation + picker | **Not started**. |
| **I10f** | (Optional) `commit_subject_refs` + watcher hooks | **Not started**. |
| **I10g** | Plan §3 polish carryovers | **Not started** (can parallelize after **I10d** web). |

### I11 — Acceptance (Batch I) vs **`20260515-full-project.md`** §11

| # | Plan / NEXT criterion | Status |
|---|------------------------|--------|
| 1 | Maintainer links **≥2** repos; **no token** in API responses or logs | **API ready** — use **`POST …/github/links`**; tokens **encrypted at rest**; verify with **`GET …/links`** (no secret fields). **Web form** not built. |
| 2 | Commits visible in **activity** + **GitHub** tab within a poll cycle | **Partial** — commits in **`github_commits`** + **`GET …/github/commits`**; **no** `github_commit` **activities** yet; **no** **`/projects/[id]/github`** page yet. |
| 3 | List rows: project, repo, SHA, **≥120** char preview, **`html_url`** | **`CommitSummary`** on **`GET …/github/commits`** satisfies this; **no** web table yet. |
| 4 | Attach commit to **task** / **comment** | **Not started** (**I10e**). |
| 5 | New widgets consume **`CommitSummary`** only | **Yes** for API contract; web widgets pending. |

### I12 — Configure GitHub repo + PAT **today** (API / OpenAPI — no web UI yet)

There is **no** Next.js screen for URL/token yet (plan **`/projects/[id]/github`** + settings — **I10d** web). Until that ships, use **`http://localhost:8300/docs`** (tag **`github`**) or any HTTP client with a normal **Bearer JWT** (same auth as the rest of the API). **Role:** project **owner** or **maintainer** only.

**Create link + initial sync** (body uses **`GithubLinkCreate`** — either **`github_repo_url`** *or* **`owner` + `repo`**, plus **`github_token`**):

```http
POST /v1/projects/{project_id}/github/links
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "github_repo_url": "https://github.com/octocat/Hello-World",
  "github_token": "<github_pat_fine_grained_or_classic>"
}
```

Then:

```http
GET /v1/projects/{project_id}/github/commits
Authorization: Bearer <access_token>
```

**Manual re-sync:** `POST /v1/projects/{project_id}/github/links/{link_id}/sync`. **Background poll:** controlled by **`GITHUB_SYNC_ENABLED`**, **`GITHUB_POLL_INTERVAL_SECONDS`**, **`GITHUB_POLL_INITIAL_DELAY_SECONDS`**, **`GITHUB_COMMITS_PER_SYNC`** (see **`.env.example`**).

---

## Batch J — clients-participants (CRM)

**Source:** `.work/features/clients-participants/20260618-SPEC.md` (Approved) + ADR-0001.  
**Goal:** Add client companies, contacts, sales pipeline, and limited client project access.

### J0 — Decisions / prerequisites (done)

- ADR-0001 decided: separate `client_contacts` with optional `user_id`; `project_clients` join table; dedicated `project_client_access`; separate `prospects` table; individual user accounts; `/client/login`; `is_internal` visibility boundary.
- Unknowns registry updated; architecture foundation doc aligned.

### J1 — Schema + models (first slice)

Add idempotent DDL in `sql/schema_changes.sql` and SQLAlchemy models:

1. `prospects`
2. `clients` (with `slug` generation from company name)
3. `client_contacts` (includes `role` for `contact` / `contact_admin`)
4. `project_clients`
5. `project_client_access`
6. Optional V1: `client_referrals`, `client_onboarding_items`

Run `apply-ddl` twice to verify idempotency.

### J2 — Prospects API + UI

- `api/app/routers/prospects.py`: list, create, get, update, delete, `PATCH /stage` with transition validation.
- `web/src/app/prospects/`: list page, detail page with tabs (overview, activity, referrals), stage transition widget.

### J3 — Clients + contacts API + UI

- `api/app/routers/clients.py`: client CRUD + contacts sub-routes.
- `web/src/app/clients/`: list, detail (contacts, projects, onboarding tabs).
- Auto-create `clients` record when prospect reaches `won`.

### J4 — Project-client linking

- `api/app/routers/project_clients.py`: link/unlink clients to projects; include client summary on project GET.
- Web: client badge on project list/header; client section in project settings.

### J5 — Client access + permission resolution

- `api/app/routers/project_client_access.py`: grant/revoke/update client contact access.
- Modify `api/app/deps.py` to check `project_client_access` alongside `project_members`.
- Enforce `is_internal = false` visibility for client participants.

### J6 — Client portal

- `web/src/app/client/login/`: separate login page.
- Limited client dashboard + project view: only assigned tasks/tickets, public activity, no settings/GitHub/internal activity.

### J7 — Pipeline flags + optional polish

- `api/app/services/pipeline_flags.py`: surface follow-up / check-in / breakup / review-for-lost flags.
- Optional V1: referrals UI, onboarding checklist UI.

### J8 — Acceptance

- [ ] Client CRUD + contacts end-to-end.
- [ ] Prospect stage transitions validated.
- [ ] Project linked to client; internal team sees client summary.
- [ ] Client participant login sees only allowed projects and public activity.
- [ ] Client participant cannot view internal activity, project settings, members, or GitHub.

---

## Batch A — Schema discipline (maintain continually)

| # | Item | Why | Hints |
|---|------|-----|-------|
| A1 | **`sql/schema_changes.sql`** ↔ **`api/app/models`** | Primary DDL | `IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`. |
| A2 | **`sql/schema_indexes.sql`** | Indexes / constraints | Idempotent. |
| A3 | **`sql/schema_backfill.sql`** | Row fixes for existing DBs | Idempotent only. |
| A4 | **`sql/schema_inserts.sql`** | Seeds after bootstrap | `ON CONFLICT`; avoid random UUIDs for fixtures unless static. |

**Current tables (non-exhaustive):** `users`, `projects`, `project_members`, `components`, `tasks`, `activities`, `mentions`, `tickets`, **`attachments`**, **`project_counters`**, **`inbox_items`**, **`watchers`**, **`github_links`**, **`github_commits`**.  
**Still planned (optional):** **`commit_subject_refs`** for normalized cross-links + **`github_commit`** activity rows (API sync today only writes **`github_commits`** + link metadata).

---

## Completed batches (reference — do not reopen unless regressing)

| Batch | Scope | Status |
|-------|--------|--------|
| **B** | Project members, RBAC, PATCH project, web members/settings | **Done** |
| **C** | Components API + UI | **Done** |
| **D** | Tasks: API transitions, filters, **table** UI, **`ref`** via counters | **Done** (Kanban = **G1**) |
| **E** | Admin user forms, auth docs | **Done** |
| **F** | Activities, mentions, tickets queue API, **`/today`** | **Done** + **ticket case**, **attachments**, queue ordering |
| **G** | Phase 1 parity: Kanban, task detail, ⌘K, project health | **Done** (see matrix) |
| **H** | Inbox, watches, SSE payload, task activity, markdown editor | **Done** (see matrix) |
| **I** | GitHub & polish | **In progress** — see **§ Batch I** |

---

## Quick verification commands (Docker)

```bash
docker compose --profile dev up --build
docker compose --profile dev run --rm api python -m app.cli_schema apply-ddl   # DDL → bootstrap → backfill/inserts
curl -s "http://localhost:8300/docs"   # GitHub routes under tag `github`
docker compose --profile dev run --rm --no-deps web sh -lc "npm ci --no-audit --no-fund && npm run check && npm run build"
```

---

*Update this file when a batch completes; keep **HANDOFF** snapshot in sync. Batch I detail lives in **§ Batch I** above. Paths moved: old `.ai/context/*` → `.work/context/`, `.ai/plans/*` → `.work/plans/legacy-plans/`, `.ai/context/NEXT.md` → `.work/plans/NEXT.md`.*
