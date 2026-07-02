# Project Query Integration — Reference Card

**Audience:** Agent OS directors and skill authors in `.ai`, `.ai.ui`, `.ai.biz`, `.ai.soc`

**Status:** Optional integration. Enable when the operator wants agents to query live project data (tasks, tickets, clients, projects).

**Source of truth:** `/mnt/work/Projects/tools-project/.work/docs/agent-query-api.md`

---

## What this gives you

5 MCP tools that any agent can call:

| Tool | What it does | Parameters |
|------|-------------|------------|
| `list_projects` | All projects with open task/ticket/member counts | *(none)* |
| `get_project_context` | Full project + tasks + tickets + members + clients + GitHub refs | `project_id` |
| `get_task_info` | List tasks, filterable by ref or status | `ref`, `status`, `limit` |
| `get_ticket_info` | List tickets, filterable by ref or status | `ref`, `status`, `limit` |
| `search_entities` | Cross-entity search (projects, tasks, tickets, clients, prospects) | `q`, `limit` |

---

## Setup (one-time)

### 1. Deploy the MCP server

Copy from tools-project into the consuming project:

```bash
mkdir -p .opencode/mcp/project-mcp
cp /mnt/work/Projects/tools-project/.opencode/mcp/project-mcp/mcp_server.py \
   .opencode/mcp/project-mcp/
```

### 2. Register in opencode.json

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

### 3. Create the key file

User runs (from the web UI at Settings → API Keys):

```bash
echo "tools_project_<generated-key>" > ~/.tools-project-key
chmod 600 ~/.tools-project-key
```

For remote deployments, add URL as first line:

```bash
echo "BASE_URL=https://project.cloudsys.win" > ~/.tools-project-key
echo "tools_project_<generated-key>" >> ~/.tools-project-key
chmod 600 ~/.tools-project-key
```

### 4. Deploy the setup skill

Copy the `project-query-setup` skill into the framework's skills directory so operators can invoke `@project-query-setup install`:

```bash
cp -r /tmp/opencode/project-query-setup \
      /path/to/framework/skills/project-query-setup/
```

---

## How skills use it

### Pattern A: Declare as prerequisite (recommended)

In any skill's `skill.md` preamble, add:

```markdown
**Prerequisites (when project context is needed):**
- tools-project MCP server registered (provides `get_project_context`, `get_task_info`,
  `get_ticket_info`, `search_entities`, `list_projects` tools)
- `~/.tools-project-key` file present with `chmod 600`
```

The skill body then instructs the agent to call MCP tools directly:

```markdown
### Step X — Load project context

Call `get_project_context` with the project UUID from HANDOFF to understand
what tasks and tickets are open. Then use `get_ticket_info` with the relevant
ref for commit message context.
```

### Pattern B: Check availability at runtime

In a protocol step:

```markdown
### Step X — Optional: Verify against live state

If tools-project MCP tools are available:
  Call `get_task_info(ref="{ref}")` to check if the task is done/blocked/open.
  If status is "done", skip this work and note it in HANDOFF.

If not available:
  Proceed with HANDOFF/NEXT as source of truth.
```

### Pattern C: Fallback gracefully

```markdown
### Step X — Query ticket status

Try: `get_ticket_info(ref="<ref>", limit=1)`.
- If the tool is available and returns data, use the live status.
- If the tool returns 401 or is unavailable, fall back to the
  `#### Status` column in NEXT.md and note "offline verification" in the task.
