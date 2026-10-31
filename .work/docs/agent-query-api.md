# Agent Query API — reference and usage

**Date:** 2026-10-30 · **Contract version:** `1.0.0` live · `1.1.0` implemented in code, pending deployment
**Audience:** operators connecting another repository or agent; authors of agents that consume the API.

This is the **canonical reference** for the agent surface: endpoints, payloads, auth, limits, MCP
tools, and troubleshooting. Setup walkthroughs link here instead of repeating it.

> **Reliability rule.** §1–§4, §6 (five live tools) and §8 were verified against the deployed API
> (`0.1.3`, OpenAPI `info.version`) on **2026-10-30**. Sections marked **1.1.0** are implemented in
> the repository (SPEC amendment 01 P0, gates green) but the hosted deployment still runs `0.1.3`
> until it is deployed — those routes return `404` there today.

---

## 0. Doc map

| Document | Owns | Use it for |
|----------|------|------------|
| **This file** | Endpoint/tool contract, auth, limits, troubleshooting | What the API returns today; what 1.1.0 will return |
| [`tutorials/LLM-2-API_SETUP.md`](tutorials/LLM-2-API_SETUP.md) | Click-by-click first connection | Creating a key, writing the key file, registering the MCP server |
| [`guides/quick-reference-to-connect-agent-with-tools-project.md`](guides/quick-reference-to-connect-agent-with-tools-project.md) | Which integration path to choose | Agent query (Case A) vs app-to-app (Case B) |
| [`tutorials/AGENT_TICKET_CONTEXT.md`](tutorials/AGENT_TICKET_CONTEXT.md) | Task tutorial: ticket + comments + screenshots | A concrete incident-resolution workflow (**requires 1.1.0**) |
| [`tutorials/REPO_INTEGRATION.md`](tutorials/REPO_INTEGRATION.md) | GitHub linking + plan sync | Commit linking, task registry, `@plan-sync` |
| [`reference/APP_INTEGRATION.md`](reference/APP_INTEGRATION.md) | App-to-app surface (identity, webhooks, external refs, inbound) | When the consumer is an application, not an agent |
| [`reference/API.md`](reference/API.md) | Curated REST map for the deployed build | Everything else |
| `.work/features/agent-query-api/20261030-SPEC-amendment-01.md` | The 1.1.0 contract (Approved 2026-10-30) | R1–R22, tests, rollout |
| `.work/features/agent-query-api/20261030-SPEC-amendment-02.md` | Web-URL addressing + activity pagination (Draft, owner-directed) | R23–R25 — resolve route, MCP `url`/activities |
| `.work/features/agent-query-api/20261030-amendment-01-verification.md` | Evidence behind the amendment | Live probes, findings, owner decisions |

---

## 1. What you get

| Capability | `1.0.0` (live) | `1.1.0` (implemented, pending deploy) |
|------------|----------------|-------------------|
| Projects, tasks, tickets (lists), search | yes | unchanged |
| Project context (members, tickets, GitHub refs) | yes, **summary counts returned 0** (fixed in this build) | real counts + totals/truncation flags |
| Ticket detail by UUID, `ref` or web URL | no | `GET /v1/agent/tickets/{ticket}` · `GET /v1/agent/tickets/resolve?url=` |
| Comment/activity thread | no (JWT-only web route) | `GET /v1/agent/tickets/{ticket}/activities` (paginated) + inline newest-first page |
| Attachment metadata (filename, mime, size) | no | in ticket detail |
| Attachment bytes (screenshots) viewable with an API key | no (`401`) | `GET /v1/agent/attachments/{id}` |
| Resolved description (working image links) | no | `description_resolved` |
| Capability/version handshake | no | `GET /v1/agent/capabilities` |
| MCP tools | 5 | 8 |

The rest of this document labels planned behaviour explicitly.

---

## 2. Connect (summary)

Full walkthrough: [`tutorials/LLM-2-API_SETUP.md`](tutorials/LLM-2-API_SETUP.md).

