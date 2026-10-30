# Agent Ticket Context & Attachments — Feature SPEC amendment 01

**Status:** Draft — pending owner review
**Owner:** Engineering
**Amends:** [`20260701-SPEC.md`](20260701-SPEC.md) (agent-query-api, Approved)
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
plus the MCP tools that expose them. It keeps the surface **read-only** and reuses the
existing attachment, activity and tenancy models — no new tables, no new storage.

### 1.1 Why now

A report that is only text can be read; a report that is mostly a screenshot cannot. PZT-T-2
("documentos fallidos") names a cartel but the failing state is in the screenshot; PZT-T-3
("botón para explorar cartel") is a visual affordance that only exists in the screenshot.
The agent's only alternatives today are to ask the operator to re-paste the images or to
guess — neither is acceptable for a platform whose purpose is to carry project evidence.

### 1.2 Evidence (live, 2026-10-30, remote `v0.1.3`)

| Need | Call (personal agent key) | Result |
|------|---------------------------|--------|
| project + tickets + descriptions | `GET /v1/agent/projects/{pzt}/context` | **200** — 4 tickets, 3 image refs |
| screenshot bytes (API) | `GET /v1/attachments/54830228-…` | **401** |
| screenshot (link inside the description) | `GET /api/attachments/54830228-…` | **401** — web session cookie required |
| ticket detail | `GET /v1/agent/tickets/{uuid}` | **404** — route absent |
| comments / activity | — | **no agent endpoint** (`/v1/projects/{id}/activities` → 401) |
| reporter / requester / queue / resolution timestamps | — | absent from the agent payload |
| attached filename / mime / size | — | absent |
| context summary counts | `open_tasks/open_tickets/member_count` | **0 / 0 / 0** (actual: 1 / 4 / 3) |
| MCP tools for the above | — | absent (5 tools today) |

---

## 2. In scope / Out of scope

### In scope

- `GET /v1/agent/tickets/{ticket}` — full ticket detail (ticket, reporter/assignee, counts,
  watchers, attachments, first activity page, per-ticket commits, URLs).
- `GET /v1/agent/tickets/{ticket}/activities` — paginated, filterable activity feed.
- `GET /v1/agent/attachments/{attachment_id}` — binary download, agent-authenticated.
- `GET /v1/agent/capabilities` — version/capability handshake.
- MCP tools `get_ticket_detail`, `list_ticket_activities`, `get_attachment` (+ version constant
  and self-check).
- Fix the context endpoint's zeroed summary counts and add truncation flags.
- `project_id` filter on `GET /v1/agent/tickets`.
- Docs (`.work/docs/agent-query-api.md`), tests, and the copy/update path for the MCP server.

### Out of scope

- Any write/comment/upload/transition through the agent API (stays read-only).
- Unauthenticated or public share links for attachments.
- Server-side OCR/vision, thumbnails, or image transformation.
- Changing storage (local disk under `ATTACHMENTS_DIR`) or the upload allowlist.
- Web UI changes (the existing `/api/attachments/<id>` proxy is untouched).
- Relaxing the agent-superuser gate (see Q1 — deliberately deferred).

---

## 3. Domain language

| Term | Definition |
|------|------------|
| Agent principal | The user resolved from an `X-Api-Key` (personal key) or a Bearer JWT. |
| Ticket address | The ticket UUID **or** its `ref` (`PZT-T-1`). `tickets.ref` is globally unique. |
| Activity | A row in `activities`: `comment`, `note` (aliased to `comment`), `status_change`, `assignment`, `attachment`, `github_commit`, `mention`, `system`, `transition`. |
| Internal note | An activity with `is_internal = true`; staff-only. |
| Attachment scope | Where a file hangs: `ticket` (`attachments.ticket_id`) or `activity` (`attachments.activity_id`). |
| Capability | A named feature advertised by `/v1/agent/capabilities` so clients can degrade gracefully. |
| Resolved markdown | `description_markdown` with every `/api/attachments/<uuid>` replaced by the absolute agent `download_url`. |

---

## 4. Behavioural spec

### R1 — Ticket addressing

`{ticket}` in every path below accepts the ticket UUID or its `ref` (trimmed,
case-insensitive). Lookup order: parse as UUID; otherwise lookup by `ref`. Unknown → 404.
Tickets are resolved **after** tenant/access checks so a foreign ticket is indistinguishable
from a missing one.

