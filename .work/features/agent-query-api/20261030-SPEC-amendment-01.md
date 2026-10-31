# Agent Ticket Context & Attachments — Feature SPEC amendment 01

**Status:** Approved
**Approved:** 2026-10-30 (owner `@feature-spec approve`; verified and corrected the same day — see §16)
**Owner:** Engineering
**ADRs referenced:** [0002-backend-stack.md](../../decisions/0002-backend-stack.md) (no Alembic, idempotent startup DDL), [0004-hosting-deployment.md](../../decisions/0004-hosting-deployment.md) (Compose services, local attachment store, 25 MiB cap)
**Related plans:** Batch I (GitHub commits → `linked_commits`), Batch J (CRM → client participants)
**Amends:** [`20260701-SPEC.md`](20260701-SPEC.md) (agent-query-api, Approved — not edited)
**Verification report:** [`20261030-amendment-01-verification.md`](20261030-amendment-01-verification.md)
**Date:** 2026-10-30
**Slug:** agent-query-api
**Trigger:** Pizote tickets PZT-T-1 … PZT-T-4 (§1.2)

---

## 1. Purpose

Agents connected through the Agent Query API can read a ticket's **title and description**
but cannot read the **evidence** recorded with it: attached screenshots, the comment thread,
attachment metadata, or lifecycle data. The description's image markdown
(`![…](/api/attachments/<uuid>)`) points at the **web-app** proxy, which requires a browser
session — an API key gets `401`, so the agent sees a broken reference and cannot view the image.

This amendment closes that gap: one ticket-detail read, one activity read, one binary read,
a capability handshake, plus the MCP tools that expose them. It keeps the surface **read-only**
and reuses the existing attachment, activity and tenancy models — no new tables, no new storage.

### 1.1 Why now

A report that is only text can be read; a report that is mostly a screenshot cannot. PZT-T-2
("documentos fallidos") names a cartel but the failing state is in the screenshot; PZT-T-3
("botón para explorar cartel") is a visual affordance that only exists in the screenshot.
The agent's only alternatives today are to ask the operator to re-paste the images or to
guess — neither is acceptable for a platform whose purpose is to carry project evidence.

### 1.2 Evidence (live, 2026-10-30, remote `0.1.3` — verified)

Probes used a personal key from `~/.tools-project-key`; full command log in the verification
report §2. `X-Api-Key` unless stated.

| Need | Call | Result |
|------|------|--------|
| project + tickets + descriptions | `GET /v1/agent/projects/{pzt}/context` | **200** — 4 tickets, 3 image refs |
| context summary counts | same payload | **0 / 0 / 0** while `/v1/agent/projects` reports **1 / 4 / 3** |
| screenshot bytes (API) | `GET /v1/attachments/54830228-…` | **401** — JWT-only route |
| screenshot (link inside the description) | `GET /api/attachments/54830228-…` | **401** — web session cookie required |
| ticket detail | `GET /v1/agent/tickets/{uuid}` or `…/PZT-T-1` | **404** — route absent |
| comments / activity | `/v1/projects/{id}/activities` → **401**; no `/v1/agent` route | absent |
| reporter / requester / queue / resolution timestamps | agent payload | absent |
| attached filename / mime / size | agent payload | absent |
| ticket web URL with an API key | `GET /projects/{id}/tickets/{id}` | **307 → /login** |
| MCP tools for the above | `tools/list` | absent (5 tools today) |
| MCP against the hosted API | canonical copy, default urllib UA | **403 Cloudflare Error 1010**; with `User-Agent` → **200** |

Deployed OpenAPI (`0.1.3`) lists exactly five agent routes: `/projects`,
`/projects/{id}/context`, `/tasks`, `/tickets`, `/search`.

---

## 2. In scope / Out of scope

### In scope

- `GET /v1/agent/tickets/{ticket}` — full ticket detail (ticket, people, counts, attachments,
  first activity page, per-ticket commits, web URL).
- `GET /v1/agent/tickets/{ticket}/activities` — paginated, filterable activity feed.
- `GET /v1/agent/attachments/{attachment_id}` — binary download, agent-authenticated.
- `GET /v1/agent/capabilities` — version/capability handshake.
- `GET /v1/agent/client/mcp_server.py` — canonical MCP server file (subject to **D1**).
- MCP tools `get_ticket_detail`, `list_ticket_activities`, `get_attachment`, plus
  `SERVER_VERSION`, `--self-check`, `--version`, and the Cloudflare-safe `User-Agent`.
- Fix the context endpoint's zeroed summary counts; add truncation flags.
- `project_id` filter on `GET /v1/agent/tickets`.
- One additive index (`activities`).
- Docs (`.work/docs/**`), tests, and the copy/update path for the MCP server (this repo and the
  `project-query-setup` skill in the Agent OS repository).

### Out of scope

- Any write/comment/upload/transition through the agent API (stays read-only).
- Unauthenticated or public share links for attachments.
- Server-side OCR/vision, thumbnails, or image transformation.
- Changing storage (local disk under `ATTACHMENTS_DIR`) or the upload allowlist.
- Changing attachment retention (it is already `0` = never purge).
- Web UI changes (the existing `/api/attachments/<id>` proxy is untouched).
- Relaxing the agent-superuser gate (see Q1 — deliberately deferred).
- A schema migration framework; `sql/*.sql` remains the only schema path.

---

## 3. Domain language

| Term | Definition |
|------|------------|
| Agent principal | The user resolved from an `X-Api-Key` (personal key) or a Bearer JWT. |
| Ticket address | The ticket UUID **or** its `ref` (`PZT-T-1`), trimmed, case-insensitive. `tickets.ref` is globally unique. |
| Activity | A row in `activities`: `comment`, `note` (legacy alias of `comment`), `status_change`, `assignment`, `attachment`, `github_commit`, `mention`, `system`, `transition`. |
| Internal note | An activity with `is_internal = true`; staff-only. |
| Client participant | A caller whose `ProjectAccess.client_access is not None` (`is_client_participant`). |
| Subject visibility | The rule that limits a client participant to tickets/tasks assigned to their company (and to project-wide activity), used by the web app. |
| Attachment scope | Where a file hangs: `ticket` (`attachments.ticket_id`), `task` (`task_id`) or `activity` (`activity_id`). |
| Capability | A named feature advertised by `/v1/agent/capabilities` so clients can degrade gracefully. |
| Resolved description | `description` with every `/api/attachments/<uuid>` replaced by the absolute agent `download_url`. |