```

---

## Per-OS usage patterns

### `.ai` — Engineering OS

| Situation | Tool to call |
|-----------|-------------|
| Building a commit message | `get_ticket_info(ref="TPR-T-12")` → extract title, status, linked commits |
| Starting a new code task | `get_project_context(project_id)` → understand members, open tasks, GitHub refs |
| Verifying HANDOFF vs reality | `get_task_info(ref="TPR-3")` → compare status with NEXT.md |
| Choosing next task | `get_task_info(status="todo", limit=20)` → pick the highest-priority todo |
| Understanding a project before new features | `get_project_context(project_id)` → full landscape |
| Searching for related work | `search_entities(q="rate limiter")` → find existing tasks/tickets |

### `.ai.ui` — UI Design OS

| Situation | Tool to call |
|-----------|-------------|
| Which tickets need UI work? | `get_ticket_info(status="open")` → filter by UI-relevant titles |
| Design a screen for a project | `get_project_context(project_id)` → understand client, members, existing components |
| Find examples of existing components | `search_entities(q="dashboard")` → find related tickets/tasks |
| Verify screen SPEC against real data | `get_project_context(project_id)` → check actual member count, client name |
| Determine which screens to build next | `list_projects` + `get_task_info(status="todo")` → prioritize by project status |

### `.ai.biz` — Business OS

| Situation | Tool to call |
|-----------|-------------|
| Portfolio health review | `list_projects` → check open_tasks/open_tickets per project |
| Client needing attention | `search_entities(q="client name")` → find client, then `get_project_context` for their project |
| Content ideas from completed work | `get_ticket_info(status="closed", limit=20)` → find recently resolved items |
| Pipeline analysis | `search_entities(q="prospect")` → find prospects by stage |
| Pricing/scope for new engagement | `get_project_context(project_id)` → task count, ticket burden, team size |

### `.ai.soc` — Security OS

| Situation | Tool to call |
|-----------|-------------|
| Find tickets flagged for security | `search_entities(q="penetration" OR "security" OR "vuln")`) |
| Check pen test findings status | `get_ticket_info(ref="TPR-T-9")` → status, linked commits, resolution |
| Security review of a project | `get_project_context(project_id)` → full ticket list, GitHub refs for code links |
| Share completed security work | `get_ticket_info(status="resolved")` → filter by security keywords |
| Identify security debt across projects | `list_projects` → then `get_project_context` per project → count open security tickets |

---

## Deploying the skill

Copy into each framework's skills directory:

| Framework | Target path |
|-----------|------------|
| `.ai` | `/mnt/work/Projects/.ai/skills/project-query-setup/skill.md` |
| `.ai.ui` | `/mnt/work/Projects/.ai.ui/skills/project-query-setup/skill.md` |
| `.ai.biz` | `/mnt/work/Projects/.ai.biz/skills/project-query-setup/skill.md` |
| `.ai.soc` | `/mnt/work/Projects/.ai.soc/skills/project-query-setup/skill.md` |

Then register in each framework's `skills/README.md`:

```markdown
| `project-query-setup` | Guide through tools-project key creation, MCP registration, connectivity test, and OS-specific usage patterns |
```

And add to each framework's `.cursorrules` § Skills table:

```markdown
| project-query-setup | `/mnt/work/Projects/.ai/skills/project-query-setup/` | Guided setup: API key creation, MCP registration, connectivity test. OS-aware (adapts guidance per OS). |
```

---

## Verification checklist

After deploying to a framework:

- [ ] `project-query-setup/skill.md` copied to framework's `skills/`
- [ ] Skill registered in framework's `skills/README.md`
- [ ] Skill registered in framework's `.cursorrules` (or equivalent)
- [ ] MCP server copied to consuming project's `.opencode/mcp/project-mcp/`
- [ ] MCP block added to consuming project's `opencode.json`
- [ ] `~/.tools-project-key` created with `chmod 600`
- [ ] Live query returns `{ "ok": true, "data": [...] }`
- [ ] Agent calls `@project-query-setup status` and sees green
- [ ] One OS-specific skill declares MCP tools as prerequisite and uses them in a protocol step

---

## Files involved

| File | Location | Purpose |
|------|----------|---------|
| `skill.md` | Each framework's `skills/project-query-setup/` | The guided setup skill |
| `mcp_server.py` | Consuming project's `.opencode/mcp/project-mcp/` | The MCP stdio bridge |
| `opencode.json` | Consuming project root | MCP server registration |
| `~/.tools-project-key` | User's home directory | API key (chmod 600) |
| `skills/README.md` | Each framework | Skill registry entry |
| `.cursorrules` | Each framework | Skill table entry |
