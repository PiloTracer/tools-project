# Connect another system to tools-project — which path?

**Status:** current (2026-10-30) — `1.0.0` verified live; the `1.1.0` tools are implemented and pending deployment
**Purpose:** pick the right integration path in one minute, then follow the linked walkthrough.
This guide does **not** repeat the steps — one home per fact (see the map at the end).

---

## 1. Pick your case

| You want… | Case | Credential | Start with |
|-----------|------|------------|------------|
| A coding agent in another repository to **read** projects, tasks, tickets, commits, and (1.1.0) comments + screenshots | **A — agent query** | personal `tools_project_…` API key | [`tutorials/LLM-2-API_SETUP.md`](../tutorials/LLM-2-API_SETUP.md) |
| Another **application** to identify users, receive events, link its objects, or push data into tools-project | **B — app-to-app** | user JWT / webhook secret | §3 below |
| A repository to **link commits** to tasks/tickets and import a plan | **C — repo/plan sync** | personal API key + GitHub PAT | [`tutorials/REPO_INTEGRATION.md`](../tutorials/REPO_INTEGRATION.md) |

Most requests are **Case A**. Case B is for satellite apps (CompanyBrain, OpsBoard, SignFlow,
LedgerLite); Case C is repo plumbing, not an agent capability.

---

## 2. Case A — a coding agent reads tools-project

**Three things happen, once per machine:**

1. **Key** — web UI → **Settings → API Keys** → *+ New key* (shown once, starts with `tools_project_`).
   The owner must be a **superuser**; agent routes reject non-superuser keys with `403`.
2. **Key file** — `~/.tools-project-key` (`chmod 600`), with `BASE_URL=…` as the first line for a
   remote instance. No key is stored in the repository or in `opencode.json`.
3. **MCP registration** — copy the MCP server into the repo (`.opencode/mcp/project-mcp/`) and
   register `python3 .opencode/mcp/project-mcp/mcp_server.py` in the agent config.

**What the agent can then do** (5 tools today, 8 after `agent_api_version 1.1.0`):

| Today | After 1.1.0 |
|-------|-------------|
| list projects · project context · list tasks · list tickets · unified search | + ticket detail by UUID/**ref** · comment/activity thread · attachment bytes (screenshots, PDFs) |

**Three things that bite** (all covered in the tutorial's troubleshooting):

- The hosted deployment is behind Cloudflare: a request without a non-default `User-Agent` gets
  `403 Error 1010`, while the MCP handshake still looks healthy.
- `API_BASE_URL` in an agent config **overrides** the key file's `BASE_URL`. Pin it only if every
  user of that repo should hit the same instance.
- A stale MCP copy can look connected and still fail every call. Run
  `python3 .opencode/mcp/project-mcp/mcp_server.py --self-check` after any refresh.

**Proof of connection** (never claim "connected" without it):

```bash
BASE=$(grep '^BASE_URL=' ~/.tools-project-key | cut -d= -f2-); BASE=${BASE:-http://localhost:8300}
KEY=$(tail -n1 ~/.tools-project-key)
curl -s -H "X-Api-Key: $KEY" -H "User-Agent: tools-project-mcp/1.1.0" "$BASE/v1/agent/projects" \
  | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["data"]), "projects")'
```

Expected: `N projects` and `"ok": true`. Contract and payloads:
[`../agent-query-api.md`](../agent-query-api.md).

---

## 3. Case B — an application integrates with tools-project

Four independent capabilities (mix as needed). All verified against the code on 2026-10-30.

| Capability | Endpoint | Auth | Notes |
|------------|----------|------|-------|
| **Identity** — who is calling, and which client companies they belong to | `GET /v1/platform/whoami` | personal API key or Bearer | Returns the user + linked companies; the same `require_agent_or_user` as the agent routes |
| **Events out** — react to prospect/client/task/ticket changes | subscribe via `POST /v1/admin/webhook-subscriptions` | superuser JWT | Payloads are HMAC-SHA256 signed: `X-Webhook-Signature: sha256=<hex>`. Events: `prospect.won`, `prospect.stage_changed`, `client.created`, `task.done`, `ticket.created`, `ticket.closed`. List/delete: `GET`/`DELETE` the same route |
| **Cross-app linking** — attach your app's objects to a task/ticket | `POST`/`GET /v1/projects/{id}/external-refs`, `DELETE /v1/projects/{id}/external-refs/{ref_id}` | Bearer | Stored as commit-subject refs with `source_app`/`external_id`/`external_url`; each POST also writes an internal system activity |
| **Inbound automation** — push an award into tools-project | `POST /v1/integrations/rfp/award` | `X-RFP-Signature` (shared secret) | The reference implementation for a new inbound channel |

Rules that matter:

- Webhook-subscription endpoints are **superuser** (`/v1/admin/...`) — a personal agent key is
  read-only and cannot subscribe.
- Verify the signature over the **raw body** before parsing; reject unknown events rather than
  guessing.
- External refs are **not** deduplicated server-side: `GET` first and skip a `POST` whose
  `(source_app, external_id)` already exists, or a retry creates a second row and a second
  internal activity entry.

Environment: `RFP_WEBHOOK_SECRET` (inbound), per-subscription `hmac_secret` (outbound).

---

## 4. Case C — link a repository and sync a plan

Not an agent feature; it uses the same personal key:

- Link the GitHub repo, set the project key (`PZT`), enable the task registry → commits become
  linked to tasks/tickets and visible in the activity feed.
- Import a plan (milestones + tasks) with `@plan-sync sync - <plan> --project <uuid>` — direct REST,
  **not** MCP; the MCP stays read-only.

Walkthrough and gotchas: [`tutorials/REPO_INTEGRATION.md`](../tutorials/REPO_INTEGRATION.md).

---

## 5. Doc map (one home per fact)

| Question | Read |
|----------|------|
| How do I connect, step by step? | [`tutorials/LLM-2-API_SETUP.md`](../tutorials/LLM-2-API_SETUP.md) |
| What exactly does each endpoint or MCP tool return? | [`agent-query-api.md`](../agent-query-api.md) |
| How do I read a ticket with its comments and screenshots? | [`tutorials/AGENT_TICKET_CONTEXT.md`](../tutorials/AGENT_TICKET_CONTEXT.md) (**1.1.0**) |
| How do I link commits / import a plan? | [`tutorials/REPO_INTEGRATION.md`](../tutorials/REPO_INTEGRATION.md) |
| Which integration path do I choose? | This file |
| What is *planned* vs *live*? | [`agent-query-api.md` §1](../agent-query-api.md#1-what-you-get) |

Do not add a new "how to connect" page — extend the two that already own it.
