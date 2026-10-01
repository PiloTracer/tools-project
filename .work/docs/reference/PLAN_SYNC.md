# Plan Sync — reference

One-way import of a **plan markdown file** into a tools-project project: the agent parses the
plan into a validated **manifest v1**, the API ingests it transactionally
(`POST /v1/projects/{id}/plan-import`). Plan edits flow *into* tools-project only — nothing is
ever written back to the plan file (`SPEC: .work/features/plan-sync/20260929-SPEC.md`, invariant I1).

- **Skill:** `<AGENT_OS_SOURCE>/skills/plan-sync/skill.md` (e.g.
  `/mnt/work/Projects/pilo.ai.logicbison/skills/plan-sync/skill.md`)
- **Backend:** `api/app/routers/milestones.py` (`POST /v1/projects/{id}/plan-import`),
  `api/app/services/plan_import.py`
- **Contract authority:** `.work/features/plan-sync/20260929-SPEC.md` §4 (R5–R27)

---

## Example — syncing a project's full plan

Run **inside the repository that owns the plan** (the invocation path is relative to it):

```bash
@plan-sync sync - .work/feedback/plans-import/plans/20260925-full-plan.md --project 6becd67b-1354-4fe7-914b-0363f13a0c33
```

That command syncs that plan into the project with that UUID (here: the **Mendarion** project,
slug `mendarion`, project key `MDR`). It parses the plan → builds the manifest → **dry-runs** →
prints the preview → asks for confirmation → commits in one transaction.

Preview first, commit later (writes nothing):

```bash
@plan-sync dry-run - .work/feedback/plans-import/plans/20260925-full-plan.md --project 6becd67b-1354-4fe7-914b-0363f13a0c33
```

---

## Modes

| Invocation | Effect |
|---|---|
| `@plan-sync status` | Connectivity + key + base URL, and the projects the key can reach |
| `@plan-sync dry-run - <plan path> [--project …]` | Full parse + validation + diff preview; **never commits** |
| `@plan-sync sync - <plan path> [--project …]` | Same, then commits after explicit operator confirmation |
| `@plan-sync help` | Usage and key setup pointer (`@project-query-setup key`) |

`--project` accepts a **UUID, slug, or project key**. Omit it (or pass something that is not a
UUID) and the skill resolves via `GET /v1/agent/projects`, then shows the matched project name +
id for confirmation before any POST. Ambiguous match → it asks, never guesses.

## Prerequisites

| Need | How |
|---|---|
| API key | `TOOLS_PROJECT_API_KEY`, else `~/.tools-project-key` (first non-`BASE_URL=` line), else legacy `AGENT_API_KEY` — same resolution as the MCP |
| Base URL | env `API_BASE_URL`, else the `BASE_URL=` line in the key file, else `http://localhost:8300`. Remote must be `https://…` |
| Skill reachable | the consumer repo's agent config lists the framework skills path (e.g. `opencode.json` → `skills.paths[0] = <AGENT_OS_SOURCE>/skills`) |
| Plan file | readable markdown inside the repo (the manifest's `tasks`/`milestones` tables) |
| Access | the key's owner needs **contributor or higher** on the target project |

`X-Api-Key` is accepted on the plan-import route **only** among mutating endpoints (SPEC D7);
`Bearer` JWT with the same RBAC also works.

**Finding the project id:** open the project in the UI (the UUID is in the URL) or list them —
`GET /v1/agent/projects` with the same key returns `id`, `slug`, `project_key`.

## What a commit does (SPEC R5–R20)

| Behaviour | Detail |
|---|---|
| Matching across runs | `(project_id, plan_ref)` per item (partial unique indexes) — re-syncing a revised plan is the normal workflow |
| Local status wins | a plan revision **never** reopens `done` or kills `in_progress`; divergence is reported as a conflict, not applied |
| Obsolete matrix | items absent from the plan are flagged `plan_state='obsolete'`; `in_progress`/`active` orphans are left untouched and reported |
| Reactivation | an `obsolete` item that reappears goes back to `active` (and `todo` if sync had cancelled it) |
| Deletion | **never** — obsolete items stay queryable via `plan_state=obsolete` |
| Atomicity | one transaction; failure leaves the project exactly as it was |
| Side effects | exactly one summary activity row per import; no webhook dispatches |
| Limits | `manifest_version: 1` only; ≤ 100 milestones, ≤ 500 tasks, ≤ 100 components per import |

## Reading the result

| Where | What |
|---|---|
| Milestones list | ordered by `sort_order`, each with task totals (progress) |
| Task filters | `milestone_id=<uuid>` and `plan_state=active|obsolete` on `GET /v1/projects/{id}/tasks` |
| Task detail | `milestone_id`, `plan_ref`, `plan_state` |
| Diff report | returned by every run: `{created, updated, obsolete, reactivated, conflicts[]}` |

### Refs and commit linking (important)

Imported tasks receive **allocated** refs from the project's own counter — with project key `MDR`
and *auto-prefix* enabled that is `MDR-1 … MDR-n` (`api/app/services/ref_alloc.py`). The plan's own
identifiers (`M1-T3`) are stored as `plan_ref` and are **not** commit-link addresses.

| Commit subject | Links to |
|---|---|
| `MDR-12: …` | ✅ that imported **task** |
| `MDR-T-8: …` | ✅ that **ticket** |
| `M1-T3: …` | ❌ never — the linker resolves `tasks.ref` / `tickets.ref` only (`api/app/services/commit_ref_linker.py`) |

So: read the allocated ref off the imported task (or the task list) before writing commits you
want linked. Linking itself runs during GitHub sync (poller every `GITHUB_POLL_INTERVAL_SECONDS`,
or the GitHub tab's *Sync now*).

## Troubleshooting

| Symptom | Cause / action |
|---|---|
| `401` | key missing or invalid → `@project-query-setup key` |
| `403` | the key's owner has less than contributor role on the project → ask the owner for a role |
| `404` | wrong project id |
| `400` + field list | manifest validation failed — nothing was written; fix the listed fields and re-run `dry-run` |
| `500` | import rolled back; the project is unchanged — report and stop |
| Nothing appears in the UI | the commit step was not confirmed (dry-run/preview only) — re-run `sync` and confirm |
| Tasks exist but commits don't link | the commit subject uses a `plan_ref` instead of the allocated ref (see above) |

## Non-negotiable rules (from the skill)

1. Dry-run → preview → explicit confirmation before commit; no confirmation = stop at preview.
2. The only write is the single `plan-import` POST. No DB access, no raw SQL, no new endpoints.
3. Never print, echo, or pass the key on a command line; never write key material into the repo.
4. Never edit the plan file or anything under `.work/` — sync is one-way.
5. MCP stays read-only; the REST contract is the stable layer, the skill is disposable.
