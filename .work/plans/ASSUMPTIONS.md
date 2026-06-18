# Assumptions

**Brownfield synthesis 2026-06-18.**

| # | Assumption | Context | Last updated |
|---|-----------|---------|-------------|
| 1 | Single-org deployment — no multi-tenant isolation needed | Architecture | 2026-06-18 |
| 2 | Client CRM is the same product as tools-project, not a separate app | Product scope | 2026-06-18 |
| 3 | Client stakeholders need limited project access (not full team member access) | Permissions | 2026-06-18 |
| 4 | Sales pipeline stages (1-9: target → won/lost) match the tracking-system-spec and clients-participants SPEC | CRM | 2026-06-18 |
| 5 | GitHub PAT is the auth mechanism for MVP (vs GitHub App) | GitHub | 2026-05-16 |
| 6 | Fernet encryption with JWT-derived key is sufficient for PAT at rest | Security | 2026-05-16 |
