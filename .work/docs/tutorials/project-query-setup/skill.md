# SKILL: project-query-setup

**Purpose:** Guide user through connecting their coding agent to tools-project, and teach it to query tasks, tickets, projects, and clients for context-aware work.

**Deploy to:** Any Agent OS framework (`.ai`, `.ai.ui`, `.ai.biz`, `.ai.soc`) — optional integration.

**Tutorial companion:** `.work/docs/tutorials/LLM-2-API_SETUP.md` (step-by-step setup walkthrough)

---

## Hard rules

1. **Optional integration.** This skill is never required. The user must explicitly ask to set it up or the director must ask first.
2. **Read-only.** The API provides read-only access. No mutations, no writes, no data modification.
3. **Key security.** Never log the API key. Never store it in shell history. `/tmp` is forbidden for key material. The `~/.tools-project-key` file must be `chmod 600`.
4. **Verify before claiming done.** Run a live query to the API and show the actual response. Never claim "connected" without evidence.

---

## Modes

| Invocation | Mode |
|-----------|------|
| `@project-query-setup install` | Full guided setup: generate key → create file → test → register MCP |
| `@project-query-setup status` | Check if connected (key file exists? API reachable? MCP tools listed?) |
| `@project-query-setup key` | Guide the user through web UI → key creation → `~/.tools-project-key` |
| `@project-query-setup test` | Verify connectivity by listing projects |
| `@project-query-setup register-mcp` | Register MCP server in consuming project's opencode.json |
| `@project-query-setup help` | Show available tools and usage patterns for this OS |
| `@project-query-setup` (no verb) | Default to `status` mode |

---

## Install protocol

### Step 1 — Detect OS context

Read the current OS identity from START_HERE.md or `.cursorrules`:

| Detected | OS | What it can do |
|----------|----|----------------|
| `.ai/` skills | Engineering OS | Query tasks/tickets for code work, build commit messages, verify HANDOFF vs live state, load project context before new features |
| `.ai.ui/` skills | UI Design OS | Check which tickets need UI work, get client/project context for screen design, search for existing components |
| `.ai.biz/` skills | Business OS | List all projects/clients for portfolio review, identify clients needing attention, find content to share |
| `.ai.soc/` skills | Security OS | Find tickets flagged for security review, check task status for pen test findings, search for vulnerability patterns |

Store this in an `OS_CONTEXT` variable for tailoring the rest of the protocol.

### Step 2 — Prerequisites gate

Check and report:

1. Is `python3` available? (required for MCP server)
2. Is there a running tools-project instance?
   - Local: try `curl -s http://localhost:8300/healthz`
   - Remote: ask user for URL
3. Can the user reach the web UI?
   - Local: `http://localhost:18513/settings/api-keys`
   - Remote: `https://<user-provided-url>/settings/api-keys`

If any prerequisite fails, stop and tell the user what to fix.

### Step 3 — Key creation (web UI)

Guide the user:

```
1. Open: <URL>/settings/api-keys
2. Click "+ New key"
3. Enter a label (e.g. "My laptop", "Agent OS integration")
4. Click "Create"
5. COPY the key now — it starts with "tools_project_" — this is the ONLY time it's shown
```

Wait for the user to confirm they have the key. Do NOT ask them to paste it into chat.

### Step 4 — Write the key file

Tell the user to run (or run it for them with their explicit permission):

```bash
# For local tools-project:
echo "tools_project_<key>" > ~/.tools-project-key

# For remote tools-project:
echo "BASE_URL=https://project.cloudsys.win" > ~/.tools-project-key
echo "tools_project_<key>" >> ~/.tools-project-key

# Always lock permissions:
chmod 600 ~/.tools-project-key
```

**Critical:** Tell the user to replace `<key>` with the actual key. Do NOT write the key yourself unless the user explicitly pastes it in the conversation and asks you to.

### Step 5 — Test connectivity

Run a live query and show the result:

```bash
curl -s http://localhost:8300/v1/agent/projects \
  -H "X-Api-Key: $(head -n2 ~/.tools-project-key | tail -n1)"
```

For remote:
```bash
BASE_URL=$(grep BASE_URL= ~/.tools-project-key | cut -d= -f2-)
KEY=$(tail -n1 ~/.tools-project-key)
curl -s "$BASE_URL/v1/agent/projects" -H "X-Api-Key: $KEY"
```

Expected: `{ "ok": true, "data": [...] }` with project names. Show the actual output.

If `401 Unauthorized` — the key is wrong or revoked. Go back to Step 3.
If `403 Forbidden` — the user is not a superuser. Tell them to contact their admin.
If `Connection refused` — API is not running. Stop and tell user.

### Step 6 — Register MCP server

If the consuming project has its own `opencode.json` (e.g. `.ai.soc` does), add the MCP server block:

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

If it does NOT have `opencode.json` (like `.ai`, `.ai.ui`, `.ai.biz`), explain:

> The MCP server registration lives in the **consuming project's** opencode.json (e.g. `tools-project/opencode.json`, or any project that deploys this OS). It does not belong in the framework's own config. When you deploy this OS to a project, add the MCP block to THAT project's opencode.json. See the reference guide for the exact block.

### Step 7 — Confirm and show OS-specific patterns

Report success with the actual project count returned. Then show OS-specific usage patterns:

```
Connected to tools-project. Found N projects.

Your {OS_NAME} agents can now:

  {OS-specific capabilities from the table in Step 1}

To use this from any skill, add this prerequisite line
to the skill's preamble:

  Prerequisites: tools-project MCP server registered
  (provides list_projects, get_project_context,
  get_task_info, get_ticket_info, search_entities tools)

Reference: .work/docs/agent-query-api.md
Tutorial:  .work/docs/tutorials/LLM-2-API_SETUP.md
```

---

## Status protocol

Run `~/.tools-project-key` check and a live query. Report:

```
Key file:    {present/missing} ({path})
Permissions: {chmod} (should be 600)
API:         {reachable/unreachable} {url}
Auth:        {ok / 401 / 403}
Projects:    {count} accessible
MCP tools:   {count} registered ({names})
```

---

## Key protocol (standalone)

Same as Steps 3-4 from Install protocol. Lighter — no MCP registration, no API test (user runs `test` or `status` after).

---

## Test protocol

Same as Step 5 from Install protocol. Returns a yes/no + response snippet.

---

## Help protocol

Show the 5 MCP tools available and their descriptions. Then show one domain-specific example for the current OS:

| OS | Example |
|----|---------|
| Engineering | "What's the status of ticket TPR-T-12?" → `get_ticket_info(ref="TPR-T-12")` |
| UI Design | "What projects need UI work?" → `list_projects` + `get_task_info(status="todo")` |
| Business | "Which clients need attention?" → `list_projects` + `get_project_context()` per project |
| Security | "Find tickets related to rate limiting" → `search_entities(q="rate limit")` |

---

## Reference

| Doc | Path |
|-----|------|
| Full API + MCP guide | `.work/docs/agent-query-api.md` |
| Step-by-step tutorial | `.work/docs/tutorials/LLM-2-API_SETUP.md` |
| Feature SPEC | `.work/features/agent-query-api/20260701-SPEC.md` |
| MCP server source | `.opencode/mcp/project-mcp/mcp_server.py` |

---

## Anti-patterns to refuse

- Claiming "connected" without a live API response
- Writing the key file without `chmod 600` after
- Asking the user to paste their API key into chat
- Storing the key in `/tmp` or any non-`~/.tools-project-key` location
- Logging the key value in any output
- Registering MCP in the framework's own config (it belongs in the consuming project's opencode.json)
