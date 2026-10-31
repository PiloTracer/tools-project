# Tutorial: connect your coding agent to tools-project

Let a coding agent (opencode, Claude Code, Cursor, …) query projects, tasks, tickets, commits and —
after `agent_api_version 1.1.0` — ticket comments and screenshots. One key per machine, one MCP
registration per repository.

**Status:** works against `1.0.0` (verified 2026-10-30). Steps that need `1.1.0` are marked.

For the endpoint/tool contract see [`../agent-query-api.md`](../agent-query-api.md). For choosing
between this and an app-to-app integration see
[`../guides/quick-reference-to-connect-agent-with-tools-project.md`](../guides/quick-reference-to-connect-agent-with-tools-project.md).

## Who this is for

- Developers whose agent should write commit messages with the right ref, read project context
  before coding, or reconcile `HANDOFF`/`NEXT` with live state.
- Project admins who need an agent to read across projects.

## Prerequisites

| Requirement | Why |
|-------------|-----|
| A running tools-project (local `./bin/start.sh dev`, or the hosted instance) | The API |
| An account that is a **superuser** | Agent routes answer `403` for non-superusers (see the reference §3) |
| Python **3.10+** on the agent machine | The MCP server uses modern typing |
| Your coding agent | opencode, Claude Code, Cursor, … |

---

## Part A — create the API key

### A1. Open Settings → API Keys

| Deployment | URL |
|-----------|-----|
| Local dev | `http://localhost:18513/settings/api-keys` |
| Hosted | `https://project.cloudsys.win/settings/api-keys` |

If the page is missing, the deployment predates the feature — the server admin can use the shared
key fallback in Part F instead.

### A2. Create and copy

**+ New key** → optional label (e.g. "laptop", "CI") → **Create**. The value starts with
`tools_project_` and is shown **once**; only its SHA-256 hash is stored. Do not paste it into chat,
issues or shell history.

### A3. Know what it grants

- Read-only across the projects of the deployment; no upload, comment or transition.
- Revocable at any time from the same page; `last used` tells you whether a copy is live.
- The key inherits the **owner's** privilege: a non-superuser owner cannot call agent routes.

---

## Part B — put the key on the machine

### B1. Key file (recommended)

```bash
printf 'BASE_URL=https://project.cloudsys.win\ntools_project_<your-key>\n' > ~/.tools-project-key
chmod 600 ~/.tools-project-key
```

Local instance: omit the `BASE_URL` line (defaults to `http://localhost:8300`) or set
`BASE_URL=http://localhost:8300`.

### B2. Environment variables (CI, one-off)

```bash
export TOOLS_PROJECT_API_KEY=tools_project_<your-key>
export API_BASE_URL=https://project.cloudsys.win   # remote only
```

**Precedence** (first match wins — this is the usual cause of "it talks to the wrong instance"):

| Setting | Order |
|---------|-------|
| Key | `TOOLS_PROJECT_API_KEY` → `~/.tools-project-key` → `AGENT_API_KEY` (legacy shared key) |
| Base URL | `API_BASE_URL` → `BASE_URL=` line in the key file → `http://localhost:8300` |

### B3. Verify the credential before touching the agent

```bash
BASE=$(grep '^BASE_URL=' ~/.tools-project-key | cut -d= -f2-); BASE=${BASE:-http://localhost:8300}
KEY=$(tail -n1 ~/.tools-project-key)
curl -s -H "X-Api-Key: $KEY" -H "User-Agent: tools-project-mcp/1.1.0" "$BASE/v1/agent/projects" \
  | python3 -m json.tool | head -20
```

Expect `"ok": true` and a list with names/counts. A non-default `User-Agent` is mandatory on the
hosted instance: Cloudflare rejects urllib's default with **403 Error 1010**.

---

## Part C — register the MCP server

### C1. Copy the server into the repository

```bash
mkdir -p .opencode/mcp/project-mcp
# Canonical copy (sends the Cloudflare-safe User-Agent; includes the 1.1.0 tools):
cp /mnt/work/Projects/tools-project/.opencode/mcp/project-mcp/mcp_server.py \
   .opencode/mcp/project-mcp/
grep -c 'User-Agent' .opencode/mcp/project-mcp/mcp_server.py   # must print >= 1
```

### C2. Add the registration

opencode (`opencode.json`):

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