```bash
# 1. Key: web UI → Settings → API Keys → + New key (starts with tools_project_)
# 2. Key file (one per machine, chmod 600):
printf 'BASE_URL=https://project.cloudsys.win\ntools_project_<key>\n' > ~/.tools-project-key
chmod 600 ~/.tools-project-key

# 3. Verify (BASE defaults to the local API when the key file has no BASE_URL line)
BASE=$(grep '^BASE_URL=' ~/.tools-project-key | cut -d= -f2-); BASE=${BASE:-http://localhost:8300}
KEY=$(grep -v '^BASE_URL=' ~/.tools-project-key | head -n1)
curl -s -H "X-Api-Key: $KEY" -H "User-Agent: tools-project-mcp/1.1.0" \
  "$BASE/v1/agent/projects" | head -c 200
```

Requirements and precedence:

| Item | Rule |
|------|------|
| Python | **3.10+** for the MCP server (`dict[str, Any] \| None` annotations) |
| Key sources (first match) | `TOOLS_PROJECT_API_KEY` env → `~/.tools-project-key` → `AGENT_API_KEY` env (legacy) |
| Base URL (first match) | `API_BASE_URL` env → `BASE_URL=` line in the key file → `http://localhost:8300` |
| Hosted deployment | send a non-default `User-Agent`; Cloudflare answers urllib's default with **403 Error 1010** |
| Agent config | the server reads the key file itself — no key in `opencode.json`/`.cursor/mcp.json` |

Register only the command (opencode example):

```json
{
  "mcp": {
    "tools-project": {
      "type": "local",
      "command": ["python3", ".opencode/mcp/project-mcp/mcp_server.py"],
      "enabled": true
    }
  }
}
```

Cursor (`.cursor/mcp.json`) and Claude Code (`.claude/mcp.json`) use
`{"mcpServers": {"tools-project": {"command": "python3", "args": [".opencode/mcp/project-mcp/mcp_server.py"]}}}`.
Do **not** pin `API_BASE_URL` in a repo config unless the whole team wants that instance — it
overrides the key file.

---

## 3. Authentication and authorization

All `/v1/agent/*` endpoints accept three credentials (`require_agent_or_user`):

| Credential | Resolves to | Requirement |
|------------|-------------|-------------|
| `X-Api-Key: tools_project_…` (personal) | The key's owner | Owner must be a **superuser**; otherwise `403` |
| `X-Api-Key: <AGENT_API_KEY>` (server-wide) | Synthetic agent superuser | Only when `MULTI_TENANCY_ENABLED=false`; `401` in multi-tenant mode |
| `Authorization: Bearer <JWT>` | The logged-in user | User must be a superuser; otherwise `403` |

**Project scoping — read this carefully.** The agent routes call `_require_agent_superuser`; a
superuser resolves as `owner` on **every** project. Personal keys are therefore *not* limited to the
owner's project memberships, contrary to what earlier revisions of this document claimed. The
project/tenant checks added in 1.1.0 are defence for the planned membership-scoped keys (SPEC Q1),
not a restriction on today's superuser callers.

- Keys are stored as SHA-256 hashes; the plaintext is shown once. Revoke from **Settings → API
  Keys**; `last_used_at` updates on each authenticated call.
- Multi-tenant mode: a personal key is tenant-scoped; `X-Tenant-Slug` is honoured and a foreign
  tenant is rejected. The shared `AGENT_API_KEY` is disabled.
- Every endpoint is read-only. The only write on these paths is `last_used_at`.

---

## 4. Endpoints — `1.0.0` (live, verified 2026-10-30)

All responses use `{ "ok": true, "data": … }`. Errors use FastAPI's `{ "detail": … }`.

### `GET /v1/agent/projects`

All projects with summary counts.

```json
{"ok": true, "data": [{"id": "uuid", "name": "Pizote", "slug": "pizote", "status": "active",
  "project_key": "PZT", "open_tasks": 1, "open_tickets": 4, "member_count": 3,
  "github_task_registry_enabled": true, "auto_prefix_enabled": true,
  "created_at": "…", "updated_at": "…"}]}
```

### `GET /v1/agent/projects/{project_id}/context`

Project + up to 100 tasks, 100 tickets, members, linked clients, GitHub refs.

