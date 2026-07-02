# Deploy Project Query to Agent OS — Full Plan

**Date:** 2026-07-01
**Artifacts prepared:** `skill.md`, `reference.md` under `/tmp/opencode/project-query-setup/`
**Tutorial:** `/mnt/work/Projects/tools-project/.work/docs/tutorials/LLM-2-API_SETUP.md`
**API reference:** `/mnt/work/Projects/tools-project/.work/docs/agent-query-api.md`
**MCP server:** `/mnt/work/Projects/tools-project/.opencode/mcp/project-mcp/mcp_server.py`

---

## Overview

This plan adds an **optional `project-query-setup` skill** to all four Agent OS frameworks (`.ai`, `.ai.ui`, `.ai.biz`, `.ai.soc`). The skill guides operators through:

1. Creating a personal API key from tools-project's web UI
2. Writing it to `~/.tools-project-key` (secure, no env var export needed)
3. Deploying the MCP server to the consuming project
4. Registering the MCP server in the project's `opencode.json`
5. Testing connectivity with a live API call
6. Showing OS-specific usage patterns

All four frameworks share the identical skill file — it auto-detects which OS it's running in and adapts its guidance (tailoring examples and use cases).

---

## WHAT — The two artifacts

### Artifact 1: `skill.md` (the skill itself)
**Path:** `/tmp/opencode/project-query-setup/skill.md` (ready to copy)
**Modes:** `install`, `status`, `key`, `test`, `register-mcp`, `help`
**Auto-detects OS** and shows relevant use cases

### Artifact 2: `reference.md` (integration reference)
**Path:** `/tmp/opencode/project-query-setup/reference.md` (ready to copy)
**Audience:** Skill authors adding MCP tool calls to their protocols
**Contains:** Per-OS usage patterns, setup checklist, file layout

---

## WHERE — Deployment map

### Step 1: Copy skill into each framework

```bash
# .ai (Engineering)
cp -r /tmp/opencode/project-query-setup \
      /mnt/work/Projects/.ai/skills/project-query-setup/

# .ai.ui (UI Design)
cp -r /tmp/opencode/project-query-setup \
      /mnt/work/Projects/.ai.ui/skills/project-query-setup/

# .ai.biz (Business)
cp -r /tmp/opencode/project-query-setup \
      /mnt/work/Projects/.ai.biz/skills/project-query-setup/

# .ai.soc (Security)
cp -r /tmp/opencode/project-query-setup \
      /mnt/work/Projects/.ai.soc/skills/project-query-setup/
```

### Step 2: Register in each framework's `skills/README.md`

Add this row to each README's skill table:

```markdown
| `project-query-setup` | Guided setup: tools-project API key creation, `~/.tools-project-key`, MCP registration, connectivity test, OS-specific usage patterns |
```

### Step 3: Register in each framework's `.cursorrules`

Add this row to each `.cursorrules` § Skills table:

```markdown
| project-query-setup | `skills/project-query-setup/` | Optional. Guide through tools-project API key setup, MCP server registration, and connectivity test. Detects OS context and tailors guidance. |
```

### Step 4: (For `.ai`) Add process-router entry

In `/mnt/work/Projects/.ai/skills/process-router/reference.md`:

```markdown
| "connect my agent to tools-project" / "setup project query" | `@project-query-setup install` — guided key creation, MCP registration, connectivity test |
| "is my agent connected to tools-project?" | `@project-query-setup status` — checks key file, API, MCP tools |
```

### Step 5: (For `.ai.soc` only) Add MCP server

`.ai.soc` is the only framework with its own `opencode.json`. Add:

```json
"mcp": {
  "tools-project": {
    "type": "local",
    "command": ["python3", ".opencode/mcp/project-mcp/mcp_server.py"],
    "enabled": true
  }
}
```

And copy the MCP server:

