# Agent Ticket Context & Attachments — amendment 01 verification

**Status:** Verified; corrections applied to the amendment (2026-10-30)
**Reviewed path:** [`20261030-SPEC-amendment-01.md`](20261030-SPEC-amendment-01.md) (Draft at review; **Approved 2026-10-30**)
**Base SPEC:** [`20260701-SPEC.md`](20260701-SPEC.md) (Approved — not edited)
**Method:** full code read at `HEAD 9d9e53d` + live probes against the deployed API (`https://project.cloudsys.win`, OpenAPI `info.version = 0.1.3`) with the personal key from `~/.tools-project-key` (value never printed) + end-to-end JSON-RPC probes of the MCP servers in the four local consuming repos.
**Decisions:** **D1 and D3 approved 2026-10-30**; **D2 approved in principle** — the protected-file edit needs explicit in-message approval at implementation, otherwise `web_url = null`.

> Evidence rule: every "confirmed" line below cites a file path or a live command result. Statements that could not be verified are labelled **Unverified**.

---

## 1. Verdict

**`needs-revision` → revised.** The direction is correct and matches the code: the four missing capabilities (ticket detail, activity read, binary attachment read, capability handshake) are genuinely absent, the defect in the context counts is real, and the design reuses existing models without a migration. Four findings would have blocked or regressed implementation and are corrected in the amendment:

| Severity | Id | Finding |
|----------|----|---------|
| **Blocker** | F1 | The canonical MCP server in this repo has no `User-Agent`; against the hosted API it returns **HTTP 403 (Cloudflare 1010)** on every tool call. R10's "refresh the copy" would have regressed the consumers that already carry the fix. |
| **Blocker** | F2 | R10's "serve the canonical file from the deployed API" is **not buildable** with the current `./api` Docker build context, and test #20 cannot run in-container as written. |
| **Major** | F3 | R2/R3/R6/R7 model client-participant access as "project access + internal-note filter". The shipped visibility rule also limits task/ticket activity to subjects assigned to the participant's company; without it, relaxing Q1 later leaks tickets, comments and attachments. |
| **Major** | F4 | `download_url`/`web_url` need a public base URL; the API has no such setting and `PUBLIC_ORIGIN` is only on the web service. The plan lists the settings but not the (protected) env wiring or the proxy-header caveat. |

Six further major findings (F5–F10) and ten minor findings (F11–F20) are listed in §3; each has a matching correction in the amendment's §16 change log.

---

## 2. Evidence — live probes (2026-10-30, deployed `0.1.3`)

All calls used `X-Api-Key` from `~/.tools-project-key` and `User-Agent: tools-project-mcp/1.0` unless stated.

| # | Probe | Result | Confirms |
|---|-------|--------|----------|
| 1 | `GET /openapi.json` | 200 — `info.version = 0.1.3`; agent paths: `/v1/agent/{projects,projects/{id}/context,search,tasks,tickets}` only | Detail/activities/capabilities/MCP-file routes are absent on the deployment |
| 2 | `GET /v1/agent/projects` | 200 — Pizote `open_tasks 1 / open_tickets 4 / member_count 3` | Counts are computable and correct on the list route |
| 3 | `GET /v1/agent/projects/19b24527-…/context` | 200 — `project.open_tasks/open_tickets/member_count = 0/0/0`; `members` 3, `tasks` 1, `tickets` 4 | R11 defect is real and reproduced |
| 4 | `GET /v1/agent/tickets/PZT-T-1` | **404** | R1/R3 absent |
| 5 | `GET /v1/agent/capabilities` | **404** | R8 absent |
| 6 | `GET /v1/attachments/54830228-…` | **401** | R7 absent; JWT-only route |
| 7 | `GET /api/attachments/54830228-…` (web proxy) | **401** | Description image links need a browser session |
| 8 | `GET /v1/projects/19b24527-…/activities` | **401** | R6 absent; JWT-only route |
| 9 | `GET /projects/19b24527-…/tickets/8fb47f08-…` (web URL) | **307 → `/login?next=…`** even with a key | A pasted ticket URL is not machine-readable |
| 10 | Ticket descriptions | Exactly `![Screenshot ….png](/api/attachments/<uuid>)`, 3 tickets, 3 distinct ids | R4 pattern matches real data |
| 11 | `python3` default urllib `User-Agent` → `/v1/agent/projects` | **403** `{"title":"Error 1010: Access denied"…}` | F1 |
| 12 | Same call with `User-Agent: tools-project-mcp/1.0` | 200, 3 254 bytes | F1 fix is a header |
| 13 | `get_ticket_info(ref=PZT-T-1)` through Pizote's MCP copy | `ok: true`, 754-byte payload: no `web_url`, no attachments, no comments | Local repo reads the ticket summary only |

