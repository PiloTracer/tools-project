# Data Classification — template

**Status:** Customize for your repo before handling production data.
**Bootstrap:** Replace examples with your domain; link from SPECs and threat model.

---

## 1. Classes

| Class | Definition | Examples (replace) |
|-------|------------|-------------------|
| **public** | Safe to expose without auth | Product catalog enums, public docs |
| **internal** | Operational, not customer-facing | Request ids, feature flags, job metadata |
| **pii** | Identifies a natural person | Name, email, phone, government id |
| **financial** | Monetary or contractual trade data | Invoice amounts, ledger entries |
| **credential** | Authenticates or authorizes | API keys, passwords, signing material, session tokens |

## 2. Handling rules

| Class | At rest | In transit | In logs | In traces |
|-------|---------|------------|---------|-----------|
| public | standard | TLS | allowed | allowed |
| internal | encrypted if policy requires | TLS | allowed | allowed |
| pii | encrypt + access control | TLS | **forbidden** (redact) | **forbidden** |
| financial | encrypt + access control | TLS | **forbidden** | **forbidden** |
| credential | secrets manager only | TLS | **forbidden** | **forbidden** |

## 3. Column tagging

- New persisted columns declare class in the SPEC §10 and in migration comments.
- References to secrets store ids are **internal**, not **credential** (the secret value is credential).

## 4. Retention

- Document legal/regulatory retention per class in ADR; default operational logs ≤ REPLACE:LOG_RETENTION_DAYS days.

## 5. Redaction

- Platform helper `REPLACE:REDACT_FN` for structured logs that must include partial payloads.

## 6. Open items

- Track unknown retention or jurisdiction rules in `.work/plans/UNKNOWNS.md`.