```bash
mkdir -p /mnt/work/Projects/.ai.soc/.opencode/mcp/project-mcp
cp /mnt/work/Projects/tools-project/.opencode/mcp/project-mcp/mcp_server.py \
   /mnt/work/Projects/.ai.soc/.opencode/mcp/project-mcp/
```

For `.ai`, `.ai.ui`, `.ai.biz`: the MCP registration belongs in the **consuming project's** `opencode.json` (e.g. `tools-project/opencode.json`), not the framework's own config.

---

## WHEN — What agents can do after integration

### Engineering (.ai)

```
"Build a commit message for ticket TPR-T-12"
    → get_ticket_info(ref="TPR-T-12")
    → extracts title, status, linked GitHub commits
    → builds: "TPR-T-12: fix rate limiter overflow on retry"

"What is the state of project X before I start M2?"
    → get_project_context(project_id)
    → returns all tasks, tickets, members, clients, GitHub refs
    → agent reconciles HANDOFF/NEXT with live state

"What tasks are open and assigned to me?"
    → get_task_info(status="todo", limit=50)
    → filters by assignee from auth context

"Find tickets related to the login bug I'm fixing"
    → search_entities(q="login")
    → returns tasks, tickets, projects mentioning "login"

"Jumpstart a new project based on existing project Y"
    → get_project_context(y_id)
    → reads tasks, members, description
    → scaffolds similar structure for new project
```

### UI Design (.ai.ui)

```
"Which tickets need UI work?"
    → get_ticket_info(status="open")
    → searches titles for UI keywords (component, screen, design, layout)

"Design a screen for client X's project"
    → get_project_context(project_id)
    → extracts client name, team members, description
    → informs screen SPEC layout, user roles, feature set

"What existing components are referenced in open tickets?"
    → search_entities(q="button" OR "card" OR "modal")
    → finds tickets mentioning existing components
    → reuses rather than re-designs
```

### Business (.ai.biz)

```
"Which clients need attention?"
    → list_projects → per project, check open_tickets and open_tasks

"What was completed this month?"
    → get_ticket_info(status="closed", limit=100)
    → get_task_info(status="done", limit=100)
    → summarizes for business review

"Generate a content idea from shipped work"
    → "What was resolved in the last sprint?"
    → search_entities(q="shipped" or "done")
    → surfaces completed features for marketing content

"Assess team velocity for client Y"
    → get_project_context(y_project_id)
    → task completion rate, ticket burden, member count
```

### Security (.ai.soc)

```
"Find all open security tickets"
    → search_entities(q="penetration" OR "vuln" OR "security" OR "rate limit")
    → returns tickets that need security review

"What's the status of the pen test findings?"
    → get_ticket_info(ref="TPR-T-9")
    → confirms all 9 findings are resolved or identifies remaining

"Audit project X for security surface"
    → get_project_context(x_id)
    → reviews all tickets and GitHub refs for security patterns

"Which closed tickets mention hardening?"
    → search_entities(q="hardening" OR "csrf" OR "rate limit" OR "cors")
    → surfaces completed security work for audit trail
```

---

## HOW — Integration prompt for each framework

This is the text that should be pasted into each framework so its agents understand the integration. Each OS gets a tailored version.

### For `.ai` (Agent / Engineering OS)

Paste into: `.ai/START_HERE.md` §10 FAQ table, or as a new `.ai/docs/integration/tools-project-query.md`

