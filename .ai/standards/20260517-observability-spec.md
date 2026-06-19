# Observability Specification — template

**Status:** Customize for your repo before production traffic.
**Pairs with:** CONVENTIONS, api-style-guide, data-classification.

---

## 1. Principles

- Every request and background job has a **correlation id** propagated across services.
- Metrics use a consistent prefix: `REPLACE:METRIC_PREFIX_` (e.g. `myapp_`).
- No PII or credentials in logs, metrics labels, or span attributes.

---

## 2. Metrics naming

| Pattern | Type | Example |
|---------|------|---------|
| `{prefix}http_request_total` | Counter | `method`, `route`, `status_class` |
| `{prefix}http_request_seconds` | Histogram | `method`, `route` |
| `{prefix}job_total` | Counter | `job_name`, `result` |
| `{prefix}job_seconds` | Histogram | `job_name` |

Add domain counters in feature SPECs §9; register them here when merged.

---

## 3. Tracing

- W3C `traceparent` (or your mesh default) on HTTP and message boundaries.
- Span names: `HTTP <method> <route template>` — not raw URLs with ids.

---

## 4. Logging

- Structured JSON (or your platform standard).
- Required fields: `timestamp`, `level`, `message`, `correlation_id`, `service`.
- Error logs include `exception.type` and stack in non-production or hashed in production per policy.

---

## 5. Dashboards and alerts

| Signal | Starter alert |
|--------|----------------|
| Error rate 5xx | > threshold for 5m → page |
| Job failure rate | > 0 for 15m → ticket |
| Dependency latency | p95 > SLO → ticket |

Replace thresholds in `.work/plans/operations/` or ADR.

---

## 6. SLOs

Document per critical user journey in SPECs or `REPLACE:OPS_DOC`:

| Journey | SLI | Target |
|---------|-----|--------|
| Example: checkout API | availability | 99.9% / 30d |

---

## 7. Forbidden

- Full request/response bodies on auth or PII routes.
- Raw tokens in any telemetry.
