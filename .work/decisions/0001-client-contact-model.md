# ADR-0001: Client contact and access model

**Status:** Decided
**Date:** 2026-06-18
**Source:** `clients-participants` SPEC (§11 Q&A)

## Context

Adding CRM capabilities to tools-project requires modeling client companies, their contacts, and how those contacts interact with projects. The core design tension is between keeping the existing internal team model clean while adding external client participants with different permissions and visibility.

## Decision

### 1. Client contact identity — separate table

`client_contacts` is a standalone table with an optional `user_id` FK to `users` and a `role` column (`contact` / `contact_admin`). Contacts may exist without a system login. When they need to authenticate, a `user` record is created and linked.

**Rationale:** Keeps the `users` table clean for authenticated system accounts. A client contact who never logs in doesn't need a `users` row. The `role` column lets client companies self-manage contacts without mixing them into internal `project_members`. Avoids mixing internal team members with external contacts in the same table.

### 2. Project-client relationship — join table

`project_clients` join table links projects to clients (many-to-many). A project may have zero, one, or multiple clients. UNIQUE `(project_id, client_id)` prevents duplicate links.

**Rationale:** Supports the real-world case where a project serves multiple client stakeholders. More flexible than a single `project.client_id` FK. A project with exactly one client displays it as "the client" in UI — a presentation concern, not a schema constraint.

### 3. Client access model — dedicated table

`project_client_access` table links `client_contacts` to `projects` with a separate role set (`view` / `contribute` / `decision_maker` / `billing`). The existing `project_members` table is unchanged and remains for internal team only.

**Rationale:** Internal team roles (owner/maintainer/contributor/viewer) and client participant roles have different semantics and permission sets. Mixing them in one table with a `type` discriminator would complicate every permission check. Separate tables give a hard boundary that's easier to audit and maintain.

### 4. Pipeline storage — separate prospects table

`prospects` tracks leads through the sales pipeline (stages 1–9). When a prospect reaches `won`, a corresponding `clients` record is auto-created. Prospects that reach `lost` remain in the prospects table for historical reference.

**Rationale:** The sales pipeline (pre-sale) and client delivery (post-sale) have different data shapes and workflows. Separating them prevents `clients` from accumulating pipeline-specific fields. The `clients` table stays focused on delivery: company info, contacts, project links.

### 5. Client contact auth — individual accounts

Client contacts who need to log in get individual `user` accounts linked via `client_contacts.user_id`. Shared accounts per client company are not supported.

**Rationale:** Individual accounts provide proper audit trails, individual permissions, and consistent auth patterns with the existing system. Matching existing `users` table patterns.

### 6. Activity visibility — by is_internal flag

Client participants see all activities where `is_internal = false`. The existing flag is reused rather than adding a new "share with client" marker.

**Rationale:** Simpler than an opt-in mechanism. The flag already exists and is used by the team to mark internal discussions. One flag controls both internal-only visibility and client visibility.

### 7. Login — separate page

Client participants authenticate via a separate `/client/login` page instead of the internal `/login`. Post-auth redirect goes to a limited client dashboard.

**Rationale:** Clear visual separation between internal tool and client portal. Reduces confusion for both audiences. The internal login page stays unchanged for team members.

### 8. Task creation — permission-based

`view` role (default) is read-only. `contribute` role can create tasks and comment. Controlled by `project_client_access.can_create_tasks` boolean alongside the role enum.

**Rationale:** Flexible — not a binary yes/no. The permission is granular enough to support both read-only stakeholders and active contributors without separate role enums for every combination.

### 9. Onboarding checklist — client record only

When a prospect reaches `won` and a client is created, a checklist is created within the client record. Items do not auto-create tasks in projects.

**Rationale:** Keeps onboarding as a lightweight checklist. Team can manually create project tasks from checklist items. Avoids coupling the onboarding workflow to the task system in V1.

## Consequences

- Permission resolution in `deps.py` must check both `project_members` (internal) and `project_client_access` (client) to determine access level.
- The `/client/login` path and client dashboard need a new Next.js route group separate from the main app layout.
- Existing projects and users are unaffected — all additions are optional and backward compatible.
- The `prospects` → `clients` promotion on `won` must be a transactional operation (create client, link contacts, trigger onboarding).
- ADR-0001 should be revisited if the product evolves toward true multi-tenant or a public client portal.
