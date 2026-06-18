# Workflow guides

> **Lost or unsure what to invoke?** Open [`.ai/START_HERE.md`](../../../START_HERE.md) - it answers "what do I do right now?" in ≤2 minutes. The matrix below is **reference**; START_HERE is the **decision tree**.

This directory holds portable workflow documentation with two filename shapes:

- **`YYYYMMDD-tutorial-<slug>.md`** - step-by-step material aimed at the **operator** (run this, then that).
- **`YYYYMMDD-guide-<slug>.md`** - **reference** or internal-style docs (layers/template, cross-cutting NFR, methodology companions to skills).

**Curriculum (recommended order) and extra narrative:** [20260518-guide-workflows-index.md](20260518-guide-workflows-index.md)

Links to `…/workflows/README.md` land here.

**Matrix scope:** list paths **normatively referenced** by **`.cursorrules`**, **`.ai/skills/*/skill.md`** (and their `reference.md` companions), **`.ai/standards/*.md`**, the **`.ai/concepts/`** workflow (`README` + per-concept `README` / `prompt.md`), the **workflow guides** in this directory, and **custom agent** wrappers only when they defer to the same rules/skills (no parallel “shadow” governance).

The **artifact matrix** below maps **planning** vs **implementation** (plus cross-cutting and operations) for those official layers only.

---

## Planning and implementation artifact matrix

### Legend - Status

| Status | Meaning |
|--------|---------|
| **Binding** | Engineering standard or rule set; code and SPECs must conform. |
| **Living** | Updated often during sessions or iterations; truth drifts if neglected. |
| **Planning** | Strategic or milestone roadmap; versioned, human-approved. |
| **Registry** | Append-only or carefully maintained planning memory (assumptions, risks, unknowns). |
| **Skill** | Executable agent/human workflow (`skill.md` + optional `reference.md`). |
| **Guide** | Process documentation (this folder and linked workflow docs). |
| **Context** | Read when relevant; not changed every sprint. |
| **Application** | Product source, tests, and migrations. |
| **Protected** | Per project rules: do not modify without explicit approval. |

### Legend - Phase (primary)

| Phase | When it matters |
|--------|-----------------|
| **Planning** | Roadmaps, certification, registries, proposals, SPEC/ADR authorship before or between coding pushes. |
| **Implementation** | Iteration execution, code, tests, schema, verify/complete, local stack bring-up. |
| **Both** | Session hygiene, tactical queue, global rules, standards, concepts, SPECs as the contract under test. |
| **Operations** | Approved runbooks and protected infra definitions (read during setup; edits need approval). |

**Paths** below use **example** filenames and layout. In each adopting repo, map rows to your placeholders ([Path bootstrap](20260518-tutorial-path-bootstrap.md)) and `.cursorrules` `REPLACE:` tokens.

