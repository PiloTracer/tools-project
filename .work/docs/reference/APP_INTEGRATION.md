# Application integration (Case B) — identity, events, links, inbound automation

**Status:** current (2026-10-30) — verified against the code on `main` (`main` = `789319c`); **not** the agent read-only surface.
**Audience:** another application (satellite app, bot, automation) integrating with a tools-project deployment.
**Auth model:** a mix of Bearer JWT (user actions), personal API keys (identity lookup), and HMAC-signed webhooks (machine-to-machine). Read the auth matrix before picking an endpoint.

> This page owns the **app-to-app** surface. For a coding agent that only reads projects/tickets, use
> [`../tutorials/LLM-2-API_SETUP.md`](../tutorials/LLM-2-API_SETUP.md) and
> [`../agent-query-api.md`](../agent-query-api.md). For repository/commit linking, use
> [`../tutorials/REPO_INTEGRATION.md`](../tutorials/REPO_INTEGRATION.md).

---

## 1. Capabilities at a glance

| Capability | Endpoint | Auth | Direction |
|------------|----------|------|-----------|
| Who is calling, and their companies | `GET /v1/platform/whoami` | personal API key **or** Bearer | app → API |
| React to project changes | `POST /v1/admin/webhook-subscriptions` | **superuser** Bearer | API → app |
| Attach your app's objects to a task/ticket | `/v1/projects/{id}/external-refs` | Bearer with project access | app → API |
| Push an award into CRM | `POST /v1/integrations/rfp/award` | `X-Webhook-Signature` (shared secret) | app → API |
| Read/write projects, tasks, tickets, activity | `/v1/...` | Bearer | app → API |

All bodies are JSON. Errors use FastAPI's `{"detail": …}` (string or list for 422 validation errors).

---

## 2. Authentication matrix

| Credential | Header | Used by | Notes |
|------------|--------|---------|-------|
| User session (JWT) | `Authorization: Bearer <token>` | whoami, external refs, subscriptions, CRUD | Obtained from `/v1/auth/local/login` or the deployment's OAuth flow |
| Personal API key | `X-Api-Key: tools_project_…` | whoami only (of the four integration surfaces) | Read-oriented; agent routes also accept it |
| Webhook secret | `X-Webhook-Signature: sha256=<hex>` | inbound RFP award | Env `RFP_WEBHOOK_SECRET`; validation uses constant-time compare |
| Subscription secret | generated per subscription | verifying **outbound** events | Returned **once** at creation as `hmac_secret` |

Two rules that bite:

- `get_current_user` (used by external refs, subscriptions, CRUD) **does not accept** `X-Api-Key`; pass a Bearer token.
- `/v1/admin/webhook-subscriptions` is **superuser-only**; a normal member gets `403`.

---

## 3. Identity — `GET /v1/platform/whoami`

Resolves the caller from a Bearer token **or** a personal API key (no superuser requirement).

```json
{
  "user": { "id": "uuid", "email": "user@example.com", "display_name": "Alice" },
  "companies": [ { "client_id": "uuid", "name": "Client Inc", "role": "contact" } ]
}
```

`companies` lists the client-contact links of that user (empty for staff-only accounts). Use it to
decide which client context your app should show; do not cache it beyond the session.

---

## 4. Events out — webhook subscriptions

### 4.1 Subscribe (superuser)

```http
POST /v1/admin/webhook-subscriptions
Authorization: Bearer <superuser token>

{ "url": "https://app.example/hooks/tools-project", "events": ["ticket.created", "prospect.won"], "label": "ops-bot" }
```

Response `201` includes `id`, `url`, `events`, `label`, `last_delivered_at` (null) and
**`hmac_secret`** (the full secret is returned only at creation — store it like a password; the list
endpoint returns a masked prefix plus `last_delivered_at`). List with `GET`, remove with `DELETE /v1/admin/webhook-subscriptions/{sub_id}` (`204`).