```markdown
## Optional: Connect to tools-project API

Your agents can query live project data (tasks, tickets, clients, projects)
from a running tools-project instance when the operator enables it.

### Enable it

Run: `@project-query-setup install`
This guides the operator through:
1. Generate a personal API key from Settings → API Keys
2. Write it to `~/.tools-project-key` (chmod 600)
3. Register the MCP server in the consuming project's opencode.json
4. Verify connectivity with a live query

### What agents gain

| Tool | What it does |
|------|-------------|
| `list_projects` | All projects with task/ticket/member counts |
| `get_project_context` | Full project, tasks, tickets, members, clients, GitHub refs |
| `get_task_info` | Tasks filterable by ref or status |
| `get_ticket_info` | Tickets filterable by ref or status |
| `search_entities` | Cross-entity search |

### How skills use it

Skills declare MCP tools as prerequisites in their preamble:

  **Prerequisites:** tools-project MCP server registered
  (provides get_project_context, get_task_info, get_ticket_info,
  search_entities, list_projects tools)

Then call them in protocol steps:
- `get_project_context(project_id)` before starting a new milestone
- `get_ticket_info(ref="TPR-T-12")` when building a commit message
- `get_task_info(status="todo")` when picking next work

### Reference

- Full guide: .work/docs/agent-query-api.md
- Tutorial:   .work/docs/tutorials/LLM-2-API_SETUP.md
- Skill:      @project-query-setup help
```

### For `.ai.ui` (UI Design OS)

Paste into: `.ai.ui/START_HERE.md` §10 FAQ table

```markdown
## Optional: Connect to tools-project (project data)

Your UI agents can query live project data from tools-project to inform
screen design, discover work needing UI, and verify real data against SPECs.

### Enable it

Run: `@project-query-setup install`
This sets up the API key and MCP server registration.

### What UI agents gain

- `get_project_context(project_id)` → client name, team members, description
  (informs screen SPEC: user roles, feature set, branding)
- `get_ticket_info(status="open")` → find tickets needing UI work
- `search_entities(q="dashboard")` → find related tickets for reuse
- `list_projects` → prioritize which projects need screen work

### How screen SPECs use it

In a screen SPEC §4 (Project/Feature Context), add:

  **Live context** (optional): Call `get_project_context({project_id})`
  to verify the team size, client name, and active task count against
  this SPEC's assumptions.

### Reference

- Full guide: .work/docs/agent-query-api.md § Framework integration guide → .ai.ui
- Tutorial:   .work/docs/tutorials/LLM-2-API_SETUP.md
- Skill:      @project-query-setup help
```

### For `.ai.biz` (Business OS)

Paste into: `.ai.biz/START_HERE.md` §8 FAQ table

```markdown
## Optional: Connect to tools-project (portfolio data)

Your business agents can query the full project/client/ticket portfolio
from tools-project to inform strategy, content, reviews, and discovery.

### Enable it

Run: `@project-query-setup install`

### What business agents gain

- `list_projects` → portfolio overview with task/ticket health
- `get_project_context(project_id)` → deep dive on one client engagement
- `search_entities(q="client name")` → find client data for discovery prep
- `get_ticket_info(status="closed")` → completed work for review/content

### How business skills use it

- `@biz-review weekly` → calls `list_projects` + `get_ticket_info(closed)` for
  actual velocity and resolution data
- `@biz-discovery prepare` → calls `search_entities` to find the prospect's
  company name and any existing touchpoints
- `@content-writing write` → calls `get_ticket_info(closed, limit=20)` to find
  recently resolved work to write about

### Reference

- Full guide: .work/docs/agent-query-api.md § Framework integration guide → .ai.biz
- Tutorial:   .work/docs/tutorials/LLM-2-API_SETUP.md
- Skill:      @project-query-setup help
```

### For `.ai.soc` (Security OS)

Paste into: `.ai.soc/START_HERE.md` or a new section

```markdown
## Optional: Connect to tools-project (security tickets)

Your security agents can query tools-project to find security-related tickets,
verify pen test findings status, and link vulnerability work to code.

### Enable it

Run: `@project-query-setup install`

Since `.ai.soc` has its own opencode.json, the MCP server registration
will be added directly. The key file goes to `~/.tools-project-key` as usual.

### What security agents gain

- `search_entities(q="penetration" OR "vuln" OR "security")` → find tickets flagged for review
- `get_ticket_info(ref="TPR-T-12")` → verify status of specific findings
- `get_project_context(project_id)` → full ticket list + GitHub refs for code auditing
- `get_task_info(status="todo")` → find pending security tasks

### How security skills use it

Before running `@soc-director` against a target:
1. `search_entities(q="<project_key>")` to find the project
2. `get_project_context(project_id)` to understand the codebase scope
3. `get_ticket_info(refs)` to check if findings are already tracked

### Reference

- Full guide: .work/docs/agent-query-api.md § Framework integration guide → .ai.soc
- Tutorial:   .work/docs/tutorials/LLM-2-API_SETUP.md
- Skill:      @project-query-setup help
```

