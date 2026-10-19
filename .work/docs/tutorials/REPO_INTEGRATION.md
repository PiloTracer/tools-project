# Quick tutorial: connect a local repo to tools-project

Two independent pieces. Do both for full integration.

## 1. Server — link the GitHub repo

Open `https://project.cloudsys.win/projects/<project-uuid>/settings`.

1. **Project key** → UPPERCASE (`PZT`, not `pzt`) → **Save settings**.
   Refs are `PZT-123` (task) and `PZT-T-12` (ticket); lowercase refs never link.
2. Create a GitHub PAT:
   - Classic: `repo` scope.
   - Fine-grained: repo access + **Contents: Read** (commit sync) or
     **Contents: Read and write** (task registry) + Metadata: Read.
3. **GitHub Repositories** → `https://github.com/<owner>/<repo>` + PAT →
   **Link repository**. Initial sync starts immediately.
4. Back in **Settings**, enable **GitHub task registry** and
   **Auto-prefix task/ticket refs** → **Save settings**.
   Link the repo first; enabling the registry before a link returns HTTP 400.
5. Verify: **Commit Association Readiness** = 5/5; the **GitHub** tab shows
   commits; **Activity** shows commit cards.

Commits must reach the repo's **default branch** — the sync reads only that branch.
Poll is 300 s by default; use **Sync now** or **Re-sync last N days**.

## 2. Local — one global key + MCP

The key is per machine, not per repo. Configure once; every repo reuses it.

Create a key at `https://project.cloudsys.win/settings/api-keys` → **+ New key** →
copy the `tools_project_...` value (shown once). The account must be a superuser.

```bash
printf 'BASE_URL=https://project.cloudsys.win\ntools_project_<key>\n' > ~/.tools-project-key
chmod 600 ~/.tools-project-key
```

Copy the MCP server into the repo (use this copy — the older tools-project copy
lacks the Cloudflare-safe User-Agent):

```bash
mkdir -p .opencode/mcp/project-mcp
cp /mnt/work/Projects/pizote/.opencode/mcp/project-mcp/mcp_server.py \
   .opencode/mcp/project-mcp/
```

Register it.

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

No key goes in these files — the server reads `~/.tools-project-key`.

Verify:

```bash
curl -s -A "tools-project-mcp/1.0" \
  -H "X-Api-Key: $(tail -n1 ~/.tools-project-key)" \
  https://project.cloudsys.win/v1/agent/projects
# {"ok":true,"data":[...]}
```

The agent then has `list_projects`, `get_project_context`, `get_task_info`,
`get_ticket_info`, `search_entities`. Give it the project UUID from the settings
URL. The MCP server is read-only.

## 3. Use it

Create the task/ticket first (auto-prefix gives it the ref), then use that ref.
Commit messages: `PZT-12: ...` or `PZT-T-4: ...`, pushed to the default branch.
The project polls, links the commit to the task/ticket, and the agent sees it in
`get_project_context` → `github_refs`.

## 4. Optional — sync a plan (milestones + tasks)

If the repo has a plan (e.g. `.work/plans/full/*-full-plan.md`), you can import its
milestones and tasks into tools-project in one transactional call. The MCP is
**not** used for this — plan sync goes through the REST API directly.

Prerequisites (local repo side):
- `opencode.json` → `skills.paths` includes `<AGENT_OS_SOURCE>/skills` (so `@plan-sync` resolves).
- A plan markdown file with milestone/task tables, readable in the repo.
- The API key + base URL already configured (`~/.tools-project-key`).
- The key's owner must be **contributor or higher** on the target project.

Run (inside the repo that owns the plan):

```bash
@plan-sync dry-run - .work/plans/full/<plan>.md --project <UUID-or-slug-or-key>
# → parses plan → builds manifest → shows diff preview → asks for confirmation

@plan-sync sync - .work/plans/full/<plan>.md --project <UUID-or-slug-or-key>
# → same, then commits after you confirm
```

- `--project` accepts UUID, slug, or project key. Omit it and the skill resolves via
  `GET /v1/agent/projects` and asks you to confirm before any write.
- Dry-run never writes. No confirmation = stops at preview.
- The plan file is never modified (one-way sync).
- Imported tasks get **allocated** refs from the project's counter (`PZT-1`, …),
  not the plan's own IDs. Use those allocated refs in commit messages.
- Imported tasks receive `milestone_id`, `plan_ref`, `plan_state` for filtering.

The GitHub PAT is not involved — plan-import authenticates with the personal API key.

## Gotchas

| Symptom | Fix |
|---|---|
| Refs never link | Project key must be UPPERCASE (`pzt` → `PZT`) |
| Commit not synced | It is not on the default branch |
| `403 Error 1010` | MCP server must send `User-Agent: tools-project-mcp/1.0` |
| opencode ignores env | Field is `environment`, not `env` |
| Registry write fails | PAT needs **Contents: Read and write** |
| `403 superuser` | API key owner must be a superuser |

## Pizote

- Project: `19b24527-128d-4087-ac48-41979c619c11`
- Repo: `https://github.com/PiloTracer/pizote`
- Fix the key to `PZT`, link the repo, then commit `PZT-1: ...` on `main`.

See also: `../agent-query-api.md` (payloads) and `FIRST_PROJECT.md` (creating a project).
