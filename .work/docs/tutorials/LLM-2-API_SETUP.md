# Tutorial: Connect Your Coding Agent to Tools-Project

Let your coding agent (opencode, Claude Code, Cursor) query project context — tasks, tickets, clients, GitHub refs — directly from the tools-project API. Two steps on the server, one on the client. Works identically for local and remote deployments.

## Who this is for

- **Developers** who want their LLM agent to write commit messages with correct ticket refs, read project context before coding, or verify task status against HANDOFF
- **Project admins** who need the agent to query across all projects
- **Anyone** running tools-project locally (`localhost:18513`) or remotely (`project.cloudsys.win`)

## Prerequisites

- A running tools-project instance (local: `docker compose --profile dev up --build`, or remote)
- A user account on that instance
- Your coding agent (opencode, etc.) installed locally

---

## Part A — Server: Generate your personal API key

### A1. Open the API Keys page

Navigate to **Settings → API Keys** in the tools-project web UI:

| Deployment | URL |
|-----------|-----|
| Local | `http://localhost:18513/settings/api-keys` |
| Remote | `https://project.cloudsys.win/settings/api-keys` |

> If you don't see "API Keys" in the navigation bar, the feature may not be deployed yet. For now, the server admin can set `AGENT_API_KEY` in `.env` as a shared key (see Part C).

### A2. Create a key

1. Click **+ New key**
2. Optionally enter a label (e.g. "My laptop", "CI/CD pipeline")
3. Click **Create**

A key starting with `tools_project_` appears — **copy it now**. This is the only time it's shown. The server stores only a SHA-256 hash; the plaintext cannot be recovered.

### A3. Manage keys

- The table shows each key's prefix, label, creation date, and last-used timestamp
- Click **Revoke** on any key to disable it immediately — any agent using it will fail to authenticate
- Create additional keys for different machines, CI servers, or team members

---

## Part B — Client: Configure your coding agent

Pick one method. The file method (B1) is permanent and recommended.

### B1. File method (recommended — one-time setup)

Create `~/.tools-project-key` with your API key and set restrictive permissions:

```bash
echo "tools_project_<your-key>" > ~/.tools-project-key
chmod 600 ~/.tools-project-key
```

For remote deployments, add the server URL as the first line:

```bash
echo "BASE_URL=https://project.cloudsys.win" > ~/.tools-project-key
echo "tools_project_<your-key>" >> ~/.tools-project-key
chmod 600 ~/.tools-project-key
```

The MCP server reads this file automatically every time it starts. No exports, no shell configuration, no risk of leaking the key in shell history.

### B2. Environment variable method (one-off)

```bash
export TOOLS_PROJECT_API_KEY=tools_project_<your-key>

# For remote deployments only:
export API_BASE_URL=https://project.cloudsys.win
```

Useful for CI/CD pipelines where env vars are the standard config mechanism.

### B3. Verify the connection

```bash
# Local instance (default)
curl -s -H "X-Api-Key: tools_project_<your-key>" \
  http://localhost:8300/v1/agent/projects | python3 -m json.tool

# Remote instance
curl -s -H "X-Api-Key: tools_project_<your-key>" \
  https://project.cloudsys.win/v1/agent/projects | python3 -m json.tool
```

Successful response:

```json
{
  "ok": true,
  "data": [
    {
      "id": "uuid",
      "name": "My Project",
      "slug": "my-project",
      "status": "active",
      "project_key": "MFP",
      "open_tasks": 12,
      "open_tickets": 3,
      "member_count": 5,
      ...
    }
  ]
}
```

### B4. Your agent is now connected

The MCP server registered in `opencode.json` launches automatically when your coding agent starts. It reads your key from `~/.tools-project-key` (or the env var) and exposes five tools:

| Tool | What it does |
|------|-------------|
| `list_projects` | List all projects with task/ticket/member counts |
| `get_project_context` | Full project dump: details, tasks, tickets, members, clients, GitHub refs |
| `get_task_info` | List tasks, filterable by ref or status |
| `get_ticket_info` | List tickets, filterable by ref or status |
| `search_entities` | Unified search across projects, tasks, tickets, clients, and prospects |

**Example:** "What's the status of ticket TPR-T-12?" — your agent calls `get_ticket_info` with `ref=TPR-T-12` and gets the title, status, and linked commits in one response.

---

## Part C — Server admin: Shared key fallback (optional)

For single-user deployments or local development, the server admin can set a shared key that bypasses personal API keys entirely. All agent queries with the matching key run as a synthetic superuser.

### C1. Generate and set the key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output, e.g.: abc123...xyz
```

Add to the project's `.env` file:

```env
AGENT_API_KEY=abc123...xyz
```

### C2. Restart the API container

```bash
docker compose --profile dev up --build api
```

### C3. Configure the client

The MCP server reads `AGENT_API_KEY` as a fallback. Either:

```bash
# File method (add after any personal key):
echo "abc123...xyz" >> ~/.tools-project-key

# Or env var:
export AGENT_API_KEY=abc123...xyz
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `401 Unauthorized` | The key is wrong or revoked. Generate a new one from Settings → API Keys. |
| `403 Forbidden` | Your user account is not a superuser. Ask the admin to grant superuser privileges. |
| No response / connection refused | The API is not running. Check `docker compose ps` or the remote server status. |
| MCP server doesn't start | Verify `~/.tools-project-key` permissions: `chmod 600 ~/.tools-project-key`. Check that opencode can run `python3`. |
| Key shown as "never used" | The agent hasn't queried yet. The timestamp updates on first authenticated request. |
| `tools_project_` prefix missing | The server auto-generates the prefix on creation. If you're using a manually-created key (shared admin key), the prefix is not required. |

---

## See also

- **Reference:** `.work/docs/agent-query-api.md` — full endpoint catalog, response schemas, MCP tool details
- **Source:** `.opencode/mcp/project-mcp/mcp_server.py` — MCP server implementation
- **Source:** `api/app/routers/me_api_keys.py` — API key management endpoints
- **Source:** `api/app/routers/agent_query.py` — aggregation query endpoints
