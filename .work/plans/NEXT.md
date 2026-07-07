# Next batch — tools-project (prioritized work)

**Purpose:** Backlog derived from **`.work/plans/legacy-plans/proposal/20260515-full-project.md`** (phases §10–§11) and repo reality.  
**North star:** Phase **1** (domain core) → **2** (activity & tickets depth) → **3** (GitHub & polish) — see **§ Batch I — GitHub integration** below for the **active** specification.  
**Run dev stack:** `.cursorrules` / `docker compose --profile dev up --build` or `./bin/start.sh`.

**Schema:** declarative **`sql/`** only — no Alembic. On API startup: `schema_changes.sql` → `schema_indexes.sql` → bootstrap → `schema_backfill.sql` → `schema_inserts.sql`.

****Latest (repo):** **2026-07-01** — Agent Query API shipped: personal API keys (user_api_keys), 5 aggregation endpoints (/v1/agent/), MCP server (5 tools), web UI (/settings/api-keys), documentation + tutorial. All gates green.

### Status at a glance (visual)

```text
Phase 1 (G)     ████████████████████  5/5   Done
Carryovers P    ████████████████████  3/3   Done (P2, P4, P5)
Phase 2 (H)     ████████████████████  5/5   Done (H1–H5)
Phase 3 (I)     ████████████████████  6/6   Done (I10a–I10g)
────────────────────────────────────────────────
Matrix (G+H+P)  ████████████████████  14/14 Done
Improvements    ████████████████████  8/8   Done (2026-06-29 sess 1)
Improvements    ████████████████████  5/5   Done (2026-06-29 sess 2)
Documentation   ████████████████████  12/12 Done (2026-06-29 sess 3)
Batch K         ████████████████████  3/3   Done (opp-to-project automation)
Batch L         ████████████████████  3/3   Done (client health dashboard)
Security fixes  ████████████████████  8/8   Done (config, auth, endpoint hardening)
Pen test rem.   ████████████████████  9/9   Done (all findings addressed)

Open: none — all follow-ups resolved
Active: none — all session follow-ups done

### Recommended next
1. Add automated tests for the ecosystem hub modifications (Mod 1–4).
2. Run full task gate (ruff, pyright, tests, scope/blast-radius) and close the iteration.
3. Build satellite apps (CompanyBrain, OpsBoard, SignFlow, LedgerLite) that consume the ecosystem APIs.
4. **Multi-tenancy:** SPEC reviewed and gaps closed. Next: mark SPEC Approved, then `@code-implementation plan` to break into milestones.

### Intake queue
- 2026-07-06 · local · "assess making this app multi-tenant" → SPEC created at `.work/features/multi-tenancy/20260706-SPEC.md` (Draft)

## Current iteration (2026-07-06)

**Goal:** Land ecosystem hub modifications 1–4 with passing task gate.

| # | Task | Status | Notes |
|---|------|--------|-------|
| T1 | Implement outbound event dispatcher (Mod 1) | **Done** | `api/app/services/webhook_dispatcher.py`, `api/app/routers/admin_webhooks.py`, `api/app/models/webhook_subscription.py` |
| T2 | Implement platform whoami (Mod 2) | **Done** | `api/app/routers/platform.py` |
| T3 | Implement cross-app references (Mod 3) | **Done** | `api/app/routers/external_refs.py` |
| T4 | Implement RFP award webhook (Mod 4) | **Done** | `api/app/routers/integrations.py` |
| T5 | Fix lint/type failures across codebase | **Done** | ruff + pyright clean |
| T6 | Fix GitHub token encryption error in dev stack | **Done** | `.env.dev` key + compose env passthrough + invalid dev link removed |
| T7 | Update iteration scope in NEXT.md | **Done** | this section |
| T8 | Add pytest + tests for new routers/services | **Done** | 25 tests in `api/tests/` covering Mod 1–4 + utilities |

## Done this iteration

- All Mod 1–4 code implemented and registered in `app/main.py`.
- `ruff check .` passes.
- `pyright .` passes (0 errors, 0 warnings).
- Dev stack starts cleanly; API / web health endpoints respond.
- GitHub poll no longer crashes on missing/invalid encryption key.

## New features (2026-07-06)

### Ecosystem hub modifications (Mod 1–4)

| ID | Scope | Status | Evidence |
|----|-------|--------|----------|
| Mod 1 | Outbound event dispatcher — HMAC-signed webhooks + admin subscriptions | **Done** | `api/app/services/webhook_dispatcher.py`, `api/app/routers/admin_webhooks.py`, `api/app/models/webhook_subscription.py` |
| Mod 2 | Platform whoami — shared identity for satellite apps | **Done** | `api/app/routers/platform.py` — `GET /v1/platform/whoami` |
| Mod 3 | Cross-app references — generic `external_refs` over `commit_subject_refs` | **Done** | `api/app/routers/external_refs.py` |
| Mod 4 | RFP award webhook — accept `tools-rfp` award, promote to client/project | **Done** | `api/app/routers/integrations.py` — `POST /v1/integrations/rfp/award` |

## New features (2026-07-01)

### M — Agent Query API

| ID | Scope | Status | Evidence |
|----|-------|--------|----------|
| M1 | `/v1/agent/` aggregation endpoints (projects, context, tasks, tickets, search) | **Done** | `api/app/routers/agent_query.py` — 5 endpoints, Pydantic response models, single-query N+1 optimization |
| M2 | Personal API keys (`POST /v1/me/keys`, `GET /v1/me/keys`, `DELETE /v1/me/keys/{id}`) | **Done** | `api/app/routers/me_api_keys.py` — SHA-256 hashed, `tools_project_` prefix, one-time plaintext display |
| M3 | `user_api_keys` table + model | **Done** | `sql/schema_changes.sql`, `api/app/models/user_api_key.py` — UUID PK, key_hash, key_prefix, last_used_at |
| M4 | `require_agent_or_user` X-Api-Key auth | **Done** | `api/app/deps.py` — resolves: agent_api_key → user_api_keys (SHA-256) → Bearer JWT |
| M5 | MCP server (5 tools) | **Done** | `.opencode/mcp/project-mcp/mcp_server.py` — JSON-RPC 2.0, reads `~/.tools-project-key` or env |
| M6 | Web UI: `/settings/api-keys` | **Done** | `web/src/app/settings/api-keys/` — table, create dialog with one-time secret display, revoke confirmation |
| M7 | Documentation + tutorial | **Done** | `.work/docs/agent-query-api.md` (reference), `.work/docs/tutorials/LLM-2-API_SETUP.md` (step-by-step) |
| M8 | Feature SPEC | **Done** | `.work/features/agent-query-api/20260701-SPEC.md` |

## New features (2026-06-29)

### K — Opportunity-to-Project Automation
| ID | Scope | Status | Evidence |
|----|-------|--------|----------|
| K1 | Auto-scaffold project + tasks on prospect promotion | **Done** | `api/app/services/pipeline_service.py` — 7 onboarding tasks, client link, access grants, activity entry |
| K2 | Return project info in promotion response (API) | **Done** | `ProspectStageChangeResponse.promoted_project`, `ProspectPromoteResponse` |
| K3 | Frontend: "View project" link in success dialog | **Done** | Detail page + list page both show project link alongside client link |

### L — Client Health Dashboard
| ID | Scope | Status | Evidence |
|----|-------|--------|----------|
| L1 | `GET /v1/clients/health` endpoint with scoring | **Done** | `api/app/routers/client_health.py` — task completion, ticket burden, activity recency weighted score |
| L2 | Health dashboard UI on `/clients` | **Done** | Toggle "Health"/"List" view, stat cards, color-coded health cards with scores |
| L3 | Feature SPECs reviewed and Approved | **Done** | `.work/features/opp-to-project-auto/` + `client-health-dashboard/` |

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

**Not implemented yet:** `PATCH …/links/{link_id}`; `GET …/github/commits/{sha}` detail; cursor pagination (extend as needed). The `q` search param on `GET …/github/commits` **is** implemented.

### I9 — Web surface (extends plan §7) — **Done**

- **`/projects/[id]/github`** — linked repos + **paginated** commit table (columns: time, repo, SHA copy, **120+ char preview**, author).
- **Settings sub-section** — add / remove repo links (owner/repo URL + token), test connection, poll interval override per link (advanced).
- **Reuse** `Activity` feed component for auto `github_commit` rows; **separate** rich history table for “full log” browsing.

**Shipped (per I10d / HANDOFF):** `/projects/[id]/github` page + commit table, `/projects/[id]/settings` add/remove repos + PAT form, `github_commit` activity cards in `ActivityClient`.
**Still pending:** cursor pagination on the commit table (see § I8), “test connection” control, per-link `poll_interval_seconds` override in the settings form.

### I10 — Phased delivery (Batch I sub-tracks)

| Sub | Scope | Status |
|-----|-------|--------|
| **I10a** | `sql/` + models **`github_links`**, **`github_commits`** | **Done** — indexes + **`html_url` NOT NULL**; **§ I4.1** row **1**. |
| **I10b** | Link CRUD API + encrypted token | **Done** — `POST/GET/DELETE …/github/links` (no **`PATCH`** link yet). |
| **I10c** | Poller + upsert + `github_commit` activity rows | **Done** — **httpx** sync + **lifespan** background loop + manual **`POST …/sync`**; `activities` rows with `kind=github_commit` written only for **new** commits. |
| **I10d** | `GET …/github/commits` + GitHub page UI | **Done** — **API + `CommitSummary`** (`html_url` required) **done**; **Next.js** **`/projects/[id]/github`** + table UI **done**; `github_commit` activity cards render with rich SHA/repo/preview. |
| **I10e** | **`github_ref`** validation + picker | **Done** — backend validation in `activities.py`; `CommitPicker` component with search; integrated into activity composer + reply forms. |
| **I10f** | (Optional) `commit_subject_refs` + watcher hooks | **Done** — table + model + router + auto-create on activity `github_ref`. |
| **I10g** | Plan §3 polish carryovers | **Done** — optional Inbox **`c`** shortcut still deferred. |

### I11 — Acceptance (Batch I) vs **`20260515-full-project.md`** §11

| # | Plan / NEXT criterion | Status |
|--:|------------------------|--------|
| 1 | Maintainer links **≥2** repos; **no token** in API responses or logs | **Done** — **`/projects/[id]/settings`** web form; tokens **encrypted at rest**; **`GET …/links`** omits secret fields. |
| 2 | Commits visible in **activity** + **GitHub** tab within a poll cycle | **Done** — **`/projects/[id]/github`** page; `github_commit` activities in feed with rich card rendering. |
| 3 | List rows: project, repo, SHA, **≥120** char preview, **`html_url`** | **Done** — web table on GitHub tab; `CommitSummary` enforces `html_url`. |
| 4 | Attach commit to **task** / **comment** | **Done** — **`github_ref`** validation in `activities.py`; **`CommitPicker`** component with search. |
| 5 | New widgets consume **`CommitSummary`** only | **Yes** — API contract and web widgets. |

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

- `api/app/routers/prospects.py`: list, create, get, update, delete, `PATCH /stage` with transition validation. **Done.**
- `web/src/app/prospects/`: list page, detail page with tabs (overview, activity, referrals), stage transition widget. **Screen SPEC created (Draft)** — `.work.ui/screens/prospects-list/20260618-SCREEN-SPEC.md`. Build pending UI design foundation.

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
| **I** | GitHub & polish | **Done** — see **§ Batch I** |

---

## Quick verification commands (Docker)

```bash
docker compose --profile dev up --build
docker compose --profile dev run --rm api python -m app.cli_schema apply-ddl   # DDL → bootstrap → backfill/inserts
curl -s "http://localhost:8300/docs"   # GitHub routes under tag `github`
docker compose --profile dev run --rm --no-deps web sh -lc "npm ci --no-audit --no-fund && npm run check && npm run build"
```

---

## Current iteration — M7: Outbound event dispatcher

**Milestone ref:** M7 · Feature SPEC: `.work/features/outbound-event-dispatcher/20260706-SPEC.md`
**Status:** complete
**Started:** 2026-07-06

### Tasks
| ID | Description | Files | Status | Notes |
|----|-------------|-------|--------|-------|
| M7-T1 | webhook_subscriptions table + model | `sql/schema_changes.sql`, `api/app/models/webhook_subscription.py` | done | DDL + SQLAlchemy model |
| M7-T2 | webhook_dispatcher service | `api/app/services/webhook_dispatcher.py` | done | dispatch_event with retry + HMAC signing |
| M7-T3 | admin CRUD router | `api/app/routers/admin_webhooks.py` | done | POST/GET/DELETE with superuser guard |
| M7-T4 | Wire into event-producing routes | `prospects.py`, `clients.py`, `tasks.py`, `tickets.py` | done | prospect.stage_changed/won, client.created, task.done, ticket.created/closed |
| M7-T5 | Register router + gate | `api/app/main.py` | done | compileall pass, 38 routes |

### Done this iteration
| Task | Completed | Notes |
|------|-----------|-------|
| M7-T1 | 2026-07-06 | webhook_subscriptions DDL + model |
| M7-T2 | 2026-07-06 | webhook_dispatcher with retry |
| M7-T3 | 2026-07-06 | admin webhook CRUD router |
| M7-T4 | 2026-07-06 | Wiring in 4 routers |
| M7-T5 | 2026-07-06 | Gate: compileall pass, 38 routes |

---

## Current iteration — M8: Cross-app external refs

**Milestone ref:** M8 · Feature SPEC: `.work/features/cross-app-refs/20260706-SPEC.md`
**Status:** complete
**Started:** 2026-07-06

### Tasks
| ID | Description | Files | Status | Notes |
|----|-------------|-------|--------|-------|
| M8-T1 | Schema: add source_app, external_url, label to commit_subject_refs | `sql/schema_changes.sql`, `sql/schema_indexes.sql` | done | ALTER TABLE + index |
| M8-T2 | Extend CommitSubjectRef model | `api/app/models/commit_subject_ref.py` | done | New columns |
| M8-T3 | External refs CRUD router | `api/app/routers/external_refs.py` | done | POST/GET/DELETE per project |
| M8-T4 | Register router + gate | `api/app/main.py` | done | compileall pass, 38 routes |

### Done this iteration
| Task | Completed | Notes |
|------|-----------|-------|
| M8-T1 | 2026-07-06 | Schema migration + index |
| M8-T2 | 2026-07-06 | CommitSubjectRef extension |
| M8-T3 | 2026-07-06 | external_refs router |
| M8-T4 | 2026-07-06 | Gate: compileall pass, 38 routes |

---

## Current iteration — M6: Platform whoami endpoint

**Milestone ref:** M6 · Feature SPEC: `.work/features/platform-whoami/20260706-SPEC.md`
**Status:** complete
**Started:** 2026-07-06
**HANDOFF waiver:** This feature is outside the original M1-M4 plan. Approved SPEC exists; implementing as an additive extension.

### In scope
- Schemas: `WhoamiUser`, `WhoamiCompany`, `WhoamiResponse`
- Router `GET /v1/platform/whoami` reusing `require_agent_or_user` auth
- Lookup `client_contacts` by `user_id`, join `clients` for name
- Register router in `main.py`

### Out of scope (explicit)
- Full OAuth2 Authorization Server
- User registration or signup
- Rate limiting specific to this endpoint

### Tasks
| ID | Description | Files | Status | Notes |
|----|-------------|-------|--------|-------|
| M6-T1 | Add whoami schemas | `api/app/schemas.py` | done 2026-07-06 | `WhoamiUser`, `WhoamiCompany`, `WhoamiResponse` |
| M6-T2 | Create platform router | `api/app/routers/platform.py` | done 2026-07-06 | `GET /v1/platform/whoami` |
| M6-T3 | Register router in main.py | `api/app/main.py` | done 2026-07-06 | Import + `include_router` |
| M6-T4 | Task gate — compile, verify | — | done 2026-07-06 | `compileall` pass, app loads 36 routes |

### Acceptance criteria
- [ ] `GET /v1/platform/whoami` returns user + companies with valid auth
- [ ] Unauthenticated returns 401
- [ ] Compileall pass

### Validation steps
- [ ] `docker compose --profile dev run --rm --no-deps api python -m compileall -q app`

### Owner blockers
- none

### Concept / NFR registry (this iteration)
| Concept id | Applies | Status | Evidence / trigger |
|------------|---------|--------|-------------------|
| MOD-01 | no | n/a | Single bounded context (API) |
| MOD-02 | no | n/a | No AI-assisted PR |
| MOD-03 | no | n/a | No cost-sensitive decisions |
| MOD-04 | no | n/a | No distributed-system concerns |
| MOD-05 | no | n/a | No compliance surface |
| MOD-06 | yes | done 2026-07-06 | 0 boundaries, no new deps, read-only query — merge_ok |
| MOD-07 | no | n/a | No ops-load impact |

### Cross-LLM verification
- Triggered: no

### Done this iteration
| Task | Completed | Notes |
|------|-----------|-------|
| M6-T1 | 2026-07-06 | WhoamiUser, WhoamiCompany, WhoamiResponse schemas |
| M6-T2 | 2026-07-06 | platform router: GET /v1/platform/whoami |
| M6-T3 | 2026-07-06 | Router registered in main.py |
| M6-T4 | 2026-07-06 | Gate: compileall pass, app imports (36 routes) |

---

## Current iteration — M5: RFP award webhook receiver

**Milestone ref:** M5 · Feature SPEC: `.work/features/rfp-award-webhook/20260706-SPEC.md`
**Status:** complete
**Started:** 2026-07-06
**HANDOFF waiver:** This feature is outside the original M1-M4 plan. Approved SPEC exists; implementing as an additive extension.

### In scope
- `rfp_webhook_secret` config setting in `Settings`
- In-memory idempotency store with 24h TTL
- HMAC-SHA256 signature verification dependency
- Schemas: `RfpAwardPayload`, `RfpAwardResponse`
- New router `POST /v1/integrations/rfp/award` — accepts webhook, resolves/creates prospect, transitions to won, runs promotion pipeline
- Register router in `main.py`

### Out of scope (explicit)
- `integration_secrets` DB table (single env var for V1)
- DB-backed idempotency (in-memory for MVP)
- Outbound webhook dispatcher (Modification 1 — separate feature)
- Cross-app reference table (Modification 3 — separate feature)
- Web UI for webhook configuration
- Tests (unit/integration — added as follow-up after manual verification)

### Tasks
| ID | Description | Files | Status | Notes |
|----|-------------|-------|--------|-------|
| M5-T1 | Add `rfp_webhook_secret` to config + in-memory idempotency store | `api/app/config.py` | done 2026-07-06 | Single env var; dict-based idempotency with expiry |
| M5-T2 | Add schemas for RFP award payload and response | `api/app/schemas.py` | done 2026-07-06 | `RfpAwardPayload`, `RfpAwardResponse` |
| M5-T3 | Create HMAC signature verification dependency | `api/app/deps.py` | done 2026-07-06 | `verify_webhook_signature` |
| M5-T4 | Create `integrations` router with `POST /v1/integrations/rfp/award` | `api/app/routers/integrations.py` | done 2026-07-06 | Resolve/create prospect, call `pipeline_service`, return client+project |
| M5-T5 | Register router in `main.py` | `api/app/main.py` | done 2026-07-06 | Import + `include_router` |
| M5-T6 | Task gate — compile, verify | — | done 2026-07-06 | `compileall` pass, app loads 35 routes |

### Acceptance criteria
- [ ] `POST /v1/integrations/rfp/award` with valid HMAC signature returns 201 with client + project
- [ ] Invalid signature returns 401
- [ ] Missing required fields returns 422
- [ ] Idempotency key prevents duplicate processing
- [ ] Same email reuses existing prospect/contact
- [ ] Compileall pass

### Validation steps
- [ ] `docker compose --profile dev run --rm --no-deps api python -m compileall -q app`

### Owner blockers
- none

### Concept / NFR registry (this iteration)
| Concept id | Applies | Status | Evidence / trigger |
|------------|---------|--------|-------------------|
| MOD-01 | no | n/a | Single bounded context (API) — no cross-boundary coupling |
| MOD-02 | no | n/a | No AI-assisted PR |
| MOD-03 | no | n/a | No cost-sensitive decisions — tiny endpoint |
| MOD-04 | no | n/a | No distributed-system concerns |
| MOD-05 | no | n/a | No compliance surface |
| MOD-06 | yes | done 2026-07-06 | Agent-assisted code — run. Output: 0 boundaries, no new cross-boundary deps, test isolation missing. Recommendation: merge_with_conditions — add tests before production traffic |
| MOD-07 | no | n/a | No ops-load impact |

### Cross-LLM verification
- Triggered: no

### Done this iteration
| Task | Completed | Notes |
|------|-----------|-------|
| M5-T1 | 2026-07-06 | rfp_webhook_secret config + in-memory idempotency store |
| M5-T2 | 2026-07-06 | RfpAwardPayload + RfpAwardResponse schemas |
| M5-T3 | 2026-07-06 | verify_webhook_signature HMAC dependency |
| M5-T4 | 2026-07-06 | integrations router: POST /v1/integrations/rfp/award |
| M5-T5 | 2026-07-06 | Router registered in main.py |
| M5-T6 | 2026-07-06 | Gate: compileall pass, app imports (35 routes) |

---

*Update this file when a batch completes; keep **HANDOFF** snapshot in sync. Batch I detail lives in **§ Batch I** above. Paths moved: old `.ai/context/*` → `.work/context/`, `.ai/plans/*` → `.work/plans/legacy-plans/`, `.ai/context/NEXT.md` → `.work/plans/NEXT.md`.*