**Event names are not validated.** The list is stored as-is, so a typo (`ticket.created `, `ticket.create`)
silently never fires. Use exactly the names below.

### 4.2 Event catalogue (verified call sites)

| Event | Fires when | `data` fields | Tenant filter |
|-------|-----------|---------------|---------------|
| `ticket.created` | ticket created | `ticket_id, project_id, title, ref, status` | — (global) |
| `ticket.closed` | status transitions to `closed` | `ticket_id, project_id, title, ref` | — (global) |
| `task.done` | task transitions to `done` | `task_id, project_id, title, ref` | — (global) |
| `prospect.stage_changed` | pipeline stage changes | `prospect_id, company_name, from_stage, to_stage` | source tenant |
| `prospect.won` | prospect becomes `won` | `prospect_id, company_name` | source tenant |
| `client.created` | client created | `client_id, name` | source tenant |

### 4.3 Delivery contract

```json
{
  "event": "ticket.created",
  "timestamp": 1793484000.12,
  "data": { "ticket_id": "…", "project_id": "…", "title": "…", "ref": "PZT-T-2", "status": "open" },
  "tenant_id": "uuid-or-null",
  "tenant_slug": "pzt-or-null"
}
```

```
POST <your url>
Content-Type: application/json
User-Agent: tools-project-webhook/1.0
X-Webhook-Signature: sha256=<hex hmac of the raw request body, key = subscription hmac_secret>
```

- Timeout **10 s**; up to **3 attempts** with exponential backoff (2 s, 4 s). Non-2xx counts as a failure.
- Dispatch is **fire-and-forget** (background task): no retry queue, no dead-letter, no replay endpoint.
  `GET /v1/admin/webhook-subscriptions` exposes `last_delivered_at` (the only delivery evidence — there
  is no per-event delivery log); log every received event and every rejection on your side.
- The signature is computed over the **raw bytes**; verify before parsing.

```python
import hashlib, hmac

def verify(raw_body: bytes, signature_header: str, secret: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

### 4.4 Known limitations (multi-tenant)

`ticket.*` and `task.done` are dispatched **without a tenant id**, so in a multi-tenant deployment
they reach every subscription regardless of tenant (prospect/client events are tenant-filtered).
Treat those payloads as cross-tenant until the dispatch call sites pass `tenant_id`
(tracked in `UNKNOWNS.md`). Single-tenant deployments are unaffected.

---

## 5. Cross-app linking — external refs

Attach an object from your app (an invoice, a scan job, a document) to a tools-project task or ticket.

```http
POST /v1/projects/{project_id}/external-refs
Authorization: Bearer <token with project access>

{
  "source_app": "signflow",
  "external_id": "contract-8842",
  "external_url": "https://signflow.example/contracts/8842",
  "label": "Signed contract",
  "subject_type": "ticket",
  "subject_id": "<ticket uuid>"
}
```

- Returns the stored ref (`id, source_app, external_id, external_url, label, subject_type, subject_id, created_by`).
- Writes an **internal** `system` activity on the subject ("Linked external reference from …").
- `GET /v1/projects/{project_id}/external-refs` → `{ "items": [ … ] }`.
- `DELETE /v1/projects/{project_id}/external-refs/{ref_id}` → `204`.
- **Not deduplicated** — the same `(source_app, external_id)` posted twice creates two rows and two
  activity entries. `GET` first, or make your sender idempotent.

---

## 6. Inbound automation — `POST /v1/integrations/rfp/award`

The reference pattern for a machine pushing a win into the CRM.

```http
POST /v1/integrations/rfp/award
X-Webhook-Signature: sha256=<hmac of the raw body, key = RFP_WEBHOOK_SECRET>
X-Idempotency-Key: award-2026-0001          # optional but recommended

