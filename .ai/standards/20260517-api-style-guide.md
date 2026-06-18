# API Style Guide — template

**Status:** Customize for your repo, then binding once HTTP APIs land.
**Pairs with:** CONVENTIONS, observability spec, FEATURE_STANDARD §6.

---

## 1. Base URL and versioning

| Env | Public API base |
|-----|-----------------|
| local-dev | `http://localhost:REPLACE:API_PORT/api/v1` |
| staging/prod | `https://REPLACE:API_HOST/api/v1` |

- Version in path only: `/api/v1/...`. Breaking changes require `/api/v2` and an ADR.

---

## 2. Authentication and tenant context

- Document auth mechanism (JWT, session cookie, API key, mTLS).
- Document how tenant or org context is resolved (claim, header, subdomain).
- Cross-tenant access → `403` unless explicitly designed otherwise.

**Common headers:**

| Header | Required | Notes |
|--------|----------|-------|
| `Authorization` | Per route | Bearer or scheme from security ADR |
| `X-Correlation-Id` | Optional | Server generates UUID if absent; echoed on response |
| `Idempotency-Key` | On mutating POST with side effects | UUID; define replay window in SPEC |

---

## 3. Resource naming

- Plural nouns, kebab-case: `/orders`, `/users/{id}/preferences`.
- Actions: `POST /resources/{id}:action` (colon suffix) when RPC-style actions are approved.
- Filters via query string, not new paths: `?status=active&from=...`.

**Identifiers:**

| Type | Format |
|------|--------|
| Internal id | UUID (default) |
| External id | Dedicated route segment; document format in SPEC |

---

## 4. Request and response bodies

- `application/json; charset=utf-8` unless file upload flow says otherwise.
- Field naming: `snake_case` or `camelCase` — pick one and match CONVENTIONS.
- Money: string decimal in JSON, never float.
- Timestamps: ISO-8601 with explicit timezone or `Z`.
- Reject unknown fields on input (`extra='forbid'` or equivalent).

**List envelope:**

```json
{
  "data": [],
  "meta": { "page": 1, "page_size": 50, "total_count": 0, "has_next": false }
}
```

Single-resource responses return the resource object directly.

---

## 5. Pagination

| Query | Default | Max |
|-------|---------|-----|
| `page` | 1 | — |
| `page_size` | 50 | 200 |

Optional cursor pagination for high-volume lists — document in SPEC.

---

## 6. Errors — RFC 7807 Problem Details

```json
{
  "type": "https://REPLACE:PROBLEM_BASE/problems/domain/code",
  "title": "Human-readable summary",
  "status": 409,
  "detail": "Safe detail for clients",
  "instance": "/api/v1/resources/uuid",
  "code": "StableMachineCode",
  "retryable": false,
  "errors": [{ "field": "name", "message": "..." }]
}
```

| Field | Required |
|-------|----------|
| `type` | Yes — stable URI |
| `title`, `status` | Yes |
| `code` | Yes — stable for clients |
| `retryable` | Yes for 429/503 |

---

## 7. OpenAPI

- Single source of truth under `REPLACE:OPENAPI_PATH` or generated from code — pick one approach in ADR.
- Every public route documented before merge to main.

---

## 8. Webhooks and callbacks

- Unauthenticated callbacks validate via signed token, mTLS, or allow-listed source IPs — document in SPEC.
- Idempotent processing with dedupe store.

---

## 9. Rate limiting

- Return `429` with `Retry-After` when limited.
- Document limits per tenant and per route class.
