# Tutorial: link a repository to tools-project (commits + plan sync)

**Scope:** Case C of the [integration chooser](../guides/quick-reference-to-connect-agent-with-tools-project.md) —
repository plumbing, not the agent connection. The agent key + MCP server are covered once in
[`LLM-2-API_SETUP.md`](LLM-2-API_SETUP.md); this page does not repeat them.

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

## 2. Local — key + MCP (one line, one link)

The key is per machine, not per repo. Set it up once with
[`LLM-2-API_SETUP.md`](LLM-2-API_SETUP.md) Parts A–C, then make sure the repository has a current
MCP copy:

```bash
grep -c 'User-Agent' .opencode/mcp/project-mcp/mcp_server.py    # must be >= 1
python3 .opencode/mcp/project-mcp/mcp_server.py --self-check    # 1.1.0: prints version + tools
```

Copy from `/mnt/work/Projects/tools-project/.opencode/mcp/project-mcp/mcp_server.py` (canonical:
Cloudflare-safe `User-Agent` + the 1.1.0 tools). A copy that predates the header fails every call
with `403 Error 1010` even though the MCP handshake looks healthy — `grep -c 'User-Agent'` first.

Verify the whole path once:

```bash
BASE=$(grep '^BASE_URL=' ~/.tools-project-key | cut -d= -f2-); BASE=${BASE:-http://localhost:8300}
curl -s -A "tools-project-mcp/1.1.0" \
  -H "X-Api-Key: $(tail -n1 ~/.tools-project-key)" \
  "$BASE/v1/agent/projects" | head -c 200
# {"ok":true,"data":[...]}
```

The agent then has `list_projects`, `get_project_context`, `get_task_info`, `get_ticket_info`,
`search_entities` (plus ticket detail/activity/attachment tools after 1.1.0). Give it the project
UUID from the settings URL. The MCP server is read-only.

## 3. Use it — commits that link back

Create the task/ticket first (auto-prefix gives it the ref), then use that ref.
Commit messages: `PZT-12: ...` or `PZT-T-4: ...`, pushed to the default branch.
The project polls, links the commit to the task/ticket, and the agent sees it in
`get_project_context` → `github_refs`, and (1.1.0) in `get_ticket_detail` → `linked_commits`
(`state: "resolved"` once synced, `"pending"` before).

## 4. Optional — sync a plan (milestones + tasks)

If the repo has a plan (e.g. `.work/plans/full/*-full-plan.md`), you can import its
milestones and tasks into tools-project in one transactional call. The MCP is
**not** used for this — plan sync goes through the REST API directly.

Prerequisites (local repo side):
- `opencode.json` → `skills.paths` includes `<AGENT_OS_SOURCE>/skills` (so `@plan-sync` resolves).
- A plan markdown file with milestone/task tables, readable in the repo.
- The API key + base URL already configured (`~/.tools-project-key`).
- The key's owner must be **superuser** (the agent gate) — a contributor-only account cannot use
  the agent surface today.

Run (inside the repo that owns the plan):

```text
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
| `403 Error 1010` (HTML) | MCP copy must send `User-Agent: tools-project-mcp/<version>` |
| Agent talks to the wrong instance | `API_BASE_URL` in the repo config overrides `BASE_URL` in the key file |
| Registry write fails | PAT needs **Contents: Read and write** |
| `403 superuser` | The key owner must be a superuser (see the reference §3) |
| Detail/attachment calls `404` | Deployment is still `1.0.0` — check `/openapi.json` `info.version` |

## Pizote

- Project: `19b24527-128d-4087-ac48-41979c619c11`
- Repo: `https://github.com/PiloTracer/pizote`
- Fix the key to `PZT`, link the repo, then commit `PZT-1: ...` on `main`.

See also: [`../agent-query-api.md`](../agent-query-api.md) (payloads),
[`LLM-2-API_SETUP.md`](LLM-2-API_SETUP.md) (connect), `FIRST_PROJECT.md` (creating a project).