Cursor (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "tools-project": {
      "command": "python3",
      "args": [".opencode/mcp/project-mcp/mcp_server.py"]
    }
  }
}
```

Claude Code (`.claude/mcp.json`): same `mcpServers` shape with `"type": "stdio"`.

No key goes into these files — the server reads `~/.tools-project-key`. Only add
`API_BASE_URL` if every user of the repository must hit a specific instance; it overrides the key
file.

### C3. Restart the agent and confirm the tools are listed

The agent should discover five tools: `list_projects`, `get_project_context`, `get_task_info`,
`get_ticket_info`, `search_entities` (plus `get_ticket_detail`, `list_ticket_activities`,
`get_attachment` after 1.1.0).

Run one real query ("list my projects") before declaring success. Then, when the server supports
it:

```bash
python3 .opencode/mcp/project-mcp/mcp_server.py --self-check
```

`--self-check` prints the effective base URL and where it came from, the API's
`agent_api_version`, and the enabled tools.

---

## Part D — use it

| Goal | Tool |
|------|------|
| Commit message with the right ref | `get_ticket_info(ref="PZT-T-2")` → `PZT-T-2: <plain subject>` |
| Understand a project before coding | `get_project_context(project_id="…")` |
| Reconcile `HANDOFF`/`NEXT` with live state | `get_task_info(status="todo", limit=200)` |
| Find a ticket by words | `search_entities(q="licitaciones")` |
| Read an incident's thread + screenshots (**1.1.0**) | `get_ticket_detail(ticket="PZT-T-2")` → `list_ticket_activities` → `get_attachment` |

Worked example: [`AGENT_TICKET_CONTEXT.md`](AGENT_TICKET_CONTEXT.md).

---

## Part E — keep the copy current

The MCP server is a client artifact: consumers keep a copy, so a new tool does not appear until the
copy is refreshed. A stale copy looks connected and fails every call.

**After 1.1.0 (served from the deployment):**

```bash
BASE=$(grep '^BASE_URL=' ~/.tools-project-key | cut -d= -f2-); BASE=${BASE:-http://localhost:8300}
curl -s -o .opencode/mcp/project-mcp/mcp_server.py \
  -H "X-Api-Key: $(tail -n1 ~/.tools-project-key)" \
  -H "User-Agent: tools-project-mcp/1.1.0" \
  "$BASE/v1/agent/client/mcp_server.py"
chmod 755 .opencode/mcp/project-mcp/mcp_server.py
python3 .opencode/mcp/project-mcp/mcp_server.py --self-check
```

**Today:** copy from `/mnt/work/Projects/tools-project/.opencode/mcp/project-mcp/mcp_server.py`
(the canonical copy — it sends the `User-Agent` and carries the 1.1.0 tools), then run
`--self-check`. The served-file download above works once a 1.1.0 build is deployed.

Check after every refresh: `--self-check` (1.1.0) or a `list_projects` call (today) plus the
`grep -c 'User-Agent'` check.

---

## Part F — admin fallback: shared key (single-tenant only)

For local or single-user deployments the admin can set one server-wide key. Every caller then acts
as a synthetic superuser — convenient, not suitable for multi-user production.

```env
# .env.dev / .env.prd — this project never reads a bare .env
AGENT_API_KEY=<random 32+ chars>
```

Restart the API (`./bin/start.sh dev restart` or the deploy pipeline) and use it via
`AGENT_API_KEY` in the agent environment, or as an extra line in the key file. In multi-tenant mode
(`MULTI_TENANCY_ENABLED=true`) the shared key is rejected with `401`; personal keys are the only
path.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `401` | Wrong/revoked key; shared key in multi-tenant mode | Recreate the key; use a personal key |
| `403 {"detail":"Agent endpoints require superuser privileges"}` | Key owner is not a superuser | Ask an admin; do not create a second account |
| `403` HTML page / `Error 1010` | Default urllib User-Agent | Use a copy that sends `User-Agent` (Part C1) |
| `404` on `/v1/agent/tickets/{ref}` or `/capabilities` | Deployment predates 1.1.0 | Check `/openapi.json` `info.version`; deploy |
| MCP starts, tools fail | Stale copy, wrong `API_BASE_URL`, or wrong instance | `--self-check`; check precedence in B2 |
| `python: command not found` | Config uses `python` | Use `python3` (3.10+) |
| Tools missing after an update | Agent not restarted, or a 1.0.0 API hides 1.1.0 tools | Restart; compare `recommended_mcp_server_version` |
| Key page missing | Old deployment | Part F, or upgrade |

---

## See also

- [`../agent-query-api.md`](../agent-query-api.md) — endpoint/tool contract, limits, troubleshooting
- [`../guides/quick-reference-to-connect-agent-with-tools-project.md`](../guides/quick-reference-to-connect-agent-with-tools-project.md) — which integration path
- [`AGENT_TICKET_CONTEXT.md`](AGENT_TICKET_CONTEXT.md) — ticket + comments + screenshots (**1.1.0**)
- [`REPO_INTEGRATION.md`](REPO_INTEGRATION.md) — GitHub commit linking and plan sync
- `.opencode/mcp/project-mcp/mcp_server.py` — the MCP server in this repository
- `api/app/routers/agent_query.py` — the server side