Counts are real (SPEC R11): `open_tasks`, `open_tickets`, `member_count`, plus `tasks_total`,
`tickets_total` and `tasks_truncated`/`tickets_truncated` when the 100-row lists were clipped.

### `GET /v1/agent/tasks` · `GET /v1/agent/tickets`

Filters `ref`, `status`, `limit` (1–200, default 50). Ticket objects carry
`id, ref, title, description, status, priority, assignee_id, project_id, project_name, created_at,
updated_at` — no attachments, comments or URLs in 1.0.0.

### `GET /v1/agent/search?q=…&limit=…`

Projects, tasks, tickets, clients, prospects. `q` required; `limit` 1–50 (default 20).

---

## 5. Endpoints — `1.1.0` (implemented in the repository; pending deployment)

Full contract and test plan: [`20261030-SPEC-amendment-01.md`](../features/agent-query-api/20261030-SPEC-amendment-01.md).
Detail, paginated activities, binary attachments, capabilities, the served MCP file and the three MCP
tools are implemented and tested (P0–P2). Until a `1.1.0` build is deployed, every route below
returns `404` on the hosted instance.

### `GET /v1/agent/tickets/{ticket}`

`{ticket}` = UUID or `ref` (case-insensitive, trimmed). Returns the ticket, reporter/assignee/
watchers, counts, attachments, the newest-first first activity page, linked commits and `web_url`.

Key fields:

| Field | Notes |
|-------|-------|
| `description` | Byte-identical stored markdown, including `![…](/api/attachments/<uuid>)` |
| `description_resolved` | Same text with every `/api/attachments/<uuid>` replaced by the agent `download_url` |
| `attachments[]` | `id, filename, mime, size_bytes, is_image, scope, activity_id, download_url, markdown_ref` — never `storage_key` |
| `activities[]` | Newest first; `next_offset` pages backwards. Use `…/activities?order=asc` to read chronologically |
| `counts` | Visibility-filtered activity total, true attachment total, linked-commit total |
| `attachments_truncated` | `true` when more than 200 attachments (description-referenced files are never cut) |
| `web_url` | Null unless `PUBLIC_WEB_BASE_URL` is configured (never guessed) |

Knobs: `include_activities` (default `true`), `activity_limit` (1–200, default 50),
`include_internal` (default `true`; forced `false` for client participants). The inline page is the
**most recent** entries, newest first.

### `GET /v1/agent/tickets/resolve?url=<web ticket URL>`

Accepts the link a human pastes — absolute (`https://host/projects/<p>/tickets/<uuid>`) or relative
(`/projects/<p>/tickets/<uuid>`) — and returns the **same payload** as the detail route. The client
does not need to know the UUID; the last path segment (UUID or ref) is resolved server-side.
A URL with no ticket segment → `400 {"detail": "invalid_ticket_url"}`.

### `GET /v1/agent/tickets/{ticket}/activities`

Paginated thread — use it when the inline first page is not enough (the detail page returns the
**most recent** `activity_limit` entries, max 200).

`limit`, `offset`, `order` (`asc`/`desc`, default `desc` = newest first), `kind` (validated against
`ACTIVITY_KINDS`; legacy `note` → `comment`), `include_internal`, `visibility`
(`all`/`internal`/`external`; `internal` is `403` for client participants). Items carry
`actor`, `body`, `is_internal`, `parent_activity_id`, `created_at`, `meta_json` and the activity's
attachments; the response adds `total`, `has_more`, `next_offset` (the next `offset`) and `order`.

### `GET /v1/agent/attachments/{attachment_id}`

Streams the bytes (`FileResponse`, never base64 in JSON). `Content-Type` from the stored mime,
re-validated against `ALLOWED_MIMES` (unknown → 404); `?download=1` switches `Content-Disposition`
from `inline` to `attachment`; `Cache-Control: private, max-age=0, no-store`,
`X-Content-Type-Options: nosniff`, `Content-Security-Policy: sandbox`, `Referrer-Policy:
no-referrer`; no `ETag`. Every failure is `404 {"detail": "attachment_not_found"}`.