**Not verified (by design of the current system):** comment bodies on Pizote tickets — no agent route exists and the web route needs a session. The amendment's test #7/#8 and the post-deploy acceptance cover this.

---

## 3. Findings and corrections

### F1 — Blocker: canonical MCP copy is broken against the hosted API

- `tools-project/.opencode/mcp/project-mcp/mcp_server.py:143-148` sends only `Accept` — no `User-Agent`.
- `pizote/…/mcp_server.py` and `opportunity-radar/…/mcp_server.py` add `User-Agent: tools-project-mcp/1.0`; `pilo.ai.logicbison/…` adds it via `MCP_USER_AGENT`.
- Live: default UA → **403 Cloudflare 1010**; custom UA → 200. `REPO_INTEGRATION.md:44` already tells operators to copy from **pizote** because "the older tools-project copy lacks the Cloudflare-safe User-Agent" — a documented workaround for an upstream defect.
- Consequence for the amendment: R10.1 "served file must be byte-identical to the repo copy" + rollout "refresh the MCP copy in Pizote" would overwrite a working consumer file with a 403-producing one.
- **Correction (C1, C18):** the canonical MCP source must send `User-Agent` (env-overridable `MCP_USER_AGENT`, default `tools-project-mcp/<SERVER_VERSION>`); P0 starts with this fix; tests assert the header; acceptance asserts a served/downloaded copy works against the hosted API.

### F2 — Blocker: R10's file-serving endpoint is not buildable as written