---

## 4. Behavioural spec

### R1 — Ticket addressing

`{ticket}` accepts the ticket UUID or its `ref` (trimmed, case-insensitive). Lookup order:
parse as UUID; otherwise lookup by `ref` (tenant-scoped). The ticket is resolved **first**, then
tenant, project access and subject visibility are enforced; **every** failure is `404` with
`{"detail": "ticket_not_found"}` so a foreign, unreadable or missing ticket is indistinguishable.

### R2 — Authentication and authorization

All new endpoints use `require_agent_or_user` (same as the existing `/v1/agent/*` routes):
personal `X-Api-Key` → its owner; shared `AGENT_API_KEY` → synthetic superuser only when
multi-tenancy is disabled; Bearer JWT → the user. After authentication:

1. **Agent gate.** `_require_agent_superuser` is **kept unchanged** in this amendment.
   Consequence: today every caller is a superuser (`403` for a non-superuser JWT), and
   `resolve_project_access` returns `owner` for a superuser regardless of membership. Q1 records
   the follow-up; **D3** keeps the gate for 1.1.0 and fixes the documentation instead.
2. **Project access.** `require_project_access(db, user, ticket.project_id)` → `404` on failure.
3. **Subject visibility (client participants).** The project check is **not** sufficient. When
   `is_client_participant(acc)`:
   - ticket detail requires `can_view_tickets(acc)` **and**
     `ticket.assignee_id ∈ client_company_user_ids(acc)`; otherwise `404`;
   - activities are filtered with `client_activity_condition(db, acc, project_id)` **and**
     `is_internal = false` — the same predicates as `GET /v1/projects/{id}/activities`;
   - attachment reads apply the same subject rule for ticket/task-scoped files (F3).
   These checks exist today only behind Q1's future relaxation; they are implemented **now** so
   the relaxation is a one-line change (I11).
4. **Internal notes.** Client participants never receive internal notes or their attachments,
   at both the metadata and the binary endpoint (defence in depth — do not rely on the list filter).

### R3 — `GET /v1/agent/tickets/{ticket}` — detail

Returns `{ "ok": true, "data": { "agent_api_version", "ticket": { … }, "project": { … } } }`
with this shape (all timestamps ISO-8601 UTC):

```json
{
  "ok": true,
  "data": {
    "agent_api_version": "1.1.0",
    "ticket": {
      "id": "8fb47f08-8daf-457f-b798-149e8e4eaf60",
      "ref": "PZT-T-1",
      "project_id": "19b24527-128d-4087-ac48-41979c619c11",
      "title": "Sin correos de reporte",
      "description": "…![Screenshot 2026-10-19 at 5.19.31 PM.png](/api/attachments/54830228-0c70-4c62-8149-bf967f47af86)",
      "description_resolved": "…![Screenshot 2026-10-19 at 5.19.31 PM.png](https://project.cloudsys.win/v1/agent/attachments/54830228-0c70-4c62-8149-bf967f47af86)",
      "status": "in_progress",
      "priority": "normal",
      "queue_slug": "default",
      "requester_email": null,
      "reporter": { "id": "…", "display_name": "…", "email": "…" },
      "assignee": { "id": "…", "display_name": "…", "email": "…" },
      "watchers": [ { "id": "…", "display_name": "…", "email": "…" } ],
      "created_at": "2026-10-19T23:17:02Z",
      "updated_at": "2026-10-30T21:52:10Z",
      "first_response_at": null,
      "resolved_at": null,
      "closed_at": null,
      "web_url": "https://project.cloudsys.win/projects/19b24527-…/tickets/8fb47f08-…",
      "counts": { "activities": 2, "attachments": 1, "linked_commits": 1 },
      "attachments_truncated": false,
      "attachments": [ /* R5 */ ],
      "activities": [ /* R6 item, newest first — omitted when include_activities=false */ ],
      "activities_page": { "total": 2, "has_more": false, "next_offset": null, "order": "desc" },
      "linked_commits": [
        { "sha": "9a31e21…", "short_sha": "9a31e21", "html_url": "https://github.com/…",
          "message_preview": "…", "author_name": "…", "committed_at": "…", "state": "resolved" }
      ]
    },
    "project": { "id": "…", "name": "Pizote", "slug": "pizote", "project_key": "PZT" }
  }
}
```

Rules:

- **Field names.** `description` is returned **verbatim** (the shipped column and the same name
  used by `/v1/agent/tickets` and the context endpoint — I8). `description_resolved` is additive.
  There is no `description_markdown` field (C5).
- **People.** `reporter`, `assignee`, watchers expose `email` **only for staff callers**
  (`acc.client_access is None`); client participants get `display_name` only. `requester_email`
  is `null` for client participants. `assignee` is `null` when unassigned.
- **Raw markdown.** `description` is never rewritten in place (round-trip safety for clients that
  post it back).
- **Inline activity page** is newest-first (`order = "desc"`), `activity_limit` 1…200 (default 50,
  clamped), and `next_offset` pages backwards through history. For chronological reading call
  R6 with `order=asc`. `include_activities` (default `true`) and `include_internal` (default
  `true` for staff, forced `false` for client participants) are knobs. With
  `include_activities=false`, both `activities` and `activities_page` are omitted.
- **Ordering.** Attachments: description-referenced first (order of appearance), then the rest by
  `created_at` ascending, capped at 200 (R16) — so description references are cut last.
  `counts.attachments` is the true, visibility-filtered total; `attachments_truncated = true` when
  the array was capped.
- **Counts.** `counts.activities` is the visibility-filtered total (client participants count
  only what they may read); `counts.linked_commits` counts resolved + pending rows.
- **Linked commits.** Rows from `commit_subject_refs` joined to `github_commits`; pending rows
  (`github_commit_id IS NULL`) are returned with `state: "pending"`, `html_url: null` and `sha`.
- **Web URL.** `web_url` = `PUBLIC_WEB_BASE_URL` + `/projects/{project_id}/tickets/{ticket_id}`
  when that setting is configured, else `null` — never a guessed origin (C4/D2).
- **Bounded work.** ≤ 8 queries with activities, ≤ 6 without (R16).

### R4 — Resolved description

`description_resolved` replaces every occurrence of `](/api/attachments/<uuid>)` — both image
`![alt](…)` and link `[name](…)` forms — with the absolute `download_url` of that attachment.

