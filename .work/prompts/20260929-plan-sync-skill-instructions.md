# Instruction document — `@plan-sync` skill for the pilo.ai.logicbison OS Framework

**Audience:** the pilo.ai.logicbison (Agent OS) framework maintainer / agent operating that repo.
**Purpose:** add the missing **P2 half** of plan-sync: the `@plan-sync` agent skill that turns plan markdown into a validated manifest and imports it into the tools-project service.
**Date:** 2026-09-29 · **Requested by:** tools-project owner
**Consuming repo context:** tools-project already ships the entire P1 backend (verified 2026-09-29: ruff/pyright/pytest 49/49, migration restart×2 idempotent, live curl smoke 14/14). **This repo needs zero further changes** — everything below is framework-side only.

---

## 1. Context — what already exists (read-only facts)

| Piece | State | Where |
|-------|-------|-------|
| Import endpoint | **LIVE** — `POST /v1/projects/{id}/plan-import` (optional `?dry_run=true`) | tools-project API |
| Auth | `X-Api-Key` (personal key or shared agent key) **or** Bearer JWT + project RBAC (contributor+) | D7 — `X-Api-Key` is accepted on this route **only** among mutating endpoints |
| Manifest schema | **v1** — see §4.2 envelope below; server validates authoritatively (pydantic, 400 + field list) | SPEC §6 |
| Semantics | local-status-wins, obsolete matrix, never deletes, one transaction, one summary activity | SPEC §4 (R5–R20) |
| Plan sources | `.work/feedback/plans-import/plans/*.md` (e.g. `20260925-full-plan.md`: 12 milestones, 153 tasks) | consuming repo |
| Key distribution standard | `~/.tools-project-key` (chmod 600, optional `BASE_URL=` first line) or `TOOLS_PROJECT_API_KEY` env | already used by `project-query-setup` + `.opencode/mcp/project-mcp` |
| Read-only MCP | `.opencode/mcp/project-mcp/mcp_server.py` — 5 GET tools | **stays read-only (see §3)** |

Architecture (approved proposal D3): **agent parses plan → JSON manifest → transactional API ingest.** The plan format will drift over time; the design point is that drift costs a *skill* edit, zero app-code change. The skill is deliberately disposable — the REST contract is the stable layer.

---

## 2. Decision (settled — do not relitigate)

**Chosen: Option (a) — skill communicates directly with the project REST API over HTTP.**

Criterion applied: *maximum simplicity when configuring access of a codebase to the Project system.*

| | (a) Direct HTTP | (b) Via MCP extension |
|---|---|---|
| Per-codebase configuration | **Zero** — skill resolves the machine-global key file/env (same rules as the MCP already uses) | Key **+** MCP registration in that codebase's agent config (`opencode.json` / cursor config) **+** server code change |
| Server changes | None | Extend a server documented as *"read-only agent queries"* with a write tool |
| Non-agent callers (curl, CI, future upload UI) | Same endpoint | Still need the endpoint anyway |

**(a) meets the criterion properly → (a) it is.** The MCP remains a read-only query adapter; both paths would hit the same API, so MCP would add configuration, not capability.

**Explicit prohibition:** do **not** add write tools to `.opencode/mcp/project-mcp` or change any "read-only" guarantee (`project-query-setup` hard rule 2, MCP docstring). If this decision is ever revisited, it requires a fresh owner sign-off — not a skill-side change.

---

## 3. Required changes (file-by-file)

All paths relative to the framework repo root (`/mnt/work/Projects/pilo.ai.logicbison/`).

| # | Action | File | Detail |
|---|--------|------|--------|
| 1 | **CREATE** | `skills/plan-sync/skill.md` | Full behavioral contract in §4 below |
| 2 | **UPDATE** | `skills/README.md` | Add row to the skills table (header at line 32: `Skill id \| Folder \| Role`) following the format of the `project-query-setup` row (line 53) |
| 3 | **UPDATE** | `skills/SKILL_DEPENDENCIES.md` | Add `plan-sync` to the dependency/gate matrix in the file's existing format; prerequisites: none (standalone, optional integration — same class as `project-query-setup`) |
| 4 | **UPDATE** | `templates/cursorrules.template` | Add table row in **§ Skills** (table containing `project-query-setup` at line 160): `plan-sync \| plan-sync/ \| Parse plan markdown → manifest → POST plan-import (dry-run gate)` — so thin-client bootstraps know the skill |
| 5 | **UPDATE** | `START_HERE.md` | One decision-tree row, e.g. `I want to sync a plan into the Project system` → `@plan-sync sync - <plan path>` (anchor: table around lines 120–125) |
| 6 | **VERIFY** | run | `bash scripts/framework-verify.sh` and `bash scripts/cursorrules-verify.sh` — both must pass before hand-back |

