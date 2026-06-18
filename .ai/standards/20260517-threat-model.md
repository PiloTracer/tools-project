# Threat Model — template

**Status:** Customize for your repo before production.
**Pairs with:** data-classification, FEATURE_STANDARD §10, security ADRs.

---

## 1. Assets (fill in for your system)

| Id | Asset | Impact if lost or tampered |
|----|-------|----------------------------|
| A1 | Customer PII | Regulatory and reputational harm |
| A2 | Integration credentials | Impersonation of your system to third parties |
| A3 | Business records (orders, invoices, …) | Audit failure, financial loss |
| A4 | Signing or encryption keys | Forgery, decryption |
| A5 | Session / API tokens | Account takeover |

## 2. Trust boundaries

```text
[Browser] ──TLS──▶ [API] ──TLS──▶ [Database]
                      │
                      ├──▶ [Queue / workers]
                      └──▶ [External provider APIs]
```

Document each arrow: auth mechanism, data classes crossing, and validation points.

## 3. STRIDE (per boundary)

| Threat | Mitigation (examples) |
|--------|----------------------|
| Spoofing | JWT validation, mTLS to providers |
| Tampering | Signed webhooks, immutable audit log |
| Repudiation | Correlation ids, append-only events |
| Information disclosure | Classification + redaction + encryption |
| Denial of service | Rate limits, queue backpressure |
| Elevation | RBAC, tenant isolation in DB session |

## 4. High-risk areas

List modules that require ≥2 reviewers and optional architect sign-off before `@code-implementation complete`:

- REPLACE:HIGH_RISK_MODULE_1 (e.g. auth, payments, external submission)
- REPLACE:HIGH_RISK_MODULE_2

Skills reference this list for cross-LLM and human review gates.

## 5. Supply chain

- Pin dependencies in `REPLACE:TECH_STACK_DOC`.
- No secrets in repo; scan CI for leaked credentials.

## 6. Incident response

- Owner contact and runbook path: `REPLACE:INCIDENT_RUNBOOK`.

## 7. Review cadence

- Revisit on any ADR that changes trust boundaries or adds a new external integration.