1. Only exact `/api/attachments/<uuid>` targets are replaced (no prefix/suffix match).
2. An attachment id that is unknown, not attached to this ticket, or not visible to the caller
   is **left as-is** (no 500, no information leak). It is also absent from `attachments[]`.
3. The response always includes `description` so a client can rebuild if needed.
4. There is no separate `description_attachments[]` list: every attachment referenced by the
   description also appears in `attachments[]` with `markdown_ref` set (R5).

### R5 — Attachment object (metadata)

```json
{
  "id": "54830228-0c70-4c62-8149-bf967f47af86",
  "filename": "Screenshot 2026-10-19 at 5.19.31 PM.png",
  "mime": "image/png",
  "size_bytes": 184320,
  "is_image": true,
  "scope": "ticket",
  "activity_id": null,
  "created_at": "2026-10-19T23:19:40Z",
  "created_by": { "id": "…", "display_name": "…" },
  "download_url": "https://project.cloudsys.win/v1/agent/attachments/54830228-0c70-4c62-8149-bf967f47af86",
  "markdown_ref": "/api/attachments/54830228-0c70-4c62-8149-bf967f47af86"
}
```

- `scope` is `"ticket"` when `ticket_id` is set, `"activity"` when `activity_id` is set,
  `"task"` when `task_id` is set.
- `is_image` is `true` for `image/png|jpeg|gif|webp` only.
- `markdown_ref` is `null` unless the description references the attachment.
- **Never** include `storage_key`, a disk path, or `project_id`-less data (I2).
- `download_url` is built from `PUBLIC_API_BASE_URL` when set, else from
  `X-Forwarded-Proto`/`Host` (falling back to `request.base_url`) — see C4. Configured base
  URLs are normalized (scheme + host, no trailing slash).

### R6 — `GET /v1/agent/tickets/{ticket}/activities`

Query: `limit` (1…200, default 50), `offset` (≥0, default 0), `order` (`asc|desc`, default
`desc`), `kind` (validated against `ACTIVITY_KINDS`, legacy `note` normalized to `comment`),
`include_internal` (default `true` for staff, forced `false` for client participants),
`visibility` (`internal|external`; omit or pass `all` for both — `all` is normalized to no filter,
while the web endpoint stays stricter and rejects it; `internal` is `403` for client participants).

```json
{
  "ok": true,
  "data": {
    "items": [
      {
        "id": "…",
        "kind": "comment",
        "actor": { "id": "…", "display_name": "…", "email": "…" },
        "body": "…",
        "is_internal": false,
        "parent_activity_id": null,
        "created_at": "2026-10-19T23:20:11Z",
        "attachments": [ /* R5 with scope="activity" */ ],
        "meta_json": null
      }
    ],
    "total": 3,
    "has_more": false,
    "next_offset": null,
    "order": "desc"
  }
}
```

- The filter/visibility builder is **shared** with `GET /v1/projects/{id}/activities`
  (`app/services/activity_query.py`), not copied (C3). Client participants additionally apply
  `client_activity_condition`.
- `meta_json` is passed through (status transitions carry from/to; `github_commit` carries the
  link). It is already stored, so this adds no new data.
- Attachments for the whole page are fetched in **one** query (R16).

### R7 — `GET /v1/agent/attachments/{attachment_id}` — binary

- **Auth:** R2. `require_project_access` on the attachment's project; subject visibility for
  client participants (ticket/task assignee rule); internal-note attachments are `404` for
  client participants (`_assert_attachment_visible`). **Every** failure is `404`
  `{"detail": "attachment_not_found"}`.
- **Response:** the stored bytes, streamed (`FileResponse`), never base64 inside JSON.
- **Headers:**
  - `Content-Type`: the stored `mime`, **re-validated against `ALLOWED_MIMES`**; anything else
    → 404.
  - `Content-Length`: the on-disk size (`FileResponse`); a DB/disk mismatch is logged, not fatal.
  - `Content-Disposition`: `inline; filename="<sanitized>"; filename*=UTF-8''<percent-encoded>`;
    `?download=1` switches to `attachment`.
  - `Cache-Control: private, max-age=0, no-store`; `X-Content-Type-Options: nosniff`;
    `Content-Security-Policy: sandbox`; `Referrer-Policy: no-referrer`.
  - **No `ETag` in 1.1.0** (C6): a sha256 would buffer or re-read the file, contradicting R16,
    and `no-store` makes validators useless.
- Missing DB row, missing file on disk, or invalid `storage_key` → 404 (`path_for_key` already
  rejects traversal).
- Range requests are out of scope.

### R8 — `GET /v1/agent/capabilities`

```json
{ "ok": true, "data": {
  "agent_api_version": "1.1.0",
  "capabilities": ["ticket_detail", "ticket_activities", "attachments", "attachment_download",
                   "capabilities", "mcp_server_file"],
  "limits": { "activities_default": 50, "activities_max": 200,
              "activity_body_max_bytes": 32768, "description_max_bytes": 32000,
              "attachments_per_response": 200, "attachment_max_bytes": 26214400 },
  "recommended_mcp_server_version": "1.1.0",
  "mcp_server_download_url": "https://project.cloudsys.win/v1/agent/client/mcp_server.py"
} }
```

- Authenticated (R2). `mcp_server_download_url` is `null` when **D1** is declined;
  `mcp_server_file` is then absent from `capabilities`.
- `recommended_mcp_server_version` is the server's expectation of the client; the caller's own
  version is unknown to the server (C7).
- **Version policy:** additive fields/tools → minor (`1.1.x`); breaking changes → major. The MCP
  server compares `major.minor`: older API → hide newer tools; newer API → keep working.
  `agent_api_version` is the contract version; the product version (`0.1.x`) is unrelated.
- No `inline_image_max_bytes` here — that is a client-side cap (R9).

### R9 — MCP tools (`api/app/client/mcp_server.py`; copy at `.opencode/mcp/project-mcp/mcp_server.py`)

| Tool | Input | Returns |
|------|-------|---------|
| `get_ticket_detail` | `ticket` (uuid or ref), `include_activities` (bool, default true), `include_internal` (bool, default true), `activity_limit` (default 50) | one `text` block with the R3 JSON |
| `list_ticket_activities` | `ticket`, `limit`, `offset`, `order`, `kind`, `include_internal` | one `text` block with the R6 JSON |
| `get_attachment` | `attachment_id`, `save_dir` (optional) | `image` block (`{"type":"image","data":"<base64>","mimeType":"image/png"}`) when `is_image` and `size_bytes ≤ inline_image_max_bytes`; `text` block for `text/plain` ≤ `inline_text_max_bytes`; otherwise the file is written to disk and a `text` block returns `{path, filename, mime, size_bytes, sha256}`. A metadata `text` block always accompanies the content block. |

