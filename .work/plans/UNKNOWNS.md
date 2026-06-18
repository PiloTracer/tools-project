# Unknowns

**Brownfield synthesis 2026-06-18.**

| # | Unknown | Blocks | Owner | Status |
|---|---------|--------|-------|--------|
| 1 | Client contact identity: same `users` table with flag vs separate `client_contacts`? | CRM architecture ADR | ADR-0001 | **Decided** — separate `client_contacts` with optional `user_id` FK |
| 2 | Project-client relationship: `project.client_id` FK vs many-to-many join? | CRM data model | ADR-0001 | **Decided** — `project_clients` many-to-many join table |
| 3 | Client access model: new table vs extending `project_members` with type flag? | Permission model | ADR-0001 | **Decided** — dedicated `project_client_access` table |
| 4 | Sales pipeline: `clients.pipeline_stage` column vs separate `prospects` table? | CRM data model | ADR-0001 | **Decided** — separate `prospects` table; auto-create `clients` on `won` |
| 5 | Client contact auth: individual system accounts vs shared access? | Auth design | ADR-0001 | **Decided** — individual `users` accounts per contact |
| 6 | What are the specific permissions a client stakeholder needs per project? | Permission model | ADR-0001 / SPEC | **Decided** — `view`/`contribute`/`decision_maker`/`billing` roles in `project_client_access` |
| 7 | Does the GitHub web page (I10d) or CRM come first in implementation order? | Batch priority | Product owner | **Open** — depends on active priority call |
