# Agent Query API

**Date:** 2026-07-01 · **Version:** 1.0.0

Read-only aggregation API + MCP server that lets any coding agent (opencode, Claude Code, Cursor, etc.) query project context — tasks, tickets, clients, prospects, GitHub refs — directly from the tools-project backend.

Designed for **cross-framework integration** by `.ai` (Agent OS), `.ai.ui` (UI Design OS), `.ai.biz` (Business OS), and `.ai.soc` (Social OS) skills, agents, and code-generation loops.

---

## Table of contents

1. [Quick start](#1-quick-start)
2. [Authentication](#2-authentication)
3. [API endpoints](#3-api-endpoints)
4. [MCP server](#4-mcp-server)
5. [Framework integration guide](#5-framework-integration-guide)
6. [Usage examples](#6-usage-examples)
7. [Agent workflow patterns](#7-agent-workflow-patterns)
8. [Reference](#8-reference)

---

## 1. Quick start

### Get your personal API key

1. Open the web UI: `http://localhost:18513/settings/api-keys` (local) or `https://project.cloudsys.win/settings/api-keys` (remote)
2. Click **+ New key**, optionally add a label, and click **Create**
3. Copy the generated key (it starts with `tools_project_`) — shown only once

### Configure your key

Pick one method:

**Option A: Permanent file (recommended)**

```bash
echo "tools_project_<your-key>" > ~/.tools-project-key
chmod 600 ~/.tools-project-key
```

For remote deployments, add the base URL as the first line:

```bash
echo "BASE_URL=https://project.cloudsys.win" > ~/.tools-project-key
echo "tools_project_<your-key>" >> ~/.tools-project-key
chmod 600 ~/.tools-project-key
```

**Option B: Environment variable**

```bash
export TOOLS_PROJECT_API_KEY=tools_project_<your-key>
export API_BASE_URL=https://project.cloudsys.win   # only for remote
```

The MCP server resolves auth in this order:
1. `TOOLS_PROJECT_API_KEY` env var
2. `~/.tools-project-key` file (one key per line, optional `BASE_URL=<url>` as first line)
3. `AGENT_API_KEY` env var (legacy shared key)

### Verify

```bash
curl -s -H "X-Api-Key: $TOOLS_PROJECT_API_KEY" \
  http://localhost:8300/v1/agent/projects | python3 -m json.tool
# { "ok": true, "data": [ ... ] }
```

The stack must be running locally (`docker compose --profile dev up --build`) for local verification.

---

## 2. Authentication

All `/v1/agent/` endpoints accept **two** auth methods:

### Method A: Personal API key (primary)

Generated from the web UI under **Settings → API Keys**. Passed via the `X-Api-Key` header.

```http
GET /v1/agent/projects
X-Api-Key: tools_project_<random>
```

Each developer has their own key. Keys are hashed with SHA-256 at rest — the plaintext is only shown once on creation. The auth resolves the real user from the stored hash, so permissions are scoped to your project memberships (just like the web UI).

### Method B: Server-wide agent API key (local convenience)

A shared secret configured by the server admin via `AGENT_API_KEY` in `.env`. When matched, the request runs as an agent superuser with full read access.

```http
GET /v1/agent/projects
X-Api-Key: <server-shared-secret>
```

This is useful for local development or single-user deployments. Not recommended for multi-user production.

### Auth resolution order

1. `X-Api-Key` matches `AGENT_API_KEY` in Settings → agent superuser (full read access)
2. `X-Api-Key` matches a `user_api_keys` row (SHA-256) → authenticated as that user (scoped to project memberships)
3. Bearer JWT present → normal user session (requires superuser for agent endpoints)
4. None → `401 Unauthorized`

---

## 3. API endpoints

All responses use the envelope `{ "ok": true, "data": <result> }`.

### `GET /v1/agent/projects`

List all projects with summary stats.

**Response shape:**

```json
{
  "ok": true,
  "data": [
    {
      "id": "uuid",
      "name": "Project Name",
      "slug": "project-name",
      "description": "...",
      "status": "active",
      "project_key": "PRJ",
      "open_tasks": 12,
      "open_tickets": 3,
      "member_count": 5,
      "github_task_registry_enabled": true,
      "auto_prefix_enabled": true,
      "created_at": "2026-06-18T...",
      "updated_at": "2026-06-30T..."
    }
  ]
}
```

### `GET /v1/agent/projects/{project_id}/context`

Full project context in a single response.

**Response shape:**

```json
{
  "ok": true,
  "data": {
    "project": { "id": "...", "name": "...", "slug": "...", "description": "...", "status": "...", "project_key": "...", "github_task_registry_enabled": true, "auto_prefix_enabled": false, "created_at": "...", "updated_at": "..." },
    "members": [ { "id": "uuid", "email": "user@example.com", "display_name": "Alice", "role": "owner" } ],
    "tasks": [ { "id": "uuid", "ref": "PRJ-1", "title": "...", "description": "...", "status": "todo", "priority": "normal", "assignee_id": null, "due_at": null, "is_todo": false, "project_id": "uuid", "project_name": "...", "created_at": "..." } ],
    "tickets": [ { "id": "uuid", "ref": "PRJ-T-1", "title": "...", "description": "...", "status": "open", "priority": "normal", "assignee_id": null, "project_id": "uuid", "project_name": "...", "created_at": "..." } ],
    "clients": [ { "id": "uuid", "prospect_id": null, "name": "Client Inc", "slug": "client-inc", "industry": null, "notes": null, "created_by": "uuid", "created_at": "...", "updated_at": "..." } ],
    "github_refs": [ { "id": "uuid", "github_commit_id": "uuid", "sha": "abc123...", "project_id": "uuid", "subject_type": "ticket", "subject_id": "uuid", "subject_ref": "TPR-T-12", "subject_title": "...", "subject_status": "closed", "subject_priority": null, "subject_description": "...", "created_by": "uuid", "created_at": "...", "commit": { "sha": "...", "short_sha": "abc123f", "message_preview": "Fix login bug...", "html_url": "https://github.com/...", "author_name": "Dev", "committed_at": "...", "owner": "org", "repo": "repo" } } ]
  }
}
```

### `GET /v1/agent/tasks`

List tasks with optional filters.

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `ref` | string | Filter by exact task ref (e.g. `TPR-3`) |
| `status` | string | Filter by status (`todo`, `in_progress`, `done`, etc.) |
| `limit` | integer | Max results (default 50, max 200) |

**Examples:**

```
GET /v1/agent/tasks?ref=TPR-3
GET /v1/agent/tasks?status=todo&limit=100
```

### `GET /v1/agent/tickets`

List tickets with optional filters.

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `ref` | string | Filter by exact ticket ref (e.g. `TPR-T-12`) |
| `status` | string | Filter by status (`open`, `closed`, `in_progress`, etc.) |
| `limit` | integer | Max results (default 50, max 200) |

**Examples:**

```
GET /v1/agent/tickets?ref=TPR-T-12
GET /v1/agent/tickets?status=open&limit=10
```

### `GET /v1/agent/search`

Unified search across projects, tasks, tickets, clients, and prospects.

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | **Required.** Search term |
| `limit` | integer | Max results (default 20, max 50) |

**Response shape:**

```json
{
  "ok": true,
  "data": [
    { "kind": "task", "id": "uuid", "label": "Fix login bug", "subtitle": "[TPR-3] My Project", "ref": "TPR-3", "status": "todo" },
    { "kind": "project", "id": "uuid", "label": "My Project", "subtitle": "Project — my-project", "ref": null, "status": "active" },
    { "kind": "client", "id": "uuid", "label": "Client Inc", "subtitle": "Client — client-inc", "ref": null, "status": null }
  ]
}
```

---

## 4. MCP server

An MCP (Model Context Protocol) server at `.opencode/mcp/project-mcp/mcp_server.py` wraps the above endpoints as callable tools. This is the **recommended** way for coding agents to consume the API.

### Registered tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_projects` | List all projects with summary stats | *(none)* |
| `get_project_context` | Full project details + tasks + tickets + members + clients + GitHub refs | `project_id` (UUID, required) |
| `get_task_info` | List tasks, optionally by ref/status | `ref`, `status`, `limit` (all optional) |
| `get_ticket_info` | List tickets, optionally by ref/status | `ref`, `status`, `limit` (all optional) |
| `search_entities` | Unified search across all entity types | `q` (required), `limit` (optional) |

### Registration

The MCP server is registered in `opencode.json`:

```json
{
  "mcp": {
    "tools-project": {
      "type": "local",
      "command": ["python3", ".opencode/mcp/project-mcp/mcp_server.py"],
      "enabled": true,
      "env": {
        "AGENT_API_KEY": "{env:AGENT_API_KEY}",
        "API_BASE_URL": "http://localhost:8300"
      }
    }
  }
}
```

The MCP server reads `AGENT_API_KEY` from its environment. opencode passes it from the host environment via `{env:AGENT_API_KEY}`. Set it before starting opencode:

```bash
export AGENT_API_KEY="$(grep AGENT_API_KEY .env | cut -d= -f2)"
```

Or include it in your shell profile.

---

## 5. Framework integration guide

### For .ai (Agent OS) skills

A skill can declare the MCP tools as prerequisites or use `webfetch` to call the API directly via a reference.

**Option A: Use MCP tools (preferred)**

In `skill.md` preamble:

```markdown
**Prerequisites:** tools-project MCP server registered (provides `get_project_context`, `get_task_info`, `get_ticket_info`, `search_entities`, `list_projects` tools)
```

Then in the skill body, invoke tools directly:

> Use `get_project_context` with the project UUID to understand what tasks and tickets are open. Then use `get_ticket_info` with the relevant ref for commit message context.

**Option B: Use direct API calls via reference**

Register the API doc as a reference in `opencode.json`:

```json
{
  "references": {
    "agent-api": {
      "path": ".work/docs/agent-query-api.md",
      "description": "Read-only API: query project/task/ticket/client context"
    }
  }
}
```

Agents can then use `webfetch` with the agent API key:

```markdown
Fetch `http://localhost:8300/v1/agent/tickets?ref=TPR-T-12` with header `X-Api-Key: {env:AGENT_API_KEY}` to get ticket details.
```

### For .ai.ui (UI Design OS) skills

Use `get_project_context` or the `/v1/agent/projects/{id}/context` endpoint to determine what UI screens are needed for a project's current task/ticket state.

**Example workflow:** "Check what tickets are open for a project → identify the most active work areas → fetch project context to understand client/team structure → build appropriate UI components."

### For .ai.biz (Business OS) skills

Use `list_projects` and the `/v1/agent/projects` endpoint to understand the full portfolio. Use `search_entities` to find clients or prospects relevant to business strategy.

**Example workflow:** "List all projects → for each, check task completion and ticket burden → identify clients needing attention → generate business review."

### For .ai.soc (Social OS) skills

Use `get_ticket_info` and `get_task_info` with status filters to identify recently completed work that could be shared as social content or community updates.

---

## 6. Usage examples

### Example 1: Build a commit message with ticket URL

**Goal:** Agent is making a commit that relates to ticket `TPR-T-12`. It wants to include the ticket URL and ref in the commit message.

```python
# Agent calls (via MCP or webfetch):
# GET /v1/agent/tickets?ref=TPR-T-12
# Response:
{
  "ok": true,
  "data": [
    {
      "id": "...",
      "ref": "TPR-T-12",
      "title": "Analyze and implement penetration test report findings",
      "description": "Penetration test report...",
      "status": "open",
      ...
    }
  ]
}

# Agent builds commit message:
# TPR-T-12: resolve 9 penetration test findings (security hardening)
#
# Closes ticket TPR-T-12 — full report at
# https://github.com/org/repo/issues/...
```

### Example 2: Get full project context

**Goal:** Agent needs to understand everything about a project before implementing a new feature.

```bash
curl -s -H "X-Api-Key: $AGENT_API_KEY" \
  http://localhost:8300/v1/agent/projects/<uuid>/context \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(f'Project: {d[\"project\"][\"name\"]}'); print(f'Tasks ({len(d[\"tasks\"])}):'); [print(f'  [{t[\"ref\"]}] {t[\"title\"]} - {t[\"status\"]}') for t in d[\"tasks\"] if t[\"status\"] not in ('done','cancelled')]"
```

### Example 3: Check pending tasks vs local context

**Goal:** Agent wants to verify that its local HANDOFF/NEXT context matches the live system state.

```bash
# Get all open tasks
curl -s -H "X-Api-Key: $AGENT_API_KEY" \
  "http://localhost:8300/v1/agent/tasks?status=todo&limit=100" \
  | python3 -c "import sys,json; data=json.load(sys.stdin)['data']; print(f'{len(data)} open tasks:'); [print(f'  [{t[\"ref\"]}] {t[\"title\"]} ({t[\"project_name\"]})') for t in data]"
```

### Example 4: Search across all entities

```bash
curl -s -H "X-Api-Key: $AGENT_API_KEY" \
  "http://localhost:8300/v1/agent/search?q=penetration" \
  | python3 -m json.tool
```

---

## 7. Agent workflow patterns

### Pattern 1: Commit-aware code generation

```
1. Agent receives task: "fix the rate limiter bug"
2. Agent queries get_ticket_info(ref="TPR-T-9") → gets ticket details + linked commits
3. Agent reads html_url from linked commits → understands context
4. Agent implements fix
5. Agent builds commit message with TPR-T-9 ref + GitHub issue URL
```

### Pattern 2: Context-aware project work

```
1. Agent receives task: "add client health dashboard enhancements"
2. Agent queries get_project_context(project_id="...") → full project state
3. Agent sees existing client health router, schemas, UI components
4. Agent sees all open tasks/tickets for the project
5. Agent implements changes with full awareness of existing code and state
```

### Pattern 3: State verification loop

```
1. Agent reads local HANDOFF.md → "implement M3-T2"
2. Agent queries get_task_info(ref="TPR-3") → checks if TPR-3 is done/blocked/pending
3. Agent reconciles local plan with live system state
4. Agent adjusts plan accordingly (skip done items, prioritize blocked ones)
```

### Pattern 4: Cross-framework coordination

```
1. Business OS agent queries list_projects → identifies clients needing attention
2. Passes project UUID to Engineering OS agent
3. Engineering agent calls get_project_context → gets full task/ticket landscape
4. Engineering agent assigns work to UI OS agent
5. UI agent calls get_ticket_info to understand which tickets need UI work
```

---

## 8. Reference

### File layout

| File | Purpose |
|------|---------|
| `api/app/routers/agent_query.py` | API router: `/v1/agent/*` endpoints |
| `api/app/deps.py` | `require_agent_or_user` auth dependency |
| `api/app/config.py` | `agent_api_key` setting |
| `.opencode/mcp/project-mcp/mcp_server.py` | MCP server stdio bridge |
| `opencode.json` | MCP server + reference registration |
| `.work/features/agent-query-api/20260701-SPEC.md` | Feature SPEC |
| `.work/docs/agent-query-api.md` | **This file** — usage documentation |

### API endpoint summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/v1/agent/projects` | API key or Bearer | List all projects with stats |
| GET | `/v1/agent/projects/{id}/context` | API key or Bearer | Full project context |
| GET | `/v1/agent/tasks` | API key or Bearer | List tasks (filterable) |
| GET | `/v1/agent/tickets` | API key or Bearer | List tickets (filterable) |
| GET | `/v1/agent/search` | API key or Bearer | Unified search |

### MCP tool summary

| Tool | Maps to endpoint |
|------|----------------|
| `list_projects` | `GET /v1/agent/projects` |
| `get_project_context` | `GET /v1/agent/projects/{id}/context` |
| `get_task_info` | `GET /v1/agent/tasks` |
| `get_ticket_info` | `GET /v1/agent/tickets` |
| `search_entities` | `GET /v1/agent/search` |

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_API_KEY` | *(empty)* | Shared secret for agent API access |
| `API_BASE_URL` (MCP only) | `http://localhost:8300` | Override the API base URL |
| `MCP_SERVER_NAME` (MCP only) | `tools-project-agent` | Server name advertised in MCP handshake |

### Security notes

- `AGENT_API_KEY` is a shared secret — treat it like a password
- The MCP server only connects to `localhost` — it is not externally exposed
- API key auth provides superuser-level read access; generate strong keys
- All endpoints are read-only — no mutations possible
- The API key is never logged by the API or MCP server