### `GET /v1/agent/capabilities`

```json
{"ok": true, "data": {
  "agent_api_version": "1.1.0",
  "capabilities": ["ticket_detail", "ticket_activities", "attachments", "attachment_download",
                   "capabilities", "mcp_server_file"],
  "limits": {"activities_default": 50, "activities_max": 200, "activity_body_max_bytes": 32768,
             "description_max_bytes": 32000, "attachments_per_response": 200,
             "attachment_max_bytes": 26214400},
  "recommended_mcp_server_version": "1.1.0",
  "mcp_server_download_url": "https://…/v1/agent/client/mcp_server.py"}}
```

Version policy: additive → minor; breaking → major. Clients compare `major.minor` and hide tools
they cannot use (`1.0.0` = five tools; `1.1.0` = eight).

### `GET /v1/agent/client/mcp_server.py`

The canonical MCP server file for the deployed API (`text/x-python`), so consuming repositories can
update instead of copying by hand. Same agent auth. Empty/404 if the owner declines the
distribution approach (SPEC D1) — the copy-from-repository path then applies.

---

## 6. MCP server

Source of truth: today `.opencode/mcp/project-mcp/mcp_server.py`; from 1.1.0 the canonical file is
`api/app/client/mcp_server.py` (packaged and served by the endpoint above), and every repository
copy is refreshed from it.

| Tool | Since | Maps to |
|------|-------|---------|
| `list_projects` | 1.0.0 | `GET /v1/agent/projects` |
| `get_project_context` | 1.0.0 | `GET /v1/agent/projects/{id}/context` |
| `get_task_info` | 1.0.0 | `GET /v1/agent/tasks` |
| `get_ticket_info` | 1.0.0 | `GET /v1/agent/tickets` |
| `search_entities` | 1.0.0 | `GET /v1/agent/search` |
| `get_ticket_detail` | **1.1.0 (shipped)** | `GET /v1/agent/tickets/{ticket}` or `/resolve?url=` |
| `list_ticket_activities` | **1.1.0 (shipped)** | `GET /v1/agent/tickets/{ticket}/activities` |
| `get_attachment` | **1.1.0 (shipped)** | `GET /v1/agent/attachments/{id}` — returns an MCP `image` block for images ≤ 5 MiB, a `text` block for text ≤ 1 MiB, otherwise saves the file and returns its path + sha256 |

Behaviour:

- Sends `User-Agent: tools-project-mcp/<version>` (override `MCP_USER_AGENT`). **Required** behind
  Cloudflare: urllib's default UA returns `403 Error 1010` while the MCP handshake still looks
  healthy.
- `initialize` never touches the network; the capability probe is lazy (5 s, cached). If the probe
  reports an older API, newer tools are hidden instead of failing.
- Every tool returns `{"ok": false, "error": …}` **as text** on failure — the transport never
  crashes and the key is never printed.
- `--version` prints the server version; `--self-check` prints the effective base URL and its
  source, calls `/v1/agent/capabilities`, and lists enabled tools.

Update a consumer copy (1.1.0+ — the file is served by the deployment and includes the
Cloudflare-safe `User-Agent`):

```bash
curl -s -o .opencode/mcp/project-mcp/mcp_server.py \
  -H "X-Api-Key: $(grep -v '^BASE_URL=' ~/.tools-project-key | head -n1)" \
  -H "User-Agent: tools-project-mcp/1.1.0" \
  "$(grep '^BASE_URL=' ~/.tools-project-key | cut -d= -f2-)/v1/agent/client/mcp_server.py"
chmod 755 .opencode/mcp/project-mcp/mcp_server.py
python3 .opencode/mcp/project-mcp/mcp_server.py --self-check
```

Inside this repository, `bin/mcp-sync.sh check` fails when the `.opencode` copy drifts from the
packaged `api/app/client/mcp_server.py`; `bin/mcp-sync.sh sync` refreshes it.

On `tools/list` the server probes `/v1/agent/capabilities` once (cached, never blocks
`initialize`): an older `agent_api_version` hides the 1.1.0 tools; a missing endpoint or a network
error keeps all tools enabled. `--self-check` prints the effective base URL, the API version,
declared capabilities and the enabled tools.