### R2 — Authentication and authorization

All new endpoints use `require_agent_or_user` (same as the existing `/v1/agent/*` routes):
personal `X-Api-Key` → its owner; shared `AGENT_API_KEY` → synthetic superuser only when
multi-tenancy is disabled; Bearer JWT → the user. After authentication:

1. `require_project_access(db, user, ticket.project_id)` — a permission failure is returned
   as **404** (no existence leak), matching `resolve_project_access` semantics.
2. Client participants (`acc.client_access is not None`) never receive internal notes or
   their attachments.
3. The agent-superuser gate (`_require_agent_superuser`) is **kept unchanged** in this
   amendment; Q1 records the follow-up. Consequently every caller of the new routes is a
   superuser today, but the project-access check is still performed and tested so the gate
   can be relaxed later without a rewrite.

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
      "title": "Sin correos de reporte",
      "description_markdown": "…![Screenshot 2026-10-19 at 5.19.31 PM.png](/api/attachments/54830228-0c70-4c62-8149-bf967f47af86)",
      "description_markdown_resolved": "…![Screenshot 2026-10-19 at 5.19.31 PM.png](https://project.cloudsys.win/v1/agent/attachments/54830228-0c70-4c62-8149-bf967f47af86)",
      "status": "in_progress",
      "priority": "normal",
      "queue_slug": "default",
      "requester_email": null,
      "reporter":   { "id": "…", "display_name": "…", "email": "…" },
      "assignee":   { "id": "…", "display_name": "…", "email": "…" },
      "created_at": "2026-10-19T23:17:02Z",
      "updated_at": "2026-10-30T21:52:10Z",
      "first_response_at": null,
      "resolved_at": null,
      "closed_at": null,
      "web_url": "https://project.cloudsys.win/projects/19b24527-128d-4087-ac48-41979c619c11/tickets/8fb47f08-8daf-457f-b798-149e8e4eaf60",
      "watchers": [ { "id": "…", "display_name": "…", "email": "…" } ],
      "counts": { "activities": 0, "attachments": 1, "linked_commits": 1 },
      "attachments": [ /* R5 */ ],
      "activities": [ /* R6, first page — omitted when include_activities=false */ ],
      "activities_page": { "total": 0, "has_more": false, "next_offset": null },
      "linked_commits": [
        { "sha": "9a31e21…", "short_sha": "9a31e21", "html_url": "https://github.com/…",
          "message_preview": "…", "author_name": "…", "committed_at": "…" }
      ]
    },
    "project": { "id": "…", "name": "Pizote", "slug": "pizote", "project_key": "PZT" }
  }
}
```

Rules:

- `reporter` / `assignee` / `created_by` / watchers expose `email` **only for staff callers**
  (`acc.client_access is None`); client participants get `display_name` only. The email is
  already exposed by `members[]` in the context endpoint, so this is not new exposure.
- `description_markdown` is returned **verbatim** — never rewritten in place (round-trip
  safety for clients that post it back).
- `assignee` is `null` when unassigned.
- Query knobs: `include_activities` (default `true`), `activity_limit` (1…200, default 50,
  clamped), `include_internal` (default `true` for staff, ignored/forced `false` for client
  participants), `include_description_resolved` (default `true`).
- Bounded work: ≤ 7 queries regardless of activity count (R20).

### R4 — Resolved markdown

`description_markdown_resolved` replaces every occurrence of
`](/api/attachments/<uuid>)` — both image `![alt](…)` and link `[name](…)` forms — with the
absolute `download_url` of that attachment. Rules:

1. Only exact `/api/attachments/<uuid>` targets are replaced.
2. An attachment id that is unknown, not attached to this ticket, or not visible to the
   caller is **left as-is** (no 500, no information leak). It is also absent from
   `attachments[]`.
3. The response always includes `description_markdown` so a client can rebuild if needed.
4. `description_attachments[]` is *not* a separate list: every attachment referenced by the
   description also appears in `attachments[]` with `"markdown_ref"` set (R5).

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

- `scope` is `"ticket"` when `ticket_id` is set, `"activity"` when `activity_id` is set.
- `markdown_ref` is `null` unless the description references the attachment.
- **Never** include `storage_key`, the disk path, or `project_id`-less data.
- Ordering: description-referenced first (in order of appearance), then the rest by
  `created_at` ascending.

### R6 — `GET /v1/agent/tickets/{ticket}/activities`

Query: `limit` (1…200, default 50), `offset` (≥0), `order` (`asc|desc`, default `desc`),
`kind` (validated against `ACTIVITY_KINDS`), `include_internal` (default `true` for staff,
forced `false` for client participants), `visibility` (`all|internal|external`, default
`all`; `internal` is 403 for client participants — same as the web endpoint).

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
        "attachments": [ /* R5 with scope=activity */ ],
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

- `meta_json` is passed through (status transitions carry from/to; `github_commit` carries
  the link). It is already stored, so this adds no new data.
- Attachments for the whole page are fetched in **one** query (R20).

### R7 — `GET /v1/agent/attachments/{attachment_id}` — binary

- Auth: R2. `require_project_access` on the attachment's project; **404** on any failure.
- Internal-note attachments (`activity.is_internal`) → 404 for client participants.
- Response: the stored bytes, streamed (`FileResponse`), never base64 inside JSON.
- Headers:
  - `Content-Type`: stored `mime` **re-validated against `ALLOWED_MIMES`**; anything else → 404.
  - `Content-Length`: `size_bytes`.
  - `Content-Disposition`: `inline; filename="<sanitized>"; filename*=UTF-8''<percent-encoded>`.
    `?download=1` switches to `attachment`.
  - `ETag`: `"<sha256 of bytes>"` (computed once per request; 25 MB worst case is acceptable)
    or, if that is judged too costly, `"<storage_key>-<size_bytes>"` — pick one and test it.
  - `Cache-Control: private, max-age=0, no-store`; `X-Content-Type-Options: nosniff`;
    `Content-Security-Policy: sandbox`; `Referrer-Policy: no-referrer`.
- Missing DB row, missing file on disk, or invalid `storage_key` → 404
  (`path_for_key` already rejects traversal).
- Range requests are out of scope.

### R8 — `GET /v1/agent/capabilities`

```json
{ "ok": true, "data": {
  "agent_api_version": "1.1.0",
  "capabilities": ["ticket_detail", "ticket_activities", "attachments", "attachment_download", "capabilities"],
  "limits": { "activities_default": 50, "activities_max": 200,
              "attachment_max_bytes": 26214400, "inline_image_max_bytes": 5242880 },
  "mcp_server": { "version": "1.1.0",
                  "download_url": "https://project.cloudsys.win/v1/agent/client/mcp_server.py" }
} }
```

Authenticated. The MCP server calls it at startup; if `agent_api_version` is older than the
tools require, it logs a warning and hides the newer tools (no hard failure).

### R9 — MCP tools (`.opencode/mcp/project-mcp/mcp_server.py`)

| Tool | Input | Returns |
|------|-------|---------|
| `get_ticket_detail` | `ticket` (uuid or ref), `include_activities` (bool, default true), `include_internal` (bool, default true), `activity_limit` (default 50) | one `text` content block with the R3 JSON |
| `list_ticket_activities` | `ticket`, `limit`, `offset`, `kind`, `include_internal` | one `text` content block with the R6 JSON |
| `get_attachment` | `attachment_id`, `save_dir` (optional) | `image` content block (`{"type":"image","data":"<base64>","mimeType":"image/png"}`) when `is_image` and `size_bytes ≤ inline_image_max_bytes`; `text` block for `text/plain` ≤ 1 MB; otherwise the file is written to disk and a `text` block returns `{path, filename, mime, size_bytes, sha256}`. A metadata `text` block always accompanies the content block. |

Rules:

- Image inline default cap **5 MiB** (`TOOLS_PROJECT_INLINE_IMAGE_MAX_BYTES`); above it,
  save + return the path (never truncate silently).
- `save_dir` defaults to `~/.cache/tools-project/attachments/` (mode `700`), filename
  sanitized (`Path(name).name`, strip `..`), collisions suffixed, never outside the dir.
- Every tool returns `{"ok": false, "error": "…"}` as text on failure — the server never
  crashes the transport.
- `SERVER_VERSION = "1.1.0"`; `--self-check` calls `/v1/agent/capabilities` and prints the
  detected version + enabled tools.
- The 5 existing tools keep their names and payloads unchanged.

### R10 — MCP server distribution

The MCP server is **copied** into each consuming repository
(`.opencode/mcp/project-mcp/mcp_server.py`), so a new tool does not reach existing consumers
until the file is refreshed. Requirements:

1. `GET /v1/agent/client/mcp_server.py` serves the canonical file from the deployed API,
   authenticated by the same agent auth, `Content-Type: text/x-python`,
   `Content-Disposition: attachment; filename="mcp_server.py"`. The served file must be
   byte-identical to the repo copy at that release (verified by a test that reads both).
2. `project-query-setup` gains an `update` verb: fetch that URL against `BASE_URL` and write
   the file, `chmod 755`, then run `--self-check`.
3. If (1) is rejected during review, the fallback is: document "re-copy from
   `/mnt/work/Projects/tools-project/.opencode/mcp/project-mcp/mcp_server.py`", and stamp
   `SERVER_VERSION` so a stale copy is visible. Q3 records the decision.

### R11 — Context summary counts (defect fix)

`GET /v1/agent/projects/{project_id}/context` must compute the real
`open_tasks` / `open_tickets` / `member_count` (the same correlated subqueries as
`agent_list_projects`), not the zero defaults. Add:

- `tasks_total`, `tickets_total` (all statuses, matching the 100-row cap),
- `tasks_truncated`, `tickets_truncated` (`true` when the 100-row limit clipped the list).

### R12 — Ticket list filters

`GET /v1/agent/tickets` accepts `project_id` (UUID, optional) in addition to `ref`, `status`,
`limit`. `project_id` is tenant-checked the same way as the context endpoint.

### R13 — Read-only

New routes are `GET` only. No activity is inserted, no attachment mutated, no counter
updated. The only write on read paths is the existing `last_used_at` stamp for API keys.

### R14 — Tenancy

Every lookup is tenant-scoped using the caller's resolved tenant (personal key owner or JWT
user). Cross-tenant access returns **404**. `X-Tenant-Slug` handling is inherited from
`require_agent_or_user`; no new header is introduced.

### R15 — Backward compatibility

Additive only: existing five endpoints keep their paths, fields and status codes. The
capabilities endpoint is new. Product versioning is unchanged; `agent_api_version` is the
contract version for clients.

### R16 — Limits and performance

- Per-ticket activity page ≤ 200; attachments per response ≤ 200 (a ticket with more
  attachments is truncated and `counts.attachments` reports the true total).
- Detail ≤ 7 queries; activities page ≤ 3 (items, attachment batch, count).
- Binary responses stream; no request holds more than one file buffer.
- Response size: description ≤ 32 KB (enforced at create), activity bodies ≤ 32 KB each.

### R17 — PII

Emails only for staff callers (R3). No PII in logs (ids only). Attachment `filename` may
contain a person's name — it is data, not a log field. No `storage_key`/paths in any JSON.

### R18 — Errors

See §8. Auth/permission failures never distinguish "exists elsewhere" from "does not exist".

### R19 — Observability

Structured logs (existing logger + request id):

- `agent.ticket_detail ticket_id=<id> project_id=<id> activities=<n> attachments=<n> result=ok|not_found|denied`
- `agent.ticket_activities ticket_id=<id> page=<offset>/<limit> result=…`
- `agent.attachment_read attachment_id=<id> project_id=<id> bytes=<n> mime=<…> result=…`

Counters (Prometheus/`/metrics` if the deployment exports them; otherwise log-derived):
`agent_ticket_detail_total{result}`, `agent_attachment_read_total{mime,result}`.
No body/filename/email in logs.

### R20 — Index

Add one idempotent index in `sql/schema_indexes.sql` (the startup DDL runner applies it):

```sql
CREATE INDEX IF NOT EXISTS ix_activities_project_subject_created
    ON activities (project_id, subject_type, subject_id, created_at DESC);
