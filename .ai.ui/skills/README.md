# UI Design OS skills (`.ai.ui/skills/`)

Portable, tool-agnostic UI workflows. Each skill is a folder with `skill.md` (+ optional `reference.md`).

**Identifiers:** Folder name = stable id = `@` handle. **All ids use prefix `ui-`** — never register unprefixed names here (reserved for Agent OS `.ai/skills/`).

**Invocation:** ASCII hyphen `-` between verb and argument: `@ui-screen-spec create - checkout`

**Work tree:** `{WORK_UI_ROOT}` = **`<repo-root>/.work.ui/`** (sibling to `.ai.ui/` — same level as `.ai/` + `.work/`). Skills **must not** write project artifacts under `.ai.ui/`. See [`SKILL_DEPENDENCIES.md`](SKILL_DEPENDENCIES.md) § Work tree path resolution.

**Session owner:** Agent OS `@session-control` only — see [`COHABITATION.md`](../COHABITATION.md).

---

## Naming protocol

| Rule | Requirement |
|------|----------------|
| Shape | `ui-{domain}-{role}` or `ui-{role}` when domain is obvious |
| Stable id | Folder = YAML `name:` = `@` handle |
| Avoid | Names that collide with Agent OS (`plan-master`, `code-implementation`, `session-control`, …) |

---

## Registered skills

| Skill id | Folder | Role |
|----------|--------|------|
| ui-bootstrap | `ui-bootstrap/` | Scaffold `.work.ui/`; create/merge `.cursorrules`; `DOCS_UI_STACK.md` |
| ui-design-foundation | `ui-design-foundation/` | Tokens, patterns, screen map; certifies **screen-spec-ready** |
| ui-screen-spec | `ui-screen-spec/` | Author/review screen SPECs |
| ui-component-build | `ui-component-build/` | UI iteration from `NEXT_UI.md` |
| ui-visual-verify | `ui-visual-verify/` | Visual/token regression audits |
| ui-accessibility-audit | `ui-accessibility-audit/` | WCAG-oriented checks |
| ui-design-system | `ui-design-system/` | Primitives catalog and Storybook discipline |
| ui-concept-run | `ui-concept-run/` | Run UIS-01…07 prompts |
| ui-plan-verify | `ui-plan-verify/` | Read-only audit: verifiers, probe coverage, screen→milestone traceability |
| ui-process-router | `ui-process-router/` | Read-only UI process Q&A |
| ui-project-approach | `ui-project-approach/` | Archetype + skill chain + pattern pointers (read [`APPROACH.md`](../APPROACH.md)) |
| ui-style-stack | `ui-style-stack/` | Active stack: tailwind / css-modules / vanilla-css / styled-components |

**Typical flow:** `@ui-bootstrap init` → `@ui-project-approach - <what you're building>` → `@ui-style-stack set - <stack>` → `ui-design-foundation greenfield` → … → verify.

**Patterns (not skills):** [`standards/20260523-UI-PATTERNS.md`](../standards/20260523-UI-PATTERNS.md) · **Approach:** [`APPROACH.md`](../APPROACH.md)

**Gates:** [`SKILL_DEPENDENCIES.md`](SKILL_DEPENDENCIES.md)

**Orientation:** `@ui-process-router - <question>` · [`START_HERE.md`](../START_HERE.md)