---

## 7. Recipes

### Resolve a ticket from a pasted URL (live)

A web URL (`https://…/projects/<project>/tickets/<ticket>`) is a browser page — it answers `307 →
/login` for an API key. Extract the last UUID and use `get_ticket_info` / `GET /v1/agent/tickets`
until 1.1.0, then `GET /v1/agent/tickets/<ticket-uuid>`. The API returns `web_url` in 1.1.0 so the
link can be reconstructed.

### Read a comment thread (1.1.0)

```bash
BASE=$(grep '^BASE_URL=' ~/.tools-project-key | cut -d= -f2-); BASE=${BASE:-http://localhost:8300}; KEY=$(tail -n1 ~/.tools-project-key)
curl -s -H "X-Api-Key: $KEY" -H "User-Agent: tools-project-mcp/1.1.0" \
  "$BASE/v1/agent/tickets/PZT-T-2/activities?order=asc&limit=200" \
  | python3 -c 'import json,sys; [print(i["created_at"], i["actor"]["display_name"], "::", i["body"][:120]) for i in json.load(sys.stdin)["data"]["items"]]'
```

### View a screenshot (1.1.0)

Use `download_url` from `attachments[]` with the same headers; the MCP tool returns an `image`
block directly:

```bash
curl -s -o /tmp/pzt-t-1.png -H "X-Api-Key: $KEY" -H "User-Agent: tools-project-mcp/1.1.0" \
  "$BASE/v1/agent/attachments/54830228-0c70-4c62-8149-bf967f47af86"
file /tmp/pzt-t-1.png   # PNG image data
```

### Build a commit message with the ticket ref (live)

`get_ticket_info(ref="PZT-T-2")` → ref, title, status. Use `PZT-T-2: <plain-language subject>`.
Commit refs sync back and link to the ticket (see `REPO_INTEGRATION.md`).

### Reconcile local HANDOFF/NEXT with the system (live)

`get_task_info(status="todo", limit=200)` and compare with `NEXT.md`.

---

## 8. Troubleshooting

### What an error looks like

| Status | Body | Meaning |
|--------|------|---------|
| 401 | `{"detail": "Not authenticated"}` | Missing, wrong or revoked key / token |
| 403 | `{"detail": "Agent endpoints require superuser privileges"}` | The key owner (or JWT user) is not a superuser |
| 400 | `{"detail": "invalid_ticket_url"}` | `/resolve` got a URL with no ticket segment |
| 404 | `{"detail": "ticket_not_found"}` · `{"detail": "attachment_not_found"}` | New 1.1.0 routes use **stable codes**; legacy agent routes still use prose (`"Project not found"`) |
| 422 | `{"detail": [{"loc": […], "msg": …, "type": …}]}` | Validation — display `msg` per field, do not retry unchanged |
| 5xx | plain text (`Internal Server Error`) or `{"detail": …}` | Server/edge failure — retry with backoff, quote the request id |
| 403 + HTML | Cloudflare page (`Error 1010`) | The request had urllib's default `User-Agent`; send `tools-project-mcp/<version>` |

### Request id (use it when reporting)

Every response — including errors — carries **`X-Request-Id`**. Log it with the status and the
endpoint, and quote it when reporting a problem; the server's access log records the same id.

### MCP errors

Tools never crash the transport. On failure the tool returns a JSON text block:

```json
{"ok": false, "status": 401, "error": "HTTP 401: Not authenticated",
 "request_id": "62f7…", "hint": "check TOOLS_PROJECT_API_KEY or ~/.tools-project-key (the key may be revoked)"}
```

`status` and `request_id` are absent for connection failures; `hint` explains the usual cause
(superuser gate, Cloudflare, missing route on an old deployment). `get_attachment` returns the same
shape when the download fails.

### Retry guidance

| Result | Action |
|--------|--------|
| 401 / 403 | Do **not** retry — fix the key, the owner's superuser flag, or the User-Agent |
| 404 | Do **not** retry blindly — verify the ref/UUID and the deployment version (`/openapi.json`) |
| 422 | Fix the payload; surface `detail[].msg` |
| 429 / 5xx / network error | Retry with exponential backoff and jitter; stop after a few attempts and report with `X-Request-Id` |

