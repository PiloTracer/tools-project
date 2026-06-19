# Agent skills (`.ai/skills/`)

Portable, tool-agnostic workflows. Each skill is a folder with `skill.md` (+ optional `reference.md`). **Repo doc map:** [`.ai/README.md`](../README.md).

**Identifiers:** Folder name = stable skill id (YAML `name:` in `skill.md` must match). Cursor `@` mentions use that id (e.g. `@dev-stack`, `@code-implementation`).

**Invocation punctuation:** Use ASCII hyphen `-` between verb and argument (`@code-implementation plan - M1`). Not em dash `—`. See [`SKILL_DEPENDENCIES.md`](SKILL_DEPENDENCIES.md).

**Work tree paths:** `{WORK_ROOT}` = `.work/` at repo root — never `context/` or `plans/` without the `.work/` prefix. See [`SKILL_DEPENDENCIES.md` § Work tree path resolution](SKILL_DEPENDENCIES.md#work-tree-path-resolution-mandatory).

---

## Naming protocol

Use for **new** skills and for any **rename** (update `.cursorrules`, this README, HANDOFF, `NEXT.md`, cross-skill links, and plan prose in one pass).

| Rule | Requirement |
|------|----------------|
| **Shape** | `{domain}-{role}` in **kebab-case** (lowercase ASCII, hyphens). Prefer **two** segments; use three only to avoid ambiguity. |
| **domain** | Broad area: `plan`, `session`, `db`, `code`, `compose`, or (rarely) a product lane. |
| **role** | What the skill does: `foundation`, `master`, `control`, `migration`, `implementation`, `stack`, … |
| **Stable id** | Folder name = `name:` in frontmatter = `@` handle = row key in `.cursorrules` § Skills. |
| **Avoid** | File extensions in the id (`.sh`), vague names (`helper`), vendor prefixes (`cursor-`). |
| **Artifacts** | Master plan **files** keep the historical glob `*-full-plan.md` under `{PLANS_ROOT}/full/`; that is **not** the same string as the **plan-master** skill id. |

---

## Registered skills

| Skill id | Folder | Role |
|----------|--------|------|
| deploy-files | `deploy-files/` | **Files-only deploy:** rsync `.ai/` to target project; excludes VCS artifacts |
| deploy-repo | `deploy-repo/` | **Full repo deploy:** git clone (mirror) or archive (snapshot with `.github`) |
| plan-foundation | `plan-foundation/` | **Orchestrator:** P0–P6 foundation gates, ADRs, SPECs, registries; **probe** (adaptive understanding loop); certifies **plan-master-ready** |
| plan-master | `plan-master/` | Master implementation plan, **probe** (plan-completeness loop), integrity, traceability; certifies **implementation-ready** |
| plan-verify | `plan-verify/` | Plan audits: foundation, master, alignment, **coverage** (code→SPEC), **brownfield** (framework slots) |
| plan-repair | `plan-repair/` | Fix plan gaps; **brownfield synthesis** from code/README/ROADMAP; optional formal certify later |
| session-control | `session-control/` | Session open/close, HANDOFF, NEXT, optional git |
| db-migration | `db-migration/` | Idempotent numbered SQL migration scripts; no version table, no chain conflicts |
| code-implementation | `code-implementation/` | Iteration execution: `NEXT.md` scope, task gates, completion |
| code-verify | `code-verify/` | Verification: milestone, uncommitted, last commit/push |
| code-repair | `code-repair/` | Remediate verifier/migration/SPEC findings; mandatory re-verify |
| dev-stack | `dev-stack/` | Isolated Docker Compose helper (`bin/start.sh`); safe `.env` handling |
| process-router | `process-router/` | Read-only router: process questions → skill, guide, or standard (no writes) |
| feature-spec | `feature-spec/` | Author, review, amend feature SPECs per FEATURE_STANDARD |
| concept-run | `concept-run/` | Run MOD-01…MOD-06 concept prompts; attach output to PR/NEXT/SPEC |
| project-bootstrap | `project-bootstrap/` | Bootstrap `.work/`, `.cursorrules`, `DOCS_TECH_STACK.md` from templates |

**Typical flow (greenfield):** `@project-bootstrap init` → `plan-foundation greenfield` → `certify plan-master-ready` → `plan-master greenfield` → `plan-master status` (implementation-ready) → `code-implementation plan` → `code-implementation start/continue/complete`.

**Canonical verb vocabulary:** see [SKILL_DEPENDENCIES.md § Canonical command vocabulary](SKILL_DEPENDENCIES.md#canonical-command-vocabulary). Every skill uses `status` for read-only state, `init` for one-time setup, and so on - no skill invents bespoke verbs.

**Shared engine docs (not skills):** [`SKILL_DEPENDENCIES.md`](SKILL_DEPENDENCIES.md) (gate graph) and [`probe-protocol.md`](probe-protocol.md) (the adaptive `probe` loop reused by `plan-foundation` and `plan-master`) are single-source-of-truth fragments that skills **link** rather than restate. They are files, not skill folders, so they are not counted in the 16-skill registry.

**Skill prerequisites (gates):** [SKILL_DEPENDENCIES.md](SKILL_DEPENDENCIES.md) - which modes **stop** if an upstream step was skipped (e.g. `@plan-master greenfield` before `@plan-foundation certify plan-master-ready`).

**Orientation:** `@process-router - <question>` when lost; `@session-control status` for repo snapshot.

**Do not** ask plan-foundation for implementation-ready - use `plan-master status`.

Registered in `.cursorrules` § Skills.

---

## Workflow guides (process, not skills)

Portable **human + agent** tutorials (bootstrap placeholders, end-to-end workflow, plan repair, observability in verify) live under **`.ai/docs/guides/workflows/`**. See [README.md](../docs/guides/workflows/README.md). Guides explain how **concept packs**, **feature SPECs**, **skills**, and **traceability** connect; skills remain the executable orchestration layer.

---

## Further reading

- **Operator decision tree (read when lost):** [`.ai/START_HERE.md`](../START_HERE.md)
- **Concept pack + invocation triggers:** [`.ai/concepts/README.md`](../concepts/README.md)