- `docker-compose.dev.yml:47` and `docker-compose.prd.yml:37` build with `context: ./api`; `api/Dockerfile.dev:17` and `api/Dockerfile.prd:11` copy only `app`. The dev API container mounts `./api:/app` and `./sql:/sql:ro` — **no** `.opencode` mount.
- Therefore the API cannot read `.opencode/mcp/project-mcp/mcp_server.py` at runtime, and `api/tests/` cannot compare served bytes with the repo copy (test #20 in the original plan; now #22).
- **Correction (C2, C9):** move the canonical MCP server into the API package (`api/app/client/mcp_server.py`), which is inside the image; keep `.opencode/mcp/project-mcp/mcp_server.py` as the consumer copy refreshed from the served endpoint; test #20 compares served bytes with the packaged module. Fallback if the owner rejects the new location: keep copy-from-repo and drop the endpoint + test #20.

### F3 — Major: client-participant visibility is under-specified (future leak)

- `api/app/routers/activities.py:243-262` (list) applies, for client participants: `is_internal = false` **and** `client_activity_condition(db, acc, project_id)` — project-wide entries plus task/ticket entries for subjects assigned to their company.
- `api/app/routers/tickets.py:78-80` limits ticket lists to `assignee_id in client_company_user_ids(...)`; `project_access.can_view_tickets` gates the feature.
- `require_project_access` returns a superuser as `owner` for **any** project (`services/project_access.py:70-72`), so today — behind `_require_agent_superuser` — the project check is a no-op and the new endpoints look safe. The moment Q1 relaxes the gate, R2/R3/R6/R7 as written leak tickets, comments and attachments to client participants.
- **Correction (C3, C5, C6, C7):** every new route reuses the *same* predicates as the web routes: `can_view_tickets`, `client_company_user_ids`, `client_activity_condition`, `_assert_attachment_visible`; tests cover a client participant whose key has project access but not the subject.

### F4 — Major: absolute URLs have no plumbing

- `api/app/config.py` has `public_host` only; no `public_api_base_url` / `public_web_base_url`. `PUBLIC_ORIGIN` is passed to the **web** service only (`docker-compose.prd.yml:100`, `docker-compose.dev.yml:122`).
- Uvicorn runs without explicit `--proxy-headers`/`FORWARDED_ALLOW_IPS` (`api/Dockerfile.prd:31`), so behind Caddy `request.base_url` may report `http://` — **Unverified** on the exact deployment, but not safe to rely on.
- **Correction (C4):** add optional `PUBLIC_API_BASE_URL` / `PUBLIC_WEB_BASE_URL` settings (default empty); derive from `X-Forwarded-Proto`/`Host` then `request.base_url` when unset; `web_url = null` when no web base is configured (never emit a guess). Wiring them in compose + `.env.example` (and the secret `.env.prd`) is a protected-file change → owner approval **D2**.

### F5 — Major: the `{"ok": false, "error": …}` error body is not what FastAPI emits

- `HTTPException(404, detail=…)` produces `{"detail": …}`, which is what every existing route returns (`agent_query.py:261`, `attachments.py:268`).
- **Correction (C13):** 4xx responses use the standard `{"detail": "<stable_code>"}` (`ticket_not_found`, `attachment_not_found`, `internal_activities_forbidden`); success keeps `{"ok": true, "data": …}`. §8 updated to the real shape.

### F6 — Major: payload vocabulary conflicts with shipped endpoints

- `tickets.description` is the column (`api/app/models/ticket.py:31`); the list/context payloads expose `description` (`agent_query.py:176-189`) and `I8` requires them unchanged. R3 invented `description_markdown` for the same field, and the PII rule mentions a ticket `created_by` that does not exist (only `attachments.created_by`).
- **Correction (C5):** detail uses `description` (verbatim) + additive `description_resolved`; `created_by` removed from the ticket field list.

### F7 — Major: query budget is not achievable

- Budget in R16 "≤7 queries". A correct detail needs: ticket+project, attachments, activities page, activities count, activity attachments, linked commits, watchers, actor/reporter/assignee users — **8** with activities, **6** without. `Activity.actor` is `lazy="joined"` (`models/activity.py:39`), so actors are free.
- **Correction (C14):** ≤8 with activities, ≤6 without; activities page ≤3 (items, attachment batch, count).

### F8 — Major: cross-repo deliverable not declared

- R10.2 changes `project-query-setup`, which lives in `/mnt/work/Projects/pilo.ai.logicbison/skills/project-query-setup/` — a **different repository**. The amendment presents it as part of this repo's work.
- The skill also has a broken verification line: Branch C runs `python3 -c "… open('${path}') …"` where `path` is a *Python* variable, so the shell substitutes an empty string (`skill.md` Branch C, `print('${path}: valid')`).
- **Correction (C9, C17):** list the skill change as an external deliverable with owner approval + its own commit; fix the `${path}` verification bug in the same change.

### F9 — Minor/major: capabilities semantics

- `limits.inline_image_max_bytes` is an **MCP client** setting (`TOOLS_PROJECT_INLINE_IMAGE_MAX_BYTES`), not a server limit; `mcp_server.version` cannot describe the caller's copy.
- "The MCP server calls it at startup" would add a blocking network call before `initialize` and fail when the API is down; `initialize.serverInfo.version` is hard-coded `"1.0.0"` (`mcp_server.py:217`).
- **Correction (C7, C8):** capabilities returns server limits + `recommended_mcp_server_version` + `mcp_server_download_url`; the client probes lazily with a timeout, caches the result, never blocks `initialize`, hides newer tools on an older API; `SERVER_VERSION` is the single source for `serverInfo.version`.

### F10 — Minor: ETag is undecided and conflicts with the rest of R7

- R7 offers sha256 **or** `storage_key-size` and says "pick one and test it". A sha256 requires buffering the file (contradicting "no request holds more than one file buffer", R16) or reading twice; `Cache-Control: no-store` makes validators nearly useless.
- **Correction (C6):** no `ETag` in 1.1.0; `Content-Length` from disk (`FileResponse`), `Cache-Control: private, max-age=0, no-store`, `X-Content-Type-Options: nosniff`, `CSP: sandbox`, `Referrer-Policy: no-referrer`; `?download=1` → `attachment`.

### F11 — Minor: counts shape / truncation

- Context truncation flags are proposed at project-object level but not specified as a shape; attachments (R16) can be capped at 200 without telling the caller.
- **Correction (C4, C10, C12):** context `project` gains `open_tasks, open_tickets, member_count, tasks_total, tickets_total, tasks_truncated, tickets_truncated`; detail `counts.attachments` is the true total and `attachments_truncated` is explicit.

### F12 — Minor: test plan defects

- Test #16 hard-codes `1/4/3` (Pizote data) — a fresh test DB has none of it; the test must create 3 members / 1 open task / 4 tickets.
- Test #20 (served == repo) is impossible in-container (F2); renumbered #22 in the corrected plan.
- Missing: UA header (F1), capabilities auth matrix, `include_activities=false`, `order=asc`, `storage_key` never serialized (I2), byte-identical description (I6), MCP image fallback > cap, `save_dir` traversal, MCP degrades on old API without a crash.
- **Correction (C15):** rewritten §11.

### F13 — Minor: R21 docs scope is too narrow, and the existing docs are wrong today

False or stale statements found in the **pre-rewrite revision** (line numbers refer to that revision; all are corrected in the current docs):

| Doc | Line | Statement | Reality |
|-----|------|-----------|---------|
| `agent-query-api.md` | 88, 104 | "permissions are scoped to your project memberships" | `_require_agent_superuser` rejects non-superusers; superusers bypass membership |
| `agent-query-api.md` | 241-265 | register with env `AGENT_API_KEY`, "server reads `AGENT_API_KEY`" | personal key file is the primary path; env is optional |
| `agent-query-api.md` | 478 | "The MCP server only connects to localhost" | `BASE_URL`/`API_BASE_URL` support remote |
| `agent-query-api.md` | 3 | "Version 1.0.0" | no agent-version concept exists in code yet |
| `quick-reference-to-connect-agent-with-tools-project.md` | 1-37 | pasted chat transcript ("I hit that earlier today", "Which scenario did you have in mind?") | not a guide |
| `REPO_INTEGRATION.md` | 42-48 | copy the MCP server from **pizote** | workaround for F1; must point at the canonical source |
| `LLM-2-API_SETUP.md` | 27-30, 131+ | implies key page always available, no version/refresh step | needs refresh/update steps + Cloudflare note |

- **Correction (C16, C17):** R21 expanded to the doc set; `quick-reference` rewritten as a decision guide; the setup tutorial and repo-integration doc de-duplicated and corrected; stale vendored skill copies marked historical.

### F14 — Minor: rollout order

- P0 as written refreshes the Pizote copy (regression, F1) and defers docs to P2 although consumers need the connection/refresh instructions at P0.
- **Correction (C18):** P0 = UA fix → detail + attachment + MCP tools + docs for what ships; P1 = activities; P2 = capabilities, counts, project_id, index, distribution.

### F15 — Info: Q6 is already satisfied

- `Settings.attachment_retention_days = 0` (never purge) by default (`api/app/config.py:64`) and `.env.dev` ships `0`. No change is required; keep 0 and add the operational note only.

### F16 — Info: the base SPEC is stale against the code

- `20260701-SPEC.md` §R2 allows only `AGENT_API_KEY`; the code accepts personal keys and keeps a superuser gate (`deps.py:259-330`, `agent_query.py:28-43`). §7 says "connects to localhost only"; §8 says `"Invalid agent API key"`.
- Approved SPECs are immutable; the amendment records the deltas and marks the base sections superseded. **Correction (C11):** explicit "supersedes" note rather than an unstated contradiction.

### F17 — Minor: inline activity page order is unspecified

- R3 says "first activity page" and R6 defaults to `desc`; a reader cannot tell what "first" means.
- **Correction (C5):** inline page is newest-first (`desc`, maximum 50 by default, capped 200), `next_offset` pages backwards; chronological reading uses the activities route with `order=asc`.

### F18 — Minor: MCP attachment handler details

- Text inline cap, image mime check, non-POSIX cache dir, and "never outside the dir" need explicit rules; `size_bytes` must come from the response, not the metadata block.
- **Correction (C8):** `TOOLS_PROJECT_INLINE_TEXT_MAX_BYTES` (default 1 MiB), image inline only when `mime` starts with `image/`, `Path(tempfile.gettempdir())/"tools-project"` fallback, `O_NOFOLLOW`-style checks, sha256 of saved bytes returned.

### F19 — Minor: acceptance commands

- R22 checks `jq` (not guaranteed on consumer machines), never proves comments or `web_url`, and runs the repo copy rather than the distributed copy.
- **Correction (C19):** python3 one-liners, add a comment assertion, a `web_url` assertion, and a self-check of the **downloaded** MCP file.

### F20 — Minor: R16 "≤200 attachments per response" contradicts "ticket detail returns attachments"

- **Correction (C12):** cap 200 + `attachments_truncated` + true `counts.attachments`; description references are never truncated silently (the first 200 include all description-referenced files by ordering rule R5).

---

## 4. Local consumer matrix (verified 2026-10-30)

| Repo | MCP copy | Version | Auth/URL resolution | Ticket list | Ticket detail | Comments | Images | Launch |
|------|----------|---------|---------------------|-------------|---------------|----------|--------|--------|
| `pizote` | `pizote/.opencode/mcp/project-mcp/mcp_server.py` | 1.0.0 | key file → remote | **works** (`get_ticket_info` 200) | absent | absent | absent (401) | ok |
| `opportunity-radar` | same file (md5 equal to pizote) | 1.0.0 | key file → remote | works* | absent | absent | absent | ok |
| `tools-project` | canonical copy — **no UA** | 1.0.0 | key file → remote unless `API_BASE_URL` set | **403 Cloudflare** | absent | absent | absent | starts, fails per call |
| `pilo.ai.logicbison` | copy with `MCP_USER_AGENT` | 1.0.0 | key file → remote | n/a | absent | absent | absent | **`python` not found** (`opencode.json` uses `python`) |

\* MCP handshake only verified for pizote; opportunity-radar's file is byte-identical, so the same handler runs.

**Answer to "can my local repos read a ticket's URL, comments and images today?"** No. They can list a ticket and read its title/description (and the description's image links are dead for the key). There is no route, no tool, and no URL that returns the comment thread or the bytes.

---

## 5. What the verification did **not** change (and why)

- **Read-only, additive surface** — the API key cannot write; `last_used_at` is the only write on a read path (`deps.py:316-317`). Approval stands.
- **Existing five endpoints unchanged** (`I8`) — the amendment's context additions are additive fields; verified against `agent_query.py`.
- **No new tables, one index** — `attachments.ticket_id/activity_id` are already indexed (`sql/schema_indexes.sql:54-58`); `R20`'s composite index is additive and idempotent.
- **Gate kept for 1.1.0 (Q1)** — the superuser gate is real and documented; the docs are corrected instead of the gate.
- **Q2 (no signed URLs)** — no new secret surface; key auth is auditable. Keep.
- **Q6** — retention is already `0` (never purge). Keep and document.

---

## 6. Owner decisions

| Id | Decision | Recommendation | Impact if declined |
|----|----------|----------------|--------------------|
| **D1** | R10 distribution: move the canonical MCP server into `api/app/client/mcp_server.py` and serve it, keeping `.opencode/…` as a refreshed consumer copy | **Approve** — only approach that fits `context: ./api` and keeps a byte-identity test | Keep copy-from-repo, drop the endpoint + test #20, document the path (consumers outside this machine keep manual copies) |
| **D2** | Protected files: add `PUBLIC_API_BASE_URL` / `PUBLIC_WEB_BASE_URL` to `docker-compose.{dev,prd}.yml`, `.env.example` (and the secret `.env.prd`) | **Approve** — otherwise `web_url` is omitted and API URLs rely on proxy headers | `web_url = null`; `download_url` falls back to request headers (works behind Caddy, unverified in dev-proxy) |
| **D3** | Q1 gate: keep `_require_agent_superuser` for 1.1.0 and fix the docs | **Approve** — membership-scoped keys are a 1.2.0 change with their own tests | Relaxing now requires the F3 predicates first, or data leaks |

D1 and D3 are decided in the amendment's §13/§16 (2026-10-30); D2 remains an edit-time approval.