{
  "company_name": "Acme",
  "contact_email": "ops@acme.example",
  "contact_name": "Ana",
  "rfp_title": "Portal modernization",
  "rfp_url": "https://…/rfp/123"
}
```

Response `201`:

```json
{ "client_id": "…", "client_name": "Acme", "project_id": "…", "project_name": "…", "prospect_id": "…" }
```

Behaviour:

- Existing contact with a prospect → promotes it; otherwise creates a prospect (`source="rfp_webhook"`,
  stage `target`) and promotes it to `won`.
- Promotion creates the client if needed and scaffolds an onboarding project; the response returns both.
- `X-Idempotency-Key` is stored **in memory** for 24 h: replaying the same key + same payload returns
  the original result; the same key with a different payload returns `409`. It does **not** survive an
  API restart or span replicas — persist the key on your side.
- Missing/failed signature → `401` (`Webhook secret not configured`, `Missing X-Webhook-Signature header`,
  `Invalid signature`). `RFP_WEBHOOK_SECRET` must be set on the deployment.

---

## 7. Errors

| HTTP | When | Body |
|------|------|------|
| 401 | no/invalid credentials, bad webhook signature, secret not configured | `{"detail": "…"}` |
| 403 | non-superuser calling the admin subscription endpoints | `{"detail": "…"}` |
| 404 | unknown project/ref/subscription, **or no project access for external refs** (no existence leak) | `{"detail": "…"}` |
| 409 | idempotency key reused with a different payload | `{"detail": "Idempotency key already processed with different payload"}` |
| 422 | validation (missing field, bad enum, malformed email) | `{"detail": [ { "loc": …, "msg": … } ]}` |
| 5xx | server/edge failure | plain text or `{"detail": …}` — retry with backoff |

### 7.1 Reporting and correlation

Every response carries **`X-Request-Id`** (errors included). Log `status`, `X-Request-Id`, endpoint and
UTC time for every failure; quote the request id in support requests. Never log the API key or the
webhook secret — a short prefix is enough to identify the credential.

### 7.2 Retry guidance

| Result | Action |
|--------|--------|
| 401 / 403 | Do **not** retry — fix the credential, superuser flag, signature secret, or User-Agent |
| 404 | Do **not** retry blindly — verify ids and project access |
| 409 | Do **not** retry with the same `X-Idempotency-Key` and a changed payload — use a new key |
| 422 | Fix the payload; surface `detail[].msg` |
| 429 / 5xx / timeout | Retry with exponential backoff and jitter; give up after a few attempts and report with `X-Request-Id` |

**Webhook receivers:** return `2xx` quickly (the sender times out at 10 s), verify the signature
first, and treat duplicate `event` deliveries as possible (retries are at-least-once). Reject with
`4xx` only when the payload is truly invalid — the sender retries up to 3 times with backoff.

---

## 8. Verification checklist (do not skip)

1. `GET /v1/platform/whoami` with your credential returns **your** user + companies.
2. A test subscription created with a **public HTTPS** callback, then trigger a harmless event
   (e.g. create a ticket, close it) and confirm the `X-Webhook-Signature` verifies against the raw body.
3. Replay the RFP award with the same `X-Idempotency-Key` → identical `201` body, no duplicate client/project.
4. `GET /v1/projects/{id}/external-refs` after posting → exactly one row (you handled the no-dedup rule).
5. Rotate/delete the subscription and the secret when done.

---

## 9. Where to go deeper

| Need | Read |
|------|------|
| Full endpoint list for the deployed build | `GET /docs` / `GET /openapi.json` — authoritative |
| Curated REST map | [`API.md`](API.md) |
| Agent/read-only surface (projects, tickets, comments, attachments) | [`../agent-query-api.md`](../agent-query-api.md) |
| Commit linking + plan import | [`../tutorials/REPO_INTEGRATION.md`](../tutorials/REPO_INTEGRATION.md) |
| Which integration path to choose | [`../guides/quick-reference-to-connect-agent-with-tools-project.md`](../guides/quick-reference-to-connect-agent-with-tools-project.md) |
