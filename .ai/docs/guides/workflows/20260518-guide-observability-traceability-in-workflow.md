# Observability and traceability in the workflow

**Doc type:** Guide (portable).  
**Pairs with:** feature SPEC “Observability” section, implementation **verify** gates, and production incident response.

---

## 1. Goals

- **Traceability:** Every request or job can be tied to **correlation** and **tenant** (or equivalent) identifiers across logs and traces.  
- **Debuggability:** On failure, an operator can find **one** trace or log stream without PII leaks.  
- **Verification:** Implementation review checks observability **claims** in the SPEC against **what shipped**.

---

## 2. Minimum contract (project-agnostic)

Define in `{OBSERVABILITY_SPEC}` (or your feature SPEC section 9) at least:

| Concern | Requirement |
|---------|-------------|
| **Log shape** | Structured fields (JSON or equivalent); stable `event` names. |
| **Correlation** | Incoming request ID propagated to outbound calls and queue payloads. |
| **Tenant / actor** | Internal IDs only in logs (no raw PII or secrets - align with security policy). |
| **Traces** | Which entrypoints create spans; which downstream calls must be child spans. |
| **Metrics** | Counters/histograms for critical user journeys (namespaced). |

---

## 3. Where this appears in the lifecycle

| Stage | Artifact | Action |
|-------|----------|--------|
| **Spec** | Feature SPEC §Observability | List events, fields, SLOs (or links). |
| **Plan** | Master plan NFR rows | Reference observability NFR ids. |
| **Implement** | Code + tests | Assert log/trace fields in unit/integration tests where cheap. |
| **Verify** | Check matrix | Row: observability - pass if SPEC fields exist in code paths touched; **skip** only if task truly did not touch instrumented surfaces (document `n/a`). |
| **Run** | Dashboards / alerts | Owned by platform; out of scope for this guide. |

---

## 4. AI-assisted coding

When agents generate code:

- Require **explicit** log field names in the PR description (copy from SPEC).  
- Forbid dumping raw payloads - align with security / privacy standard.  
- If `{OBSERVABILITY_SPEC}` is missing, default verify row = **gap** with recommendation to draft spec before GA.

---

## 5. Evidence tags for SLOs

Numeric SLOs in plans must carry `measured` (from load test or prod metrics), `estimated`, or `assumption` - never presented as measured without a source.