---

## Verification — How to test it works

After deploying to a framework, run from any consuming project:

```bash
# 1. Check the skill is discoverable
@project-query-setup status

# Expected: reports key file status, API URL, auth status, project count

# 2. Full guided install (from scratch)
@project-query-setup install

# Expected: walks user through web UI → key creation → file → test → MCP register

# 3. OS-aware help
@project-query-setup help

# Expected: shows 5 tools + one OS-specific example

# 4. Direct MCP tool call from any skill
"Query the tools-project API for ticket TPR-T-12"
# Expected: agent calls get_ticket_info(ref="TPR-T-12") and returns status
```

---

## Summary — Files to create/modify

| Target | Action | File |
|--------|--------|------|
| `/mnt/work/Projects/.ai/skills/` | CREATE | `project-query-setup/skill.md` |
| `/mnt/work/Projects/.ai/skills/` | CREATE | `project-query-setup/reference.md` |
| `/mnt/work/Projects/.ai/skills/README.md` | ADD row | `project-query-setup` entry |
| `/mnt/work/Projects/.ai/.cursorrules` | ADD row | Skill table entry |
| `/mnt/work/Projects/.ai/skills/process-router/reference.md` | ADD rows | Routing entries |
| `/mnt/work/Projects/.ai/START_HERE.md` | ADD section | Integration prompt (§10 FAQ) |
| | | |
| `/mnt/work/Projects/.ai.ui/skills/` | CREATE | `project-query-setup/skill.md` |
| `/mnt/work/Projects/.ai.ui/skills/` | CREATE | `project-query-setup/reference.md` |
| `/mnt/work/Projects/.ai.ui/skills/README.md` | ADD row | `project-query-setup` entry |
| `/mnt/work/Projects/.ai.ui/.cursorrules` | ADD row | Skill table entry |
| `/mnt/work/Projects/.ai.ui/START_HERE.md` | ADD section | Integration prompt (§10 FAQ) |
| | | |
| `/mnt/work/Projects/.ai.biz/skills/` | CREATE | `project-query-setup/skill.md` |
| `/mnt/work/Projects/.ai.biz/skills/` | CREATE | `project-query-setup/reference.md` |
| `/mnt/work/Projects/.ai.biz/skills/README.md` | ADD row | `project-query-setup` entry |
| `/mnt/work/Projects/.ai.biz/.cursorrules` | ADD row | Skill table entry |
| `/mnt/work/Projects/.ai.biz/START_HERE.md` | ADD section | Integration prompt (§8 FAQ) |
| | | |
| `/mnt/work/Projects/.ai.soc/skills/` | CREATE | `project-query-setup/skill.md` |
| `/mnt/work/Projects/.ai.soc/skills/` | CREATE | `project-query-setup/reference.md` |
| `/mnt/work/Projects/.ai.soc/skills/README.md` | ADD row | `project-query-setup` entry |
| `/mnt/work/Projects/.ai.soc/.cursorrules` | ADD row | Skill table entry |
| `/mnt/work/Projects/.ai.soc/opencode.json` | ADD block | MCP server registration |
| `/mnt/work/Projects/.ai.soc/.opencode/mcp/` | CREATE + COPY | `mcp_server.py` |

**Total:** 4 new skill directories, 4 new skill.md+reference.md files, 4 README updates, 4 cursorrules updates, 1 opencode.json update, 4 START_HERE updates.

**Nothing is deleted or overwritten.** All changes are additive registration entries + new files.
