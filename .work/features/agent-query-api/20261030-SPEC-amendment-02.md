# Web-URL ticket addressing + activity pagination — Feature SPEC amendment 02

**Status:** Draft — owner-directed implementation 2026-10-30 (approval pending)
**Owner:** Engineering
**Amends:** [`20260701-SPEC.md`](20260701-SPEC.md) (Approved) · [`20261030-SPEC-amendment-01.md`](20261030-SPEC-amendment-01.md) (Approved)
**Date:** 2026-10-30 · **Slug:** agent-query-api
**Trigger:** owner direction — a client system receives a **web ticket link** and must fetch the ticket (including recent comments) without knowing UUIDs or refs.

---

## 1. Purpose

Amendment 01 addresses tickets by UUID or `ref`. A consumer that receives a copied link
(`https://host/projects/<project>/tickets/<uuid>`) must parse it first. This amendment adds a
server-side resolver and documents the paginated comment feed, so the link itself is a usable input.

## 2. Binding changes

### R23 — `GET /v1/agent/tickets/resolve?url=<link>`

- Accepts an absolute URL (`https://…/projects/<p>/tickets/<uuid-or-ref>`) or a relative path
  (`/projects/<p>/tickets/<uuid-or-ref>`), trailing slash and query string allowed.
- The last non-empty path segment is the ticket address (UUID or ref), resolved exactly like R3.
- Returns the **same payload** as R3 (all knobs apply).
- No ticket segment → `400 {"detail": "invalid_ticket_url"}`; unknown ticket/tenant/access → the R3
  `404 ticket_not_found`.
- The URL host is not validated (the ticket lookup and access checks decide); no redirects are
  followed and no external request is made.

### R24 — MCP `get_ticket_detail(url=…)` + `list_ticket_activities`

- `get_ticket_detail` accepts `url` as an alternative to `ticket` (one of the two is required) and
  calls the resolve route.
- `list_ticket_activities` exposes the R6 feed (`ticket, limit, offset, order, kind,
  include_internal`) so older pages are reachable from an agent.

### R25 — Attachment `scope` precedence (clarification of R5)

When a file is linked to an activity **and** carries `ticket_id` (comment uploads do both), `scope`
is `"activity"` — the more specific owner. Ticket-level files (no activity) stay `"ticket"`.

## 3. Evidence

- Implemented on `main` (uncommitted at time of writing): `agent_query.py` (resolve + activities +
  scope), `api/app/client/mcp_server.py` (url argument + tool), tests.
- Verification: `POST/GET` live on the dev stack — resolve by a Pizote-style link returned the ticket
  with `counts.activities=3`, newest-first comments; `activities?limit=2&order=desc` returned the two
  newest with `has_more=true, next_offset=2`; `order=asc` returned the oldest pair; MCP
  `get_ticket_detail(url=…)` and `list_ticket_activities` returned the same data. Test suite
  covers URL resolution (absolute/relative/trailing slash/invalid/unknown), newest-first ordering,
  pagination/offset, internal/visibility/kind filters and comment attachments.

## 4. SPEC sections affected

- Amendment 01: R1 (addressing), R3 (detail), R5 (scope), R6 (activities), R9 (tools), §6 (APIs),
  §8 (error model adds `invalid_ticket_url`), §11 (tests).
- Base SPEC §6 (endpoint list) gains the resolve route; product version unchanged.

## 5. Rollout

Additive. P1 of amendment 01 (activities + MCP tool) and the new resolve route ship together; no
schema, no migration, no new dependency. Rollback = remove the two routes and the MCP additions.
