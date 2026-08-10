Here's the relationship, based on the docs (.work/docs/agent-query-api.md, @project-query-setup skill). There are two kinds of "communicate" — pick per case:                                                                                                                                                                                                                                                    

   Case A: another repo's coding agent should query tools-project (read-only)

   This is the standard, documented path — 3 steps on the consuming side:

   1. Get a key from the deployment's web UI: <deployment-url>/settings/api-keys → + New key → copy the tools_project_… key (shown once).
   2. Store it on the consuming machine in ~/.tools-project-key (chmod 600), with the deployment URL as the first line:
      ```bash
        printf 'BASE_URL=https://project.cloudsys.win\ntools_project_<key>\n' > ~/.tools-project-key
        chmod 600 ~/.tools-project-key
      ```
   3. Register the MCP server in the consuming project's agent config: copy mcp_server.py to .opencode/mcp/project-mcp/ there and add a tools-project entry to its opencode.json (or .cursor/mcp.json, .claude/mcp.json). That gives the agent 5 tools: list_projects, get_project_context, get_task_info, get_ticket_info, search_entities.

   The @project-query-setup install skill automates all of this (key guidance → key file → live connectivity test → MCP registration with a confirmation gate → verified checklist). That's the "proper" way — it refuses to claim "connected" without a live {"ok": true} response.

   Manual smoke test:

   ```bash
     curl -s -H "X-Api-Key: $(tail -n1 ~/.tools-project-key)" \
       https://project.cloudsys.win/v1/agent/projects
   ```

   (For project.cloudsys.win specifically: send a browser User-Agent or Cloudflare blocks the call with error 1010 — I hit that earlier today.)

   Access is read-only, scoped to the key owner's project memberships (or full read if the deployment admin set a shared AGENT_API_KEY).

   Case B: another application should integrate with the deployment (app-to-app)

   That's the ecosystem-hub layer (Mods 1–4, shipped 2026-07-06):

   • Identity: the satellite app calls GET /v1/platform/whoami with the user's key to resolve who/which companies.
   • Events: subscribe to HMAC-signed outbound webhooks via the admin endpoints (/v1/admin/webhooks — prospect won, client created, task done, ticket created/closed).
   • Cross-app linking: POST/GET/DELETE /v1/projects/{id}/external-refs to attach your app's objects to tools-project tasks/tickets.
   • Inbound automation: tools-project receives signed webhooks at POST /v1/integrations/rfp/award (that's the pattern to mirror for new inbound channels).

   Most of the time the answer is Case A: run @project-query-setup install from the other project and it walks you through it. Which scenario did you have in mind — a coding agent in another repo, or one of the satellite apps (CompanyBrain/OpsBoard/etc.)?                                                                                                                                                     