# `.work/` - project working tree

> **This `.work/` tree is a demo skeleton inside the Agent OS framework repo.** When you bootstrap Agent OS into your own repo (`bash .ai/templates/bootstrap.sh`), the same layout is created at your repo root and the files are filled in by skills (**`@plan-foundation`**, **`@plan-master`**, **`@session-control`**, **`@code-implementation`**, **`@feature-spec`**) as you work. This README itself is permanent navigation - it does not change per session.

**Purpose:** All **project-specific** artifacts: plans, SPECs, ADRs, prompts, and session handoff.

**Agnostic** process (skills, standards, concepts, guides) lives under **`.ai/`** only.

## Layout

| Path | Contents |
|------|----------|
| `.work/plans/` | Foundation docs (`*-01-*` … `*-04-*`), master plan (`full/*-full-plan.md`), registries, `NEXT.md`, operations runbooks |
| `.work/features/<slug>/` | Feature SPECs, amendments, `CHANGELOG.md` per FEATURE_STANDARD |
| `.work/prompts/` | Decision questionnaires; optional user scratch (`initial.md` - **not read by skills** unless user names it) |
| `.work/decisions/` | ADRs (`YYYYMMDD-NNN-*.md`) |
| `.work/context/` | `HANDOFF.md` - read/write via `@session-control` |
| `.work/reports/` | Optional verify snapshots (e.g. code-registry audit from `@plan-verify coverage`) |
| `.work/analysis/` | Generated investigation / audit markdown (gap analyses, session postmortems, parity reports) |
| `.work/scripts/` | Markdown runbooks for one-off operational scripts (backfills, repairs); code lives in application tree |

## Placeholder map

Configured in `.cursorrules` § Workflow bootstrap:

| Placeholder | Resolves to |
|-------------|-------------|
| `{WORK_ROOT}` | `.work/` |
| `{PLANS_ROOT}` | `.work/plans/` |
| `{FEATURE_SPEC_ROOT}` | `.work/features/` |
| `{PROMPTS_ROOT}` | `.work/prompts/` |
| `{DECISIONS_ROOT}` | `.work/decisions/` |
| `{ITERATION_CARRIER}` | `.work/plans/NEXT.md` |
| `{MASTER_PLAN}` | `.work/plans/full/*-full-plan.md` (latest **Approved**) |
| `{HANDOFF}` | `.work/context/HANDOFF.md` |

## Quick pick-up

1. `.work/context/HANDOFF.md`
2. `.work/plans/NEXT.md`

Operator entry: `.ai/START_HERE.md`

## Bootstrap

If this tree was created empty, run from repo root:

```bash
bash .ai/templates/bootstrap.sh
```

Or invoke `@project-bootstrap init`.

Foundation docs **01–04** are created by `@plan-foundation greenfield` (templates under `.ai/templates/work/plans/foundation/`).