Rules:

- **HTTP client.** Every request sends `User-Agent: tools-project-mcp/<SERVER_VERSION>`
  (override `MCP_USER_AGENT`). This is mandatory: the hosted deployment is behind Cloudflare,
  which answers urllib's default UA with **403 Error 1010** (verified — C1).
- Image inline default cap **5 MiB** (`TOOLS_PROJECT_INLINE_IMAGE_MAX_BYTES`); text inline cap
  **1 MiB** (`TOOLS_PROJECT_INLINE_TEXT_MAX_BYTES`); above the cap the file is saved and the path
  returned — never truncate silently. Image blocks only for `image/*` mimes.
- `save_dir` defaults to `~/.cache/tools-project/attachments/` (mode `700`), falling back to
  `Path(tempfile.gettempdir())/"tools-project"/"attachments"`; filenames are `Path(name).name`,
  `..` stripped, collisions suffixed, and the resolved path must stay inside `save_dir`.
- Every tool returns `{"ok": false, "error": "…"}` as **text** on failure — the server never
  crashes the transport and never prints the key.
- `SERVER_VERSION = "1.1.0"` is the single source for `initialize.serverInfo.version` (C7);
  `--version` prints it; `--self-check` prints the effective base URL (+ where it came from), runs
  `/v1/agent/capabilities`, and prints the detected version + enabled tools.
- **Capability probe is lazy**, on the first tool call, 5 s timeout, cached. If the probe *fails*
  (API down), all tools stay visible and calls surface the error; if it *succeeds* with an older
  `agent_api_version`, the newer tools are hidden. `initialize` never blocks on the network.
- The five existing tools keep their names and payloads unchanged (I8).

### R10 — MCP server distribution

The MCP server is a **client artifact**; consuming repositories keep their own copy. Today the
canonical copy lives outside the API image and is broken for the hosted deployment (F1, F2).

Requirements (subject to **D1**):

1. **Canonical location:** `api/app/client/mcp_server.py` — standard-library only, importable
   (`main()` guarded), packaged by both Dockerfiles (`COPY app ./app`). No third copy.
2. **Served file:** `GET /v1/agent/client/mcp_server.py` returns that file with agent auth
   (R2), `Content-Type: text/x-python; charset=utf-8`,
   `Content-Disposition: attachment; filename="mcp_server.py"`, `X-MCP-Server-Version`.
   The served bytes are byte-identical to the packaged module (test #20).
3. **Repo copy:** `.opencode/mcp/project-mcp/mcp_server.py` is refreshed from the endpoint (or
   from the packaged file) by `bin/mcp-sync.sh sync`; `bin/mcp-sync.sh check` exits non-zero when
   the copy and the packaged file differ. The check runs on the host/CI (the repo root is **not**
   mounted in the API container).
4. **Consumer update:** `project-query-setup update` (Agent OS repository — an **external**
   deliverable, see §14) downloads the served file to a temp path, validates it is Python, writes
   it atomically, `chmod 755`, runs `--self-check`, and prints local vs API versions. It never
   overwrites a *newer* local copy without `--force`.
5. **Fallback if D1 is declined:** no endpoint and no test #20; the `update` verb copies from the
   canonical path in this repository (documented) or, for other machines, a pinned release
   artifact; `--self-check` still reports version skew loudly.
6. **Any distribution path must ship the `User-Agent` header.** A copy without it is non-functional
   against the hosted API and is rejected by the sync check (grep for `User-Agent`).

### R11 — Context summary counts (defect fix)

`GET /v1/agent/projects/{project_id}/context` must return the real counts — the same correlated
subqueries as `agent_list_projects` — instead of the zero defaults
(`agent_query.py:309` calls `_project_dict(project)` with no counts):

```json
"project": {
  "id": "…", "name": "Pizote", "slug": "pizote", "project_key": "PZT",
  "open_tasks": 1, "open_tickets": 4, "member_count": 3,
  "tasks_total": 1, "tickets_total": 4,
  "tasks_truncated": false, "tickets_truncated": false
}
```

- `open_tasks` / `open_tickets` / `member_count` are the same definitions as the list route
  (`status NOT IN ("done","cancelled")` / `("resolved","closed")`; `project_members` count).
- `tasks_total` / `tickets_total` are unfiltered counts; `*_truncated` is `true` when the
  100-row list cap clipped the array.
- Additive shape change; existing consumers of `project` are unaffected (I8).

### R12 — Ticket list filters

`GET /v1/agent/tickets` accepts `project_id` (UUID, optional) in addition to `ref`, `status`,
`limit`. `project_id` is tenant-checked the same way as the context endpoint; unknown or
foreign → empty page (list semantics, not 404).

### R13 — Read-only

New routes are `GET` only. No activity is inserted, no attachment mutated, no counter updated.
The only write on read paths is the existing `last_used_at` stamp for API keys (`deps.py:316`).

### R14 — Tenancy

Every lookup is tenant-scoped using the caller's resolved tenant (personal key owner or JWT
user). Cross-tenant access returns **404**. `X-Tenant-Slug` handling is inherited from
`require_agent_or_user`; no new header is introduced.

### R15 — Backward compatibility

Additive only: existing five endpoints keep their paths, fields and status codes. The context
project object gains fields (additive). The capabilities and MCP-file endpoints are new. Product
versioning is unchanged; `agent_api_version` is the contract version for clients.

