# Risk registry

**Brownfield synthesis 2026-06-18.**

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | Permission model becomes too complex with client + internal roles, leading to bugs | Medium | High | ADR first, then simple implementation, then iterate |
| 2 | GitHub web UI (I10d) stalls while CRM is prioritized, leaving a half-finished Batch I | Medium | Medium | Document in NEXT.md; decide priority explicitly |
| 3 | Client contacts without system accounts create auth friction | High | Medium | Consider magic-link or invite-code as interim auth |
| 4 | No dedicated `.env.example` for new CRM env vars creates deployment confusion | Low | Medium | **Mitigated / closed:** CRM V1 reuses existing auth (JWT/OAuth) and no new secrets; no CRM-specific env vars required in first PR. Re-open if onboarding email/external integrations add secrets. |
| 5 | Scope creep: CRM grows into a full ERP with billing, invoicing, etc. | Medium | High | Strict §2 Out of scope in CRM feature SPEC |