```

`attachments.ticket_id` and `attachments.activity_id` are already indexed (`index=True`
in the model → `CREATE INDEX` in `sql/`). No migration framework is used in this repo;
`sql/*.sql` is applied idempotently at startup (`Settings.sql_schema_apply`).

### R21 — Docs

Update `.work/docs/agent-query-api.md`: endpoints table, response examples, auth note that
attachment bytes are agent-readable, MCP tools table, a "download a screenshot" example, and
the capabilities/version handshake. Update the SPEC implementation map (§14) and the feature
README row if the tool list is mirrored there. Correct the membership-scoping claim or the
gate (Q1).

### R22 — Acceptance

The amendment is accepted when, against the deployed API with a personal key:

```bash
BASE=$(grep '^BASE_URL=' ~/.tools-project-key | cut -d= -f2-)
KEY=$(grep -v '^BASE_URL=' ~/.tools-project-key | head -n1)

# 1. detail by ref
curl -s "$BASE/v1/agent/tickets/PZT-T-1" -H "X-Api-Key: $KEY" \
  | jq '.data.ticket | {ref, counts, attachments, activities_page}'

# 2. the three PZT screenshots stream as images
for id in 54830228-0c70-4c62-8149-bf967f47af86 \
          8b3cd170-7b4b-4170-a889-53e1dd22798a \
          841a6851-536d-4d48-ab75-8fb8becc302d; do
  curl -s -o "/tmp/$id" -w "%{http_code} %{content_type} %{size_download}\n" \
    "$BASE/v1/agent/attachments/$id" -H "X-Api-Key: $KEY"
  file "/tmp/$id"          # PNG image data, …
done

# 3. MCP returns an image block for 54830228-…
python3 .opencode/mcp/project-mcp/mcp_server.py --self-check
```

Plus: every test in §11 green; `ruff`/type checks unchanged; no new tables; remote deployed
and the three screenshots confirmed by an agent.

---

## 5. Data model

No new tables. Existing rows used:

| Table | Columns | Use |
|-------|---------|-----|
| `tickets` | all | detail (reporter_id, requester_email, queue_slug, first_response_at, resolved_at, closed_at are currently missing from the agent payload) |
| `activities` | all | feed, internal notes, meta_json |
| `attachments` | all | metadata + bytes (never `storage_key`) |
| `commit_subject_refs` + `github_commits` | all | per-ticket linked commits |
| `watchers` | user_id, subject_type, subject_id | watcher list |
| `users` | id, display_name, email | actor/reporter/assignee |
| `project_members` | role | staff vs client participant (via `resolve_project_access`) |

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
| GET | `/v1/agent/client/mcp_server.py` | agent auth | Canonical MCP server file (R10) |

### Changed endpoints

| Method | Path | Change |
|--------|------|--------|
| GET | `/v1/agent/projects/{project_id}/context` | real counts + truncation flags (R11) |
| GET | `/v1/agent/tickets` | optional `project_id` filter (R12) |

### Reused internals (do not duplicate logic)

- `api/app/routers/attachments.py::download_attachment` — extract the storage lookup +
  headers into a helper both the JWT route and the agent route call.
- `api/app/routers/activities.py` — reuse the visibility/filter rules rather than a second
  copy; factor the filter builder into `app/services/activity_query.py` if needed.
- `api/app/services/project_access.py` — `require_project_access`, `is_client_participant`,
  `can_comment_on_project` (staff detection = `client_access is None`).

---

## 7. Invariants

- **I1** Read-only: no mutation endpoint, no activity row, no attachment change.
- **I2** No `storage_key`, disk path, or absolute filesystem path in any JSON.
- **I3** Attachments are served only after an access check on their own project; failures are
  404, never 403-with-details.
- **I4** Internal notes and their attachments never reach a client participant.
- **I5** Tenant boundary is the same as the rest of `/v1/agent/*`; cross-tenant = 404.
- **I6** `description_markdown` is returned byte-identical; resolved text is additive.
- **I7** Attachment bytes are served with the stored mime **and** an allowlist re-check.
- **I8** Existing five endpoints and their fields are unchanged.
- **I9** The MCP server degrades (hides tools) when the API is older; it never crashes.
- **I10** Every new route is covered by an auth-matrix test (401/403/404/200).

---

## 8. Error model

| Condition | HTTP | Body |
|-----------|------|------|
| No credentials / bad key | 401 | `{"detail": "Not authenticated"}` |
| Bearer user not superuser (agent gate) | 403 | `{"detail": "Agent endpoints require superuser privileges"}` |
| Client participant requests `visibility=internal` | 403 | `{"detail": "Client participants cannot view internal activities"}` |
| Unknown ticket (uuid or ref) | 404 | `{"ok": false, "error": "ticket_not_found"}` |
| Ticket in another project/tenant, or caller has no access | 404 | `{"ok": false, "error": "ticket_not_found"}` |
| Unknown attachment / missing file / bad storage key | 404 | `{"ok": false, "error": "attachment_not_found"}` |
| Attachment of an internal activity, client participant | 404 | `{"ok": false, "error": "attachment_not_found"}` |
| Stored mime not in `ALLOWED_MIMES` | 404 | `{"ok": false, "error": "attachment_not_found"}` |
| `limit`/`offset`/`kind` invalid | 422 | FastAPI validation error |
| API older than the MCP server expects | n/a | `/capabilities` returns the old version; client hides tools |

Existing endpoints keep the `{ "ok": true, "data": … }` envelope; the new ones do too.

---

## 9. Observability

- The three log lines in R19, at `INFO` for success and `WARNING` for `denied`.
- Optional counters if `/metrics` exists in the deployment; otherwise a documented grep.
- Request id propagation already exists (`request_id_middleware` in `app/main.py`).
- No filenames, emails, or bodies in logs.

---

## 10. Security and privacy

- Attachment downloads are audited by log line (R19); the personal key owner is the actor.
- The API key remains read-only: no possibility to upload, comment, or transition.
- Internal notes are a hard boundary: filter on the activity's `is_internal` at both the
  metadata and the binary endpoint (defence in depth — do not rely on the list filter).
- `Content-Disposition` filename sanitisation: strip CR/LF/quotes, cap 200 chars; the stored
  name is already sanitised at upload (`_safe_filename`) but re-sanitise for the header.
- `nosniff` + `CSP: sandbox` on bytes; SVG is not uploadable (`ALLOWED_MIMES`), so the
  classic image-based XSS vector is closed.
- The `storage_key` never leaves the server; `path_for_key` rejects traversal.
- Personal keys are tenant-scoped and hashed (SHA-256) already; no new secret is introduced.
- If R10's code-serving endpoint is rejected, no auth change is needed — the file is copied
  from the repo.

---

## 11. Test plan

New `api/tests/test_agent_ticket_context.py` (the repo's pytest suite is thin — this is the
first agent-route test file; use the existing fixtures/factories in `api/tests/conftest.py`
and `api/tests/factories.py`):

| # | Test | Asserts |
|---|------|---------|
| 1 | `test_detail_by_uuid_and_ref` | same payload for UUID and `PZT-T-1` |
| 2 | `test_detail_unknown_ticket_is_404` | 404, no leak |
| 3 | `test_detail_other_tenant_is_404` | tenant boundary |
| 4 | `test_detail_requires_auth` | 401 without key |
| 5 | `test_detail_includes_attachments_and_resolved_markdown` | `download_url` substituted, `markdown_ref` set |
| 6 | `test_detail_unknown_attachment_ref_left_untouched` | no 500, markdown intact |
| 7 | `test_detail_includes_activities_and_commits` | counts + page + linked commits |
| 8 | `test_activities_pagination_and_order` | `limit/offset/order`, `has_more`, `next_offset` |
| 9 | `test_activities_internal_hidden_from_client_participant` | `is_internal` absent; `visibility=internal` → 403 |
| 10 | `test_attachment_download_streams_bytes` | 200, `Content-Type`, `Content-Length`, bytes md5 equal |
| 11 | `test_attachment_download_unknown_is_404` | 404 |
| 12 | `test_attachment_download_internal_note_hidden_from_client` | 404 |
| 13 | `test_attachment_download_bad_storage_key_is_404` | traversal rejected |
| 14 | `test_attachment_download_disposition` | `?download=1` → `attachment` |
| 15 | `test_capabilities_lists_new_features` | version + capabilities |
| 16 | `test_context_counts_are_real` | 1/4/3, no zeroed defaults |
| 17 | `test_ticket_list_filters_by_project` | `project_id` filter |
| 18 | `test_mcp_get_attachment_returns_image_block` | unit-test the handler with a fake bytes payload |
| 19 | `test_mcp_tools_degrade_on_old_api` | capability check hides tools |
| 20 | `test_mcp_server_file_matches_repo` | served file bytes == repo file bytes |

Manual (deployment gate): the four commands in R22 against the remote, plus the three PZT
screenshots confirmed by `file`.

---

## 12. Rollout and rollback

Additive, no feature flag.

**P0 — unblock the screenshots (smallest diff, ship first):**
1. `api/app/routers/attachments.py`: extract the download body into
   `_serve_attachment(db, user, attachment_id, disposition)`; add an agent router
   (`/v1/agent/attachments/{attachment_id}`) using `require_agent_or_user` that calls it.
2. `api/app/routers/agent_query.py`: add `GET /v1/agent/tickets/{ticket}` returning the
   ticket + attachments + counts (activities `include_activities=false` default for P0).
3. MCP: add `get_attachment` and `get_ticket_detail` (activities empty).
4. Test #1–#7, #10–#14.
5. Deploy; refresh the MCP copy in Pizote; verify the three screenshots.

**P1 — full context:** activities endpoint, internal-note rules, detail `include_activities`,
MCP `list_ticket_activities`, tests #8, #9, #15, #18.
**P2 — hardening and distribution:** capabilities handshake, R10 serving endpoint,
context counts fix, `project_id` filter, index (R20), docs (R21), tests #16, #17, #19, #20.

**Deploy steps (remote):** rebuild/restart the API container; the startup DDL applies the
index idempotently; no data migration; version stays `0.1.x` while `agent_api_version` becomes
`1.1.0`. Verify `/v1/agent/capabilities` and the R22 commands.

**Rollback:** remove the new routes (they are additive); the served MCP file endpoint can be
disabled independently. No schema rollback needed (one index; harmless if left).

---

## 13. Open questions

| # | Question | Recommendation |
|---|----------|----------------|
| Q1 | Should the agent-superuser gate be relaxed so a personal key only needs project membership (as the docs already claim)? | **Keep** the gate for 1.1.0 and fix the docs; plan membership-scoped keys for 1.2.0. The new routes already perform the project check, so the relaxation later is a one-line change plus tests. |
| Q2 | Signed, expiring attachment URLs instead of key-authenticated bytes? | **No.** The key is read-only and revocable; signed URLs add a second secret surface and leak into logs/links. Keep key-auth + audit. |
| Q3 | Serve the MCP server from the API (R10) or keep copy-from-repo? | Serve it — consuming repos already copy the file and drift (Pizote's copy differs from the source by a `User-Agent` line). The served file is version-pinned to the deployed API. |
| Q4 | Inline image cap for MCP `image` blocks? | **5 MiB** default, env-tunable; above it save + return the path. |
| Q5 | Include `requester_email` and reporter emails? | Yes for staff callers (already in `members[]`); no for client participants. |
| Q6 | Attachment retention (`ATTACHMENT_RETENTION_DAYS`) vs ticket evidence? | **Raise to 0 (never) for ticket-scoped attachments** or set a retention longer than any ticket's life. A purged screenshot silently breaks the report — this is the exact failure this amendment exists to fix. |

---

## 14. Implementation map

| Layer | Path | Change |
|-------|------|--------|
| Agent router | `api/app/routers/agent_query.py` | new routes + counts fix + `project_id` filter |
| Attachments | `api/app/routers/attachments.py` | extract `_serve_attachment`; add agent router using `require_agent_or_user` |
| Activities | `api/app/routers/activities.py` | factor the filter/visibility builder (or reuse) |
| Schemas | `api/app/schemas.py` | `AgentTicketDetailOut`, `AgentAttachmentOut`, `AgentActivityOut`, `CapabilitiesOut` |
| Config | `api/app/config.py` | `public_api_base_url`, `public_web_base_url`, `inline_image_max_bytes` |
| DDL | `sql/schema_indexes.sql` | R20 index |
| Router registration | `api/app/main.py` | register the new agent attachment router |
| MCP server | `.opencode/mcp/project-mcp/mcp_server.py` | 3 tools, `SERVER_VERSION`, `--self-check` |
| Docs | `.work/docs/agent-query-api.md` | endpoints, tools, examples |
| Copies in consumers | `<repo>/.opencode/mcp/project-mcp/mcp_server.py` | refreshed via R10 / `project-query-setup update` |
| Tests | `api/tests/test_agent_ticket_context.py` | §11 |

**Effort (estimated):** P0 ≈ 0.5–1 dev-day; P1 ≈ 1 day; P2 ≈ 0.5 day + review.

---

## 15. Concept / NFR registry

| Concept id | Applies | Notes |
|------------|---------|-------|
| MOD-01 | no | No new bounded context; existing ticket/activity/attachment modules |
| MOD-02 | no | No AI-assisted PR in this change |
| MOD-03 | no | No cost-sensitive decision |
| MOD-04 | no | No distributed-system concern (one service + one client) |
| MOD-05 | yes | Project evidence contains customer PII (screenshots, emails) — access is audited and emails are role-scoped |
| MOD-06 | yes | Agent-facing surface; review the boundary between web session and agent key before implementation |