**Naming compliance** (skills/README.md § Naming protocol, lines 15–26): id `plan-sync` = `{domain}-{role}` (`domain: plan`, `role: sync`), kebab-case, two segments; folder name = frontmatter `name:` = `@` handle = row key in `.cursorrules` § Skills. Update all registration points in one pass (the protocol says so explicitly).

**Model the skill file on:** `skills/project-query-setup/skill.md` (auth/key/connectivity posture, Modes table, Hard rules, operator handoff contract) + `skills/code-implementation/skill.md` (multi-step gated workflow). Reuse the **Operator handoff contract** from `SKILL_DEPENDENCIES.md` verbatim (Form A / Form B) — no invented response format.

---

## 4. Skill behavioral contract (`skills/plan-sync/skill.md` content)

### 4.1 Modes

| Invocation | Mode |
|------------|------|
| `@plan-sync status` | Connectivity + key + base URL check; list reachable projects (also the setup verification) |
| `@plan-sync sync - <plan path>` | Full flow: parse → validate → **dry-run** → preview → operator confirmation → commit → report (default) |
| `@plan-sync dry-run - <plan path>` | Same as sync but stops after the preview; never commits |
| `@plan-sync help` | Usage, auth setup pointer (`@project-query-setup key`), limits |

Optional argument on sync/dry-run: `--project <uuid|slug|project_key>`. If omitted or not a UUID: resolve via `GET /v1/agent/projects` with the same key, match `slug`/`project_key`, and **show the matched project name + id for operator confirmation before any POST**. If ambiguous → ask, never guess.

### 4.2 Auth & endpoint resolution (mirror the MCP exactly — zero new config)

1. Key: env `TOOLS_PROJECT_API_KEY` → file `~/.tools-project-key` (first line that is not `BASE_URL=…`) → env `AGENT_API_KEY` (legacy). Same order as `mcp_server.py:41-56`.
2. Base URL: env `API_BASE_URL` → `BASE_URL=` line in the key file → `http://localhost:8300`. Same as `mcp_server.py:59-74`.
3. Missing/empty key → stop, print `@project-query-setup key` guidance. Never invent a key.
4. **Security hard rules (copy into skill):** never print/echo/log the key; never pass it on a command line (`ps`-visible) — read the file and set the header in-process or via stdin; never write key material to `tmp/`, repo files, or shell history; remote `BASE_URL` must be `https://…`.
5. HTTP status mapping: `401` → key missing/invalid → `@project-query-setup key`; `403` → project role < contributor → ask owner for role; `404` → wrong project id; `400` → print the field-error list verbatim and fix the manifest (nothing was written); `500` → project unchanged (transaction rolled back) → report and stop.

### 4.3 Manifest envelope (v1) — embed this in the skill

```json
{
  "manifest_version": 1,
  "source_path": ".work/feedback/plans-import/plans/20260925-full-plan.md",
  "plan_version": "v1.7",
  "project": {"name": "…", "key": "…", "description": "…"},
  "milestones": [{"plan_ref": "M1", "key": "M1", "name": "…", "description": "…", "sort_order": 1, "status": "pending"}],
  "tasks": [{"plan_ref": "M1-T1", "milestone_ref": "M1", "title": "…", "description": "…", "status": "pending"}],
  "components": []
}
```

Constants to embed:
- `manifest_version` must be `1` (server rejects anything else with 400).
- `plan_ref`: milestones `^M\d+$`, tasks `^M\d+-T\d+$`; unique within the manifest; every task's `milestone_ref` must exist in `milestones[]`.
- Limits: `tasks ≤ 500`, `milestones ≤ 100`; `title` 1–200 chars; `name` 1–200 chars.
- Task status vocabulary — accepts **plan** or app vocab; mapping applied server-side: `pending→todo`, `done→done`, `blocked→blocked`, `deferred→cancelled` (app vocab `todo|in_progress|blocked|done|cancelled` passes through).
- Milestone status: `pending | active | blocked | done | cancelled` (default `pending`). At most one `active` per project at commit (server enforces).

### 4.4 Parsing rules (plan markdown → manifest)

