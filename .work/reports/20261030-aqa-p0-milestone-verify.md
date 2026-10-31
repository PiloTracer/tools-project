## code-verify milestone — AQA P0: ticket detail + attachment reads

**Date:** 2026-10-30 · **Triggered by:** `@code-implementation complete` (after T1–T7)
**Request:** explicit mode (`milestone`, iteration-scoped feature work under Approved SPEC amendment 01)

### M0 — Milestone
AQA-P0 is the active `## Current iteration` in `NEXT.md`; it is **not** a master-plan milestone (M1–M4 shipped). The HANDOFF plan-gate waiver (2026-10-30) covers feature-SPEC iterations — recorded per `@code-implementation` ST0.

### Check matrix

| Dimension | Result | Evidence / gap |
|-----------|--------|----------------|
| FR coverage | **pass** | Feature SPEC amendment 01 §11 mapping; every P0 test is implemented (40 feature tests) |
| SPEC rules | **pass (scoped)** | R1–R7, R9, R13–R19 implemented and tested; R8, R11, R12, R20, R21(partial), R22 are P1/P2 by §12 design — deferred, not missed |
| ADR alignment | **pass** | ADR-0002 (no Alembic; idempotent startup DDL untouched), ADR-0004 (Compose services, local attachment store, 25 MiB cap) |
| Scope discipline | **pass** | `touch-scope-verify.sh` pass — every changed file declared in the iteration or `.work/touch-scope` |
| Schema | **skip** | No DDL in P0; R20 index is P2 |
| Invariants | **pass** | I1 (GET only), I2 (`storage_key` absent — test), I3/I4/I7 (resolver + mime allowlist tests), I6 (description byte-identical — test), I8 (additive), I11 (subject-visibility tests), I12 (UA test) |
| Security | **pass** | secrets scan clean; emails staff-only; audit log lines carry ids only; auth matrix 401/403/404 covered |
| Test coverage | **pass** | 128 tests in-container (21 discovery/attachment, 19 MCP, 5 shared builder, 3 public URLs, rest pre-existing) |
| Observability | **pass (gap low)** | `agent.ticket_detail` + `agent.attachment_read` logged; `agent.ticket_activities` is P1 |
| Concept / NFR registry | **pass** | MOD-01/MOD-05/MOD-06 marked done with evidence; MOD-06 validated by `mod06-output-check.sh` |
| Coupling / blast | **warn** | 4 boundaries (API services/routers, deps, compose config, MCP client) — second reviewer required |
| AI-assisted safety | **pass** | `.work/reports/20261030-aqa-p0-mod06.md` → `mod06-output: pass` |
| Docs alignment | **pass** | `agent-query-api.md`, `AGENT_TICKET_CONTEXT.md`, `LLM-2-API_SETUP.md`, `REPO_INTEGRATION.md`, guide updated to "implemented, pending deployment" |

### Gaps

| Severity | Gap | Owner / resolution |
|----------|-----|--------------------|
| **High** | M3 cross-LLM / human architect review for the authorization boundary (single-model session; high-risk area) | **Owner**: document human architect review in HANDOFF (name + date) or run a cross-model review before merging |
| **Med** | Hosted acceptance (R22) against a deployed 1.1.0 build not run — production still runs `0.1.3` | **Owner**: deploy; then run the R22 subset (detail, comments, 3 screenshots, capabilities, MCP self-check) |
| **Low** | `agent.ticket_activities` log line, capabilities endpoint, `list_ticket_activities`, `project_id` filter, context counts fix, R20 index | P1/P2 of amendment §12 |

### Cross-LLM
`gap` — single-model session; the iteration touches a high-risk area (authorization + binary serving). Not waived: recorded as the High gap above (owner action).

### Verdict
**pass with gaps** — implementation and gates are green; the gaps are the owner's deployment and human/cross-model review, both documented in HANDOFF.