**Base SPEC reconciliation (C11).** `20260701-SPEC.md` §R2 ("`AGENT_API_KEY` only"), §7 ("MCP
server connects to localhost only") and §8 ("Invalid agent API key") are **superseded** by the
shipped code (personal keys, superuser gate, remote base URLs) and by this amendment. The base
SPEC is Approved and is not edited; this paragraph is the authoritative delta.

### R16 — Limits and performance

- Detail ≤ **8** queries with activities, ≤ **6** without (ticket+project, attachments, activities
  page, activity count, activity attachments, linked commits, watchers, people lookup); actors are
  free (`Activity.actor` is `lazy="joined"`, `models/activity.py:45`).
- Activities page ≤ **3** queries (items, attachment batch, count).
- Per-ticket activity page ≤ 200; attachments per response ≤ 200 with `attachments_truncated`
  (description-referenced files are ordered first, so they are cut last).
- Binary responses stream; no request holds more than one file buffer (no sha256 ETag).
- Response size: description ≤ 32 KB (enforced at create, `TicketCreate`), activity bodies ≤ 32 KB.

### R17 — PII

Emails only for staff callers (R3). `requester_email` is hidden from client participants. No PII
in logs (ids only). Attachment `filename` may contain a person's name — it is data, not a log
field. No `storage_key`/paths in any JSON.

### R18 — Errors

4xx responses use FastAPI's standard envelope `{"detail": "<stable_code>"}` (C13); success uses
`{"ok": true, "data": …}`. Auth/permission failures never distinguish "exists elsewhere" from
"does not exist".

### R19 — Observability

Structured logs (existing logger + request id; the access log already records method/path/status):

- `agent.ticket_detail ticket_id=<id> project_id=<id> activities=<n> attachments=<n> result=ok|not_found|denied`
- `agent.ticket_activities ticket_id=<id> page=<offset>/<limit> result=…`
- `agent.attachment_read attachment_id=<id> project_id=<id> bytes=<n> mime=<…> result=…`

There is **no** Prometheus exporter in this deployment (verified: no `/metrics`, no client
library); counters are log-derived and documented as grep commands in `agent-query-api.md`, not
implemented as a new metrics stack.

### R20 — Index

Add one idempotent index in `sql/schema_indexes.sql` (applied by `run_pre_bootstrap` on every
start, after `schema_changes.sql`):

```sql
CREATE INDEX IF NOT EXISTS ix_activities_project_subject_created
    ON activities (project_id, subject_type, subject_id, created_at DESC);
```

`attachments.ticket_id`, `task_id` and `activity_id` are already indexed
(`sql/schema_indexes.sql:54-58`). No migration framework is used; `sql/*.sql` is applied at
startup (`Settings.sql_schema_apply`). The index build takes a brief write lock — acceptable at
current table size; note it in the deploy step.

### R21 — Docs

The doc set is split **by purpose, one home per fact** (C16):

| File | Owns | Change |
|------|------|--------|
| `.work/docs/agent-query-api.md` | Canonical endpoint + tool reference, auth, limits, versions | Add detail/activities/attachment/capabilities, resolved description recipe, availability matrix (1.0.0 live vs 1.1.0), correct the membership claim, registration and remote notes, Cloudflare UA note |
| `.work/docs/tutorials/LLM-2-API_SETUP.md` | Step-by-step connect (key → file → register → verify), refresh/update | Correct URLs, auth claims, add `update`/`--self-check` step |
| `.work/docs/guides/quick-reference-to-connect-agent-with-tools-project.md` | Decision guide: agent query (Case A) vs app-to-app (Case B) | Rewritten as a guide (the current file is a pasted chat transcript) |
| `.work/docs/tutorials/REPO_INTEGRATION.md` | GitHub link + plan sync + gotchas | Replace the "copy from pizote" workaround with the canonical update path; link the setup tutorial instead of duplicating it |
| `.work/docs/tutorials/AGENT_TICKET_CONTEXT.md` | Task tutorial: read a ticket with comments + images from another system | New; banner marks it as requiring `agent_api_version 1.1.0` until deployed |
| `.work/docs/tutorials/project-query-setup/` | Historical deployment record | Banner: canonical skill lives in the Agent OS repository; not an install source |
| Agent OS `skills/project-query-setup/skill.md` | Install/update skill | External deliverable: `update` verb, served-file download, `${path}` bug fix, UA note |

Also update the SPEC §14 implementation map and the feature README row if the tool list is
mirrored there. R21 is P0 for the connection/refresh instructions (consumers need them when the
API ships), not P2.

### R22 — Acceptance

Against the deployed API with a personal key (python3, no `jq` dependency):

```bash
BASE=$(grep '^BASE_URL=' ~/.tools-project-key | cut -d= -f2-)
KEY=$(grep -v '^BASE_URL=' ~/.tools-project-key | head -n1)
UA='User-Agent: tools-project-mcp/1.1.0'

# 1. detail by ref: counts, web_url, people, attachments
curl -s "$BASE/v1/agent/tickets/PZT-T-1" -H "X-Api-Key: $KEY" -H "$UA" | python3 -c '
import json,sys; t=json.load(sys.stdin)["data"]["ticket"]
print(t["ref"], t["counts"], t["attachments_truncated"], t["web_url"])
print("desc-resolved:", "v1/agent/attachments/" in t["description_resolved"])
print("people:", bool(t["reporter"]), t["assignee"])'

# 2. comments/activity (assert at least one item exists on a ticket that has a thread)
curl -s "$BASE/v1/agent/tickets/PZT-T-1/activities?order=asc&limit=200" \
  -H "X-Api-Key: $KEY" -H "$UA" | python3 -c '
import json,sys; d=json.load(sys.stdin)["data"]
print("items:", len(d["items"]), "total:", d["total"], "order:", d["order"])'

# 3. the three PZT screenshots stream as images
for id in 54830228-0c70-4c62-8149-bf967f47af86 \
          8b3cd170-7b4b-4170-a889-53e1dd22798a \
          841a6851-536d-4d48-ab75-8fb8becc302d; do
  curl -s -o "tmp/$id" -w "%{http_code} %{content_type} %{size_download}\n" \
    "$BASE/v1/agent/attachments/$id" -H "X-Api-Key: $KEY" -H "$UA"
  file "tmp/$id"          # PNG image data, …
done

# 4. capabilities + MCP self-check of the downloaded copy (never clobber a working copy blindly)
curl -s "$BASE/v1/agent/capabilities" -H "X-Api-Key: $KEY" -H "$UA" | python3 -m json.tool
curl -s -o tmp/mcp_server.py "$BASE/v1/agent/client/mcp_server.py" -H "X-Api-Key: $KEY" -H "$UA"
python3 -m py_compile tmp/mcp_server.py                      # fails on an HTML error page
python3 tmp/mcp_server.py --self-check
cp tmp/mcp_server.py .opencode/mcp/project-mcp/mcp_server.py && chmod 755 .opencode/mcp/project-mcp/mcp_server.py
```

Accepted when: every command above passes; every test in §11 is green; `ruff`/`pyright` unchanged;
no new tables; the served MCP file drives a successful `get_attachment` image block for
`54830228-…`; and a client participant key is denied the internal note and any ticket not assigned
to their company (manual, staging).

---

## 5. Data model

No new tables. Existing rows used:

| Table | Columns | Use |
|-------|---------|-----|
| `tickets` | all | detail (reporter_id, requester_email, queue_slug, first_response_at, resolved_at, closed_at are missing from today's agent payload) |
| `activities` | all | feed, internal notes, meta_json, `subject_type/subject_id`, `parent_activity_id` |
| `attachments` | all | metadata + bytes (never `storage_key`) |
| `commit_subject_refs` + `github_commits` | all | per-ticket linked commits (resolved and pending) |
| `watchers` | user_id, subject_type, subject_id | watcher list (populated via `/v1/me/watch`) |
| `users` | id, display_name, email | actor/reporter/assignee/watcher |
| `project_members` | role | staff vs client participant (via `resolve_project_access`) |
| `project_client_access` | role, can_view_* | client subject visibility |

One additive index (R20).

---

## 6. APIs

### New endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/v1/agent/tickets/{ticket}` | agent auth | Ticket detail (R3) |
| GET | `/v1/agent/tickets/{ticket}/activities` | agent auth | Activity feed (R6) |
| GET | `/v1/agent/attachments/{attachment_id}` | agent auth | Binary download (R7) |
| GET | `/v1/agent/capabilities` | agent auth | Version/capability handshake (R8) |
| GET | `/v1/agent/client/mcp_server.py` | agent auth | Canonical MCP server file (R10, D1) |

### Changed endpoints

| Method | Path | Change |
|--------|------|--------|
| GET | `/v1/agent/projects/{project_id}/context` | real counts + totals/truncation flags (R11) |
| GET | `/v1/agent/tickets` | optional `project_id` filter (R12) |

### Reused internals (do not duplicate logic)

- `api/app/routers/attachments.py` — extract the storage lookup, visibility check and headers into
  `app/services/attachment_serve.py`; the JWT route and the agent route both call it.
- `api/app/routers/activities.py` + `app/services/activity_visibility.py` — reuse the visibility
  predicate (`client_activity_condition`, `is_client_participant`) and factor the filter builder
  into `app/services/activity_query.py`.
- `api/app/services/project_access.py` — `require_project_access`, `is_client_participant`,
  `can_view_tickets`, `client_company_user_ids`.

---

## 7. Invariants

- **I1** Read-only: no mutation endpoint, no activity row, no attachment change.
- **I2** No `storage_key`, disk path, or absolute filesystem path in any JSON.
- **I3** Attachments are served only after an access check on their own project; failures are 404.
- **I4** Internal notes and their attachments never reach a client participant.
- **I5** Tenant boundary is the same as the rest of `/v1/agent/*`; cross-tenant = 404.
- **I6** `description` is returned byte-identical; `description_resolved` is additive.
- **I7** Attachment bytes are served with the stored mime **and** an allowlist re-check.
- **I8** Existing five endpoints and their fields are unchanged; the only additions to them are
  new fields (context counts) and a new query parameter (`project_id`).
- **I9** The MCP server degrades (hides tools) when the API is older; it never crashes and never
  blocks `initialize` on the network.
- **I10** Every new route is covered by an auth-matrix test (401/403/404/200).
- **I11** Client participants see only subjects assigned to their company — the same rule as the
  web list/activity routes — at the detail, activity and binary endpoints.
- **I12** Every MCP distribution path sends the Cloudflare-safe `User-Agent`.

---

## 8. Error model

| Condition | HTTP | Body |
|-----------|------|------|
| No credentials / bad key | 401 | `{"detail": "Not authenticated"}` |
| Bearer user not superuser (agent gate) | 403 | `{"detail": "Agent endpoints require superuser privileges"}` |
| Client participant requests `visibility=internal` | 403 | `{"detail": "Client participants cannot view internal activities"}` |
| Unknown ticket (uuid or ref) | 404 | `{"detail": "ticket_not_found"}` |
| Ticket in another project/tenant, not visible, or caller has no access | 404 | `{"detail": "ticket_not_found"}` |
| Unknown attachment / missing file / bad storage key | 404 | `{"detail": "attachment_not_found"}` |
| Attachment of an internal note, or of an invisible subject, client participant | 404 | `{"detail": "attachment_not_found"}` |
| Stored mime not in `ALLOWED_MIMES` | 404 | `{"detail": "attachment_not_found"}` |
| MCP file not available (D1 declined) | 404 | `{"detail": "mcp_server_file_unavailable"}` |
| `limit`/`offset`/`kind`/`visibility` invalid | 422 | FastAPI validation error |
| API older than the MCP server expects | n/a | `/capabilities` returns the old version; client hides tools |

The `detail` string is a stable machine token; clients must not parse human prose.

---

## 9. Observability

- The three log lines in R19, at `INFO` for success and `WARNING` for `denied`.
- Log-derived counters (no metrics stack in this deployment):
  `grep -c 'agent.ticket_detail .* result=ok'` etc.; document the exact commands in
  `agent-query-api.md`.
- Request id propagation already exists (`request_id_middleware` in `app/main.py`).
- No filenames, emails, or bodies in logs.

---

## 10. Security and privacy

- Attachment downloads are audited by log line (R19); the personal key owner is the actor.
- The API key remains read-only: no possibility to upload, comment, or transition.
- Internal notes and subject visibility are hard boundaries: enforced at the metadata and the
  binary endpoint (defence in depth — do not rely on the list filter).
- `Content-Disposition` filename sanitisation: strip CR/LF/quotes, cap 200 chars; the stored name
  is already sanitised at upload (`_safe_filename`) but re-sanitise for the header.
- `nosniff` + `CSP: sandbox` on bytes; SVG is not uploadable (`ALLOWED_MIMES`), so the classic
  image-based XSS vector is closed.
- The `storage_key` never leaves the server; `path_for_key` rejects traversal.
- Personal keys are tenant-scoped and hashed (SHA-256) already; no new secret is introduced.
- Serving the MCP file exposes client code only; it contains no secrets (it reads the key file at
  runtime) and requires the same agent auth.
- Public base URLs are emitted to the authenticated caller only; reading `X-Forwarded-*` for that
  purpose has no cross-caller effect (no cache, no redirect).

---

## 11. Test plan

New `api/tests/test_agent_ticket_context.py` (fixtures: `client`, `db`, `api/tests/factories.py`;
the suite has 12 modules / 80 tests today) and `api/tests/test_mcp_server.py` (imports
`app.client.mcp_server`, monkeypatches its HTTP helper — no network).

| # | Test | Asserts |
|---|------|---------|
| 1 | `test_detail_by_uuid_and_ref` | identical payload for UUID and `PZT-T-1` |
| 2 | `test_detail_unknown_ticket_is_404` | 404 + `ticket_not_found` |
| 3 | `test_detail_other_tenant_is_404` | tenant boundary |
| 4 | `test_detail_requires_auth` | 401 without key; 403 for non-superuser JWT |
| 5 | `test_detail_includes_attachments_and_resolved_description` | `download_url` substituted, `markdown_ref` set, `description` byte-identical |
| 6 | `test_detail_unknown_attachment_ref_left_untouched` | no 500, markdown intact |
| 7 | `test_detail_includes_activities_and_commits` | counts, page, linked commits (`state`) |
| 8 | `test_detail_attachments_capped_with_flag` | 201 attachment fixtures → 200 items, `attachments_truncated=true`, true count |
| 9 | `test_activities_pagination_and_order` | `limit`/`offset`/`order` (both directions), `has_more`, `next_offset` |
| 10 | `test_activities_internal_hidden_from_client_participant` | items absent; `visibility=internal` → 403 |
| 11 | `test_client_participant_subject_visibility` | ticket/comment/attachment of another company → 404 (detail, activity, binary) |
| 12 | `test_attachment_download_streams_bytes` | 200, `Content-Type`, `Content-Length`, bytes equal |
| 13 | `test_attachment_download_unknown_is_404` | 404 |
| 14 | `test_attachment_download_internal_note_hidden_from_client` | 404 |
| 15 | `test_attachment_download_bad_storage_key_is_404` | traversal rejected |
| 16 | `test_attachment_download_disposition` | `?download=1` → `attachment`; no `ETag` |
| 17 | `test_no_storage_key_in_any_agent_payload` | recursive scan of detail/activities JSON (I2) |
| 18 | `test_capabilities_lists_new_features` | version, capabilities, limits, recommended MCP version |
| 19 | `test_context_counts_are_real` | fixture: 3 members, 1 open task, 4 tickets (1 resolved) → `1/4/3`, totals correct |
| 20 | `test_context_truncation_flags` | >100 tasks → `tasks_truncated=true` |
| 21 | `test_ticket_list_filters_by_project` | `project_id` filter |
| 22 | `test_served_mcp_file_matches_packaged_module` | served bytes == `app/client/mcp_server.py` (in-container) |
| 23 | `test_mcp_get_attachment_returns_image_block` | fake PNG bytes → `image` block; oversize → saved path + sha256 |
| 24 | `test_mcp_sends_user_agent` | fake opener records headers (I12) |
| 25 | `test_mcp_tools_degrade_on_old_api` | capabilities 1.0.0 → newer tools hidden, no crash |
| 26 | `test_mcp_never_prints_key` | error strings exclude the key |

Manual (deployment gate): R22 against the remote, plus the three PZT screenshots confirmed by
`file`, plus a client-participant denial check in staging.

---

## 12. Rollout and rollback

Additive, no feature flag. **D1–D3 must be decided before P0.**

**P0 — unblock the screenshots (smallest diff, ship first):**
1. Fix the MCP `User-Agent` in the canonical source (F1) — nothing else ships before this.
2. `api/app/services/activity_query.py`: the shared activity filter/visibility builder (used by
   the inline detail page in P0 and by the HTTP route in P1 — no duplicate logic).
3. `api/app/services/attachment_serve.py`: extract the download body; agent attachment route.
4. `api/app/routers/agent_query.py`: `GET /v1/agent/tickets/{ticket}` (ticket + attachments +
   counts + people + web URL + inline activity page).
5. MCP: `get_attachment`, `get_ticket_detail`, `SERVER_VERSION`, `--self-check`, `--version`.
6. Tests #1–#8, #12–#17, #23, #24, #26; docs for what now exists (R21: reference + tutorial).
7. Deploy; refresh the repo MCP copy; verify the three screenshots and a comment thread.

**P1 — activity route:** `GET /v1/agent/tickets/{ticket}/activities` over the shared builder,
client-participant visibility edge cases, MCP `list_ticket_activities`, tests #9–#11.

**P2 — hardening and distribution:** capabilities handshake, served MCP file (D1), context counts,
`project_id` filter, index (R20), remaining docs, framework skill `update` verb (external), tests
#18–#22, #25.

**Deploy steps (remote):** rebuild/restart the API container; the startup DDL applies the index
idempotently (brief write lock); no data migration; product version stays `0.1.x` while
`agent_api_version` becomes `1.1.0`. Verify `/v1/agent/capabilities` and the R22 commands.

**Rollback:** remove the new routes (additive); the served MCP file endpoint can be disabled
independently; the index is harmless if left.

---

## 13. Open questions

| # | Question | Recommendation | Status |
|---|----------|----------------|--------|
| Q1 | Relax the agent-superuser gate so a personal key only needs project membership (as the docs claim)? | **Keep** the gate for 1.1.0 and fix the docs; plan membership-scoped keys for 1.2.0. The new routes already enforce the F3 predicates, so the relaxation is one line + tests. | Decided 2026-10-30 (D3) |
| Q2 | Signed, expiring attachment URLs instead of key-authenticated bytes? | **No.** The key is read-only and revocable; signed URLs add a second secret surface and leak into logs/links. Keep key-auth + audit. | Closed |
| Q3 | Serve the MCP server from the API (R10) or keep copy-from-repo? | Serve it — consuming repos drift today and the canonical copy is broken (F1). Requires **D1**. | Decided 2026-10-30 (D1) |
| Q4 | Inline image cap for MCP `image` blocks? | **5 MiB** default, env-tunable; above it save + return the path. | Closed |
| Q5 | Include `requester_email` and reporter emails? | Yes for staff callers (already in `members[]`); no for client participants. | Closed |
| Q6 | Attachment retention vs ticket evidence? | Already `0` = never purge (`Settings.attachment_retention_days`); keep it and document the operational rule. No change. | Closed (F15) |
| Q7 | Where is the canonical MCP source? | `api/app/client/mcp_server.py` (packaged, served, testable); `.opencode/…` is a refreshed copy (C2/D1). | Decided 2026-10-30 (D1) |

---

## 14. Implementation map

| Layer | Path | Change |
|-------|------|--------|
| Agent router | `api/app/routers/agent_query.py` | detail, activities, capabilities, counts fix, `project_id` filter |
| Agent attachments | `api/app/routers/agent_attachments.py` | binary download route (new file) |
| Attachments | `api/app/routers/attachments.py` | extract `_serve_attachment` → `app/services/attachment_serve.py` |
| Activities | `api/app/routers/activities.py` + `api/app/services/activity_query.py` | shared filter/visibility builder (new service) |
| Visibility | `api/app/services/activity_visibility.py`, `project_access.py` | reuse; add subject-visibility helper for attachments if needed |
| Schemas | `api/app/schemas.py` | `AgentTicketDetailOut`, `AgentAttachmentOut`, `AgentActivityOut`, `AgentCapabilitiesOut` |
| Config | `api/app/config.py` | `public_api_base_url`, `public_web_base_url` (optional) |
| Compose / env | `docker-compose.dev.yml`, `docker-compose.prd.yml`, `.env.example` (and secret `.env.prd`) | pass the two base URLs — **protected, D2** |
| DDL | `sql/schema_indexes.sql` | R20 index |
| Router registration | `api/app/main.py` | register the agent attachment router |
| MCP (canonical) | `api/app/client/mcp_server.py` | 3 tools, UA, `SERVER_VERSION`, `--self-check`, `--version`, lazy probe |
| MCP (served) | `api/app/routers/agent_query.py` | `GET /v1/agent/client/mcp_server.py` |
| MCP (repo copy) | `.opencode/mcp/project-mcp/mcp_server.py` | refreshed copy |
| MCP sync | `bin/mcp-sync.sh` | `check` / `sync` between packaged and repo copy |
| Docs | `.work/docs/agent-query-api.md`, `.work/docs/tutorials/{LLM-2-API_SETUP,REPO_INTEGRATION,AGENT_TICKET_CONTEXT}.md`, `.work/docs/guides/quick-reference-to-connect-agent-with-tools-project.md` | R21 |
| External skill | `/mnt/work/Projects/pilo.ai.logicbison/skills/project-query-setup/` | `update` verb, download path, `${path}` fix — **separate repo, owner approval** |
| Tests | `api/tests/test_agent_ticket_context.py`, `api/tests/test_mcp_server.py` | §11 |

**Effort (estimated):** P0 ≈ 1 dev-day; P1 ≈ 1 day; P2 ≈ 1 day + review.

---

## 15. Concept / NFR registry

| Concept id | Applies | Notes |
|------------|---------|-------|
| MOD-01 | no | No new bounded context; existing ticket/activity/attachment modules |
| MOD-02 | no | No AI-assisted PR in this change |
| MOD-03 | no | No cost-sensitive decision |
| MOD-04 | no | No distributed-system concern (one service + one client) |
| MOD-05 | yes | Project evidence contains customer PII (screenshots, emails) — access is audited and role-scoped |
| MOD-06 | yes | Agent-facing surface; review the boundary between web session and agent key before implementation |
| MOD-07 | no | No app-side LLM prompt composition |
| MOD-08 | no | No IaC change |

---

## 16. Verification record (2026-10-30)

Verified against `HEAD 9d9e53d` and the deployed API `0.1.3`; evidence and probe log in
[`20261030-amendment-01-verification.md`](20261030-amendment-01-verification.md). The filename is
retained (it is already referenced by NEXT/HANDOFF) although the framework naming convention adds
a short slug.

### Change log — corrections applied to this draft

| Id | Section | Correction |
|----|---------|------------|
| C1 | R9, R10, §12 | MCP sends a Cloudflare-safe `User-Agent`; P0 starts with this fix; sync check rejects copies without it |
| C2 | R10, §14 | Canonical MCP moves to `api/app/client/mcp_server.py` (fits `context: ./api`); repo copy is refreshed; test #22 compares served vs packaged |
| C3 | R2, R6, §6 | Client subject visibility reuses `client_activity_condition` / `can_view_tickets` / `client_company_user_ids` |
| C4 | R3, R5, §3, §14 | `PUBLIC_API_BASE_URL` / `PUBLIC_WEB_BASE_URL`; `web_url` null when unset; protected wiring called out |
| C5 | R3, §3 | `description` (verbatim) + `description_resolved`; `created_by` removed; inline page order defined |
| C6 | R7 | No ETag; headers fixed; Content-Length from disk |
| C7 | R8, R9 | Client-side inline caps removed from server limits; lazy capability probe; `SERVER_VERSION` source of truth |
| C8 | R9 | Text cap env, image mime check, save-dir fallback, sha256 of saved bytes |
| C9 | R10, §14 | `project-query-setup` is an external deliverable; `${path}` skill bug recorded |
| C10 | R11 | Exact context-count fields and shape |
| C11 | R15 | Base SPEC sections superseded explicitly (no silent contradiction) |
| C12 | R3, R16 | Attachment cap + `attachments_truncated` + true counts |
| C13 | R18, §8 | `{"detail": "<code>"}` instead of an unimplementable `{"ok": false}` |
| C14 | R16 | Query budget 8/6 |
| C15 | §11 | Fixture-based tests, auth matrix, I2/I6/UA/visibility tests, in-container #22 |
| C16 | R21 | Doc ownership split; `quick-reference` rewrite; availability matrix |
| C17 | R21, §10 | Existing doc corrections (membership claim, localhost-only, env registration, version) |
| C18 | R10, §12 | Rollout order; P0 includes the connection/refresh docs |
| C19 | R22 | Acceptance uses python3, adds comments/`web_url`/downloaded-file checks |

### Owner decisions

**Decided 2026-10-30 on approval:** D1 and D3 accepted as recommended. D2 accepted in principle — the
protected-file edit (`docker-compose.dev.yml`, `docker-compose.prd.yml`, `.env.example`, and the
secret `.env.prd`) still requires **explicit in-message approval** when implementation reaches it
(`.cursorrules` § Protected Files); if declined, the documented fallback applies (`web_url = null`,
request-derived API base URLs).

| Id | Decision | Recommendation | Decision |
|----|----------|----------------|----------|
| D1 | R10: packaged canonical MCP + served file + repo copy (vs copy-from-repo only) | Approve | **Accepted** 2026-10-30 |
| D2 | Protected files: the two public base URLs in compose + `.env.example` (and secret `.env.prd`) | Approve (or accept `web_url = null`) | **Accepted in principle**; edit-time approval required |
| D3 | Q1: keep the superuser gate for 1.1.0 and fix the docs | Approve | **Accepted** 2026-10-30 |