From the actual plan format (`.work/feedback/plans-import/plans/20260925-full-plan.md`):
- Milestone = `### M<n> — <name>` heading sections (metadata: `**Objective:**`, `**Scope — in/out:**`, `**Deliverables:**`, …). Populate `plan_ref: "M<n>"`, `name`, `description` from the section body, `sort_order` = section order.
- Tasks = the `#### Tasks - M<n>: …` tables: columns `| ID | Description | Files | FR/NFR | Complexity | Acceptance | Status |`. `ID` → `plan_ref` (e.g. `M1-T1`), its section → `milestone_ref`.
- `title` = `Description` cell **truncated/edited to ≤200 chars** (plan cells can be ~1400 chars — never send them as title).
- `description` = `## Acceptance` cell content first (the contract), then a provenance block (`plan_ref`, source file, plan version, `Files`, `FR/NFR`, `Complexity`) — SPEC R21.
- **`Complexity` must NEVER become `priority`** (SPEC R22) — complexity is description text only.
- `Status` cell → plan status via the mapping above; unknown status → ask operator, never guess.
- `source_path` = the plan file path as given; `plan_version` = from the plan header if present, else prompt.
- **Agent parses semantics, not a rigid grammar:** if a section is ambiguous or a table lacks the documented columns → stop and ask (proposal D3 rejected deterministic parsers for exactly this reason).

### 4.5 Mandatory safety gates

1. **Always `dry_run=true` first** (SPEC R7 — the preview is what the operator approves). Client-side pre-validate against §4.3 before even the dry run.
2. Preview must show: milestones/tasks `created / updated / obsolete / reactivated` counts + full `conflicts[]` (kind, plan_ref, detail) in a readable table, and state plainly: *nothing written yet; obsolete = will be flagged, never deleted; local statuses will be preserved*.
3. **Real POST only after explicit operator confirmation in the same session.** No confirmation → stop at preview.
4. Re-runs are safe (idempotent upsert matched by `(project_id, plan_ref)`); a second identical import reports `updated` counts, zero creates.
5. Never write to the plan file or anything under `.work/` (sync is one-way, invariant I1). Never edit app code — a format drift is fixed **in this skill**.

### 4.6 Report (post-commit)

Print the server's `PlanImportResult`: per-entity counts, conflict list, plus a one-line pointer to the project's activity feed (one `kind: system` summary row is the audit trail). Close per the Operator handoff contract (Form B if follow-up decisions exist, else Form A).

### 4.7 Hard rules block (skill.md must contain, near-verbatim)

1. Read-only toward the plan sources and the repo; the **only** write is the single `POST …/plan-import` call, gated by confirmation.
2. Never commit (dry_run → confirm → commit) without operator confirmation; never bulk-import from an unvalidated manifest.
3. Key secrecy per §4.2 rule 4.
4. No MCP changes; no new endpoints; no local database access; no raw SQL.
5. Auth/RBAC failures are reported, never worked around (no privilege escalation attempts, no key sharing).
6. Terse responses; Operator handoff contract (Form A/B) at end of turn.

---

## 5. Acceptance criteria (framework hand-back)

- [ ] `skills/plan-sync/skill.md` exists with Modes table, Hard rules, procedure covering §4.4–4.6, manifest constants §4.3, auth resolution §4.2, and the Operator handoff contract.
- [ ] Registered in all four places: `skills/README.md` table, `skills/SKILL_DEPENDENCIES.md`, `templates/cursorrules.template` § Skills, `START_HERE.md` decision tree.
- [ ] Naming protocol compliant (`plan-sync`, stable id rules).
- [ ] `bash scripts/framework-verify.sh` and `bash scripts/cursorrules-verify.sh` pass.
- [ ] Zero changes to the read-only MCP and to `project-query-setup`'s read-only rule.
- [ ] Functional check (document in hand-back): against a reachable tools-project, `@plan-sync status` returns project list; `@plan-sync dry-run - <plan>` returns a diff with `dry_run: true` and leaves task count unchanged; a confirmed `sync` on a scratch project creates milestones/tasks, and an immediate identical re-run reports zero creates.

## 6. After the framework change (consumers)

1. Tools-project: re-run thin-client deploy (`@deploy-basic - <path>`) so the repo's `.cursorrules` Skills table picks up the new row (this repo resolves skills from `AGENT_OS_SOURCE`; no other change needed).
2. First real usage: `@project-query-setup key` (if no `~/.tools-project-key`), then `@plan-sync status`, then `@plan-sync sync - .work/feedback/plans-import/plans/20260925-full-plan.md`.
3. P3 (web UI: milestone list/progress, filters, obsolete badge) is a separate tools-project iteration — not part of this instruction.