**Never** log the API key; a truncated key prefix (`tools_pr…`) is enough to identify the credential.


| Symptom | Cause | Fix |
|---------|-------|-----|
| `401` | Missing, wrong or revoked key; shared key in multi-tenant mode | Recreate the key; use a personal key |
| `401` on `/v1/attachments/{id}` or `/api/attachments/{id}` | Those routes are JWT/web-session only in 1.0.0 | Expected until 1.1.0 (`/v1/agent/attachments/…`) |
| `403 {"detail":"Agent endpoints require superuser privileges"}` | Key owner / JWT user is not a superuser | Ask an admin to grant superuser |
| `403` with an **HTML** Cloudflare page / `Error 1010` | Default urllib User-Agent | Send `User-Agent: tools-project-mcp/<version>` |
| `404 {"detail":"Not Found"}` on `/v1/agent/tickets/…` or `/v1/agent/capabilities` | The deployment predates 1.1.0 | Check `/openapi.json` `info.version`; deploy |
| MCP handshake works but every tool call fails | Stale copy without the UA header, or wrong `API_BASE_URL` | Run `--self-check`; refresh the copy |
| `python: command not found` | Some configs use `python` | Use `python3` (3.10+) |
| Tools missing | Agent config not reloaded, or a 1.0.0 API hides 1.1.0 tools | Restart the agent; check `recommended_mcp_server_version` |
| Key file ignored | `TOOLS_PROJECT_API_KEY`/`API_BASE_URL` env overrides the file | Check the precedence table in §2 |

---

## 9. Operations

- **Logs** (1.1.0): `agent.ticket_detail`, `agent.ticket_activities`, `agent.attachment_read`, with
  ids and result codes only — no bodies, filenames or emails. No Prometheus exporter exists; use
  `grep -c 'agent.attachment_read .* result=ok'`.
- **Retention:** `ATTACHMENT_RETENTION_DAYS=0` (never purge). A purged screenshot silently breaks
  a report — keep it at 0 for deployments used as evidence systems.
- **Quota:** `ATTACHMENT_MAX_PER_PROJECT` (default 500), `ATTACHMENT_MAX_BYTES_PER_PROJECT`
  (default 0 = off).
- **Storage:** `ATTACHMENTS_DIR` (default `/data/attachments`); `storage_key` never leaves the API.

---

## 10. Reference

| File | Purpose |
|------|---------|
| `api/app/routers/agent_query.py` | `/v1/agent/*` routes |
| `api/app/routers/agent_attachments.py` | agent binary download (1.1.0) |
| `api/app/deps.py` | `require_agent_or_user`, `_require_agent_superuser` |
| `api/app/services/project_access.py` | project access, client participant helpers |
| `api/app/services/activity_visibility.py` | client visibility predicate |
| `api/app/config.py` | `agent_api_key`, `public_*_base_url` (1.1.0) |
| `api/app/client/mcp_server.py` | canonical MCP server (1.1.0) |
| `.opencode/mcp/project-mcp/mcp_server.py` | MCP copy used by this repository |
| `opencode.json` | MCP registration + `agent-api` reference |

| Env var | Default | Used by |
|---------|---------|---------|
| `AGENT_API_KEY` | empty | API — shared agent key (single-tenant only) |
| `TOOLS_PROJECT_API_KEY` | empty | MCP — personal key (overrides the key file) |
| `API_BASE_URL` | from key file, else `http://localhost:8300` | MCP |
| `MCP_USER_AGENT` | `tools-project-mcp/<version>` | MCP |
| `TOOLS_PROJECT_INLINE_IMAGE_MAX_BYTES` | `5242880` | MCP (1.1.0) |
| `TOOLS_PROJECT_INLINE_TEXT_MAX_BYTES` | `1048576` | MCP (1.1.0) |
| `PUBLIC_API_BASE_URL` / `PUBLIC_WEB_BASE_URL` | empty | API (1.1.0) — link generation |