| Path | Phase | Status | Short description |
|------|-------|--------|-------------------|
| `.cursorrules` | Both | Binding | Global agent + engineering rules; workflow bootstrap and placeholder quick-map. |
| `.ai/START_HERE.md` | Both | Context | **Operator decision tree** - answers "what do I invoke right now?"; recovery checklist; forgetfulness gate. First read when lost. |
| `README.md` (repo root) | Both | Context | Human entry point; planning mode and stack pointers (`plan-foundation` identity read). |
| `REPLACE:TECH_STACK_DOC` (e.g. `DOCS_TECH_STACK.md`) | Both | Binding | Pinned versions, stack topology, open ADR TODOs. |
| `.ai/README.md` | Both | Context | Canonical map of `.ai/` trees (plans, standards, skills, features). |
| `.work/context/HANDOFF.md` | Both | Living | Session open/close, repository state, pick-up, produced-artifact table. |
| `.work/plans/NEXT.md` | Both | Living | Tactical backlog, **Recommended next**, **`## Current iteration`** sub-plan, Done history. |
| `.work/plans/full/*-full-plan.md` | Planning | Planning | Master implementation plan (FR/NFR, milestones M1…, acceptance, validation gates). |
| `.work/plans/foundation/YYYYMMDD-0*-*.md` | Planning | Planning | Foundation docs 01–04 (scope, integration, adjacency, architecture proposal - not the full plan). |
| `.work/plans/ASSUMPTIONS.md` | Planning | Registry | Labeled assumptions (Confirmed / Inference / …). |
| `.work/plans/RISK_REGISTRY.md` | Planning | Registry | Architectural, ops, security, compliance risks. |
| `.work/plans/UNKNOWNS.md` | Planning | Registry | Open questions, owners, blockers. |
| `.work/plans/proposals/` | Planning | Context | Optional pre-SPEC feature proposals (`FEATURE_STANDARD`). |
| `.work/plans/operations/*.md` | Operations | Context | Approved runbooks (docker, sandbox, compliance, regulatory watch, …). |
| `.work/plans/archives/` | Planning | Context | Long-lived planning archives when used. |
| `.work/plans/YYYYMMDD-personas-v1.md` | Planning | Living | **Optional** UX personas when UI is in scope (`plan-foundation`); path/date are project-specific. |
| `.work/features/<slug>/YYYYMMDD-SPEC.md` | Both | Binding | Feature behaviour (R1…), data model, observability, **section 15** concept registry, test plan. |
| `.work/features/<slug>/CHANGELOG.md` | Implementation | Living | Per-feature release notes after merge. |
| `.work/features/<slug>/YYYYMMDD-SPEC-amendment-*.md` | Planning | Planning | Post-approval SPEC deltas (do not edit merged SPEC in place). |
| `.work/decisions/README.md` | Planning | Context | ADR index. |
| `.work/decisions/YYYYMMDD-NNN-*.md` | Both | Binding | Architectural decision records. |
| `.ai/standards/20260517-CONVENTIONS.md` | Both | Binding | Code layout, naming, tests tooling, logging discipline. |
| `.ai/standards/20260517-FEATURE_STANDARD.md` | Both | Binding | Feature lifecycle, SPEC template (incl. section 15 concept registry). |
| `.ai/standards/20260517-DIRECTORY_MAP.md` | Both | Binding | Repo directory gate; interim **module boundary** reference. |
| `.ai/standards/20260517-observability-spec.md` | Both | Binding | Metrics, traces, logs, SLO expectations. |
| `.ai/standards/20260517-api-style-guide.md` | Both | Binding | HTTP API style (RFC 7807, pagination, idempotency). |
| `.ai/standards/20260517-threat-model.md` | Both | Binding | STRIDE threat model. |
| `.ai/standards/20260517-data-classification.md` | Both | Binding | Data classes + handling matrix. |
| `.ai/skills/README.md` | Both | Skill | Skill registry and **kebab-case** naming protocol. |
| `.ai/skills/plan-foundation/skill.md` | Planning | Skill | Foundation P0–P6; certify **plan-master-ready**. |
| `.ai/skills/plan-foundation/reference.md` | Planning | Context | Optional extended procedures for `plan-foundation`. |
| `.ai/skills/plan-master/skill.md` | Planning | Skill | Master plan; integrity; **implementation-ready** status. |
| `.ai/skills/plan-master/reference.md` | Planning | Context | Optional extended procedures for `plan-master`. |
| `.ai/skills/session-control/skill.md` | Both | Skill | Session start/close; HANDOFF/NEXT; optional git. |
| `.ai/skills/session-control/reference.md` | Both | Context | Optional extended procedures for `session-control`. |
| `.ai/skills/db-migration/skill.md` | Implementation | Skill | Idempotent numbered SQL migrations; no version table, no chain conflicts. |
| `.ai/skills/db-migration/reference.md` | Implementation | Context | Optional extended procedures for `db-migration`. |
| `.ai/skills/code-implementation/skill.md` | Implementation | Skill | `plan` *(alias: `plan-iteration`)*, `start`/`continue`/`complete`; task gates; tests. |
| `.ai/skills/code-implementation/reference.md` | Implementation | Context | Optional extended procedures for `code-implementation`. |
| `.ai/skills/code-verify/skill.md` | Implementation | Skill | `milestone` / `uncommitted` / `last` verification gates. |
| `.ai/skills/code-verify/reference.md` | Implementation | Context | Optional extended procedures for `code-verify`. |
| `.ai/skills/code-repair/skill.md` | Implementation | Skill | Remediate verifier/migration/SPEC findings; mandatory re-verify. |
| `.ai/skills/code-repair/reference.md` | Implementation | Context | Optional extended procedures for `code-repair`. |
| `.ai/skills/plan-verify/skill.md` | Planning | Skill | Foundation / master / alignment plan audits; orchestrates status + integrity. |
| `.ai/skills/plan-verify/reference.md` | Planning | Context | Optional extended procedures for `plan-verify`. |
| `.ai/skills/plan-repair/skill.md` | Planning | Skill | Remediate plan-verify findings; brownfield plan bootstrap; mandatory re-verify. |
| `.ai/skills/plan-repair/reference.md` | Planning | Context | Optional extended procedures for `plan-repair`. |
| `.ai/skills/dev-stack/skill.md` | Implementation | Skill | Isolated Docker Compose helper (`bin/start.sh`); safe `.env` handling. |
| `.ai/skills/dev-stack/reference.md` | Implementation | Context | Optional extended procedures for `dev-stack`. |
| `.ai/skills/process-router/skill.md` | Both | Skill | Read-only router: process questions → skill verb, guide, standard (no writes). |
| `.ai/skills/process-router/reference.md` | Both | Context | Routing table and example invocations for `process-router`. |
| `.ai/skills/feature-spec/skill.md` | Planning | Skill | Author, review, amend feature SPECs per FEATURE_STANDARD. |
| `.ai/skills/concept-run/skill.md` | Both | Skill | Run MOD-01…MOD-06 concept prompts; attach output to PR/NEXT/SPEC. |
| `.ai/concepts/README.md` | Both | Context | Architecture / NFR **concept pack** index (e.g. MOD-01–MOD-06). |
| `.ai/concepts/<concept>/README.md` | Both | Context | Per-concept human + agent context. |
| `.ai/concepts/<concept>/prompt.md` | Both | Guide | Per-concept agent procedure + output shape. |
| `.ai/docs/guides/workflows/README.md` | Both | Context | This file: filename rules + **canonical artifact matrix**. |
| `.ai/docs/guides/workflows/20260518-guide-workflows-index.md` | Both | Guide | Curriculum map, principles, link back to this matrix. |
| `.ai/docs/guides/workflows/20260518-guide-*.md` | Both | Guide | Reference workflow docs (pattern): end-to-end template, boundary map, observability, testing-in-process, plan companions. |
| `.ai/docs/guides/workflows/20260518-tutorial-*.md` | Both | Guide | Operator step-by-step tutorials (pattern): bootstrap, walk-throughs, NEXT/delivery, test requests. |
| `.ai/docs/guides/workflows/20260529-tutorial-probe-project.md` | Planning | Guide | Operator tutorial: `probe` mode - adaptive interrogation to fill foundation/plan gaps before certification. |
| `.ai/docs/integration/MANIFEST.txt` | Implementation | Context | Vendor artifact inventory (project adds; see `docs/integration/README.md`). |
| `.ai/docs/integration/**` | Implementation | Context | Cached vendor specs (project-owned; read on demand). |
| `.work/plans/foundation/*-01-*-initial-scope.md` | Planning | Living | **P0 initial scope** mini-plan - `@plan-foundation` greenfield creates; canonical product-intent capture (not `{PROMPTS_ROOT}/initial.md`). |
| `.work/prompts/*` (project-local) | Planning | Context | Questionnaires, archived decision prompts, optional **user scratch** (`initial.md`). Skills **do not** read `initial.md` unless the user explicitly names it. |
| `REPLACE:APP_ROOT/**` | Implementation | Application | Application source and bounded contexts. |
| `REPLACE:APP_ROOT/tests/**` or project test dir | Implementation | Application | Unit, contract, integration, e2e as adopted. |
| `REPLACE:MIGRATIONS_DIR/*.sql` | Implementation | Application | Idempotent schema scripts (`db-migration` skill). |
| `REPLACE:FRONTEND_ROOT/**` | Implementation | Application | UI (when present). |
| `bin/start.sh` (if present) | Implementation | Living | Dev stack entry script when **dev-stack** skill creates or maintains it; absent until generated. |
| `docker-compose.yml` | Operations | Protected | Multi-service local dev stack (`.cursorrules`: no edits without approval). |
| `Dockerfile.*`, `docker-compose*.yml` | Operations | Protected | Container definitions (approval required). |
| `package.json`, `REPLACE:FRONTEND_CONFIG_PATHS`, `.env*` (not `.env.example`) | Both | Protected | Tooling and env files: **no edits without explicit approval** (see `.cursorrules`). |
| `.env.example` | Both | Living | Safe environment variable template (no secrets). |

*Other paths may be added to `.cursorrules` as protected; treat that list as authoritative when it diverges from this matrix.*

---

**Skills registry (`@` handles, naming protocol):** [`.ai/skills/README.md`](../../../skills/README.md). **Curriculum and principles:** [20260518-guide-workflows-index.md](20260518-guide-workflows-index.md).