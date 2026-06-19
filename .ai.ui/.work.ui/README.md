# `.work.ui/` — UI project working tree

> **This `.work.ui/` tree is a demo skeleton inside the UI Design OS framework repo.** When you bootstrap into your own repo (`bash .ai.ui/templates/bootstrap.sh`), the same layout is created at **your application repo root** (sibling to `.ai.ui/` and `.ai/`) and filled in by **`ui-*` skills** as you work. This README is permanent navigation.

**Purpose:** All **project-specific UI** artifacts: design foundation, screen SPECs, UI iteration state, design-system catalog, UI registries.

**Agnostic** process (skills, standards, concepts, inputs) lives under **`.ai.ui/`** only.

**Location rule:** `{WORK_UI_ROOT}` always resolves to **`<repo-root>/.work.ui/`** — never under `.ai.ui/`. Same pattern as Agent OS `{WORK_ROOT}` → `<repo-root>/.work/`.

## Layout

| Path | Contents |
|------|----------|
| `.work.ui/context/` | `HANDOFF_UI.md` — UI design state (updated by `ui-*` skills; session bookends via `@session-control`) |
| `.work.ui/plans/` | Foundation docs 01–04, optional UI roadmap (`full/`), registries, `NEXT_UI.md` |
| `.work.ui/screens/<slug>/` | Screen SPECs (`YYYYMMDD-SCREEN-SPEC.md`) per SCREEN_SPEC_STANDARD |
| `.work.ui/design-system/` | `CATALOG.md` — primitives registry (`@ui-design-system`) |
| `.work.ui/decisions/` | UI ADRs (or use `.work/decisions/` with `ui-` prefix — see HANDOFF_UI) |
| `.work.ui/prompts/` | Design questionnaires; optional user scratch (not read by skills unless named) |

## Placeholder map

Configured in `.cursorrules` UI block (`UI_DESIGN_OS_BEGIN`):

| Placeholder | Resolved path |
|-------------|---------------|
| `{WORK_UI_ROOT}` | `.work.ui/` |
| `{UI_PLANS_ROOT}` | `.work.ui/plans/` |
| `{SCREEN_SPEC_ROOT}` | `.work.ui/screens/` |
| `{UI_ITERATION_CARRIER}` | `.work.ui/plans/NEXT_UI.md` |
| `{UI_ROADMAP}` | `.work.ui/plans/full/*-ui-roadmap.md` (latest **Approved**, when used) |
| `{HANDOFF_UI}` | `.work.ui/context/HANDOFF_UI.md` |
| `{UI_DECISIONS_ROOT}` | `.work.ui/decisions/` |
| `{UI_PROMPTS_ROOT}` | `.work.ui/prompts/` |
| `{UI_DESIGN_SYSTEM_ROOT}` | `.work.ui/design-system/` |

## Quick pick-up

1. `.work.ui/context/HANDOFF_UI.md`
2. `.work.ui/plans/NEXT_UI.md`
3. Active screen SPEC under `.work.ui/screens/`

Operator entry: `.ai.ui/START_HERE.md` · Coexistence: `.ai.ui/COHABITATION.md`

## Bootstrap

From **application repo root** (parent of `.ai.ui/`):

```bash
bash .ai.ui/templates/bootstrap.sh
```

Or `@ui-bootstrap init`.

Foundation docs **01–04** are created by `@ui-design-foundation greenfield` (templates under `.ai.ui/templates/work.ui/plans/foundation/`).

## Skills that write here

| Skill | Typical outputs under `.work.ui/` |
|-------|-----------------------------------|
| `ui-bootstrap` | Skeleton files (copy-if-missing) |
| `ui-design-foundation` | `plans/foundation/01–04`, registries, HANDOFF_UI readiness |
| `ui-screen-spec` | `screens/<slug>/YYYYMMDD-SCREEN-SPEC.md` |
| `ui-component-build` | `plans/NEXT_UI.md` iteration block, HANDOFF_UI |
| `ui-design-system` | `design-system/CATALOG.md` |
| `ui-visual-verify` / `ui-accessibility-audit` | Findings in HANDOFF_UI / task Notes (no duplicate truth) |

**Do not** write UI SPECs or `NEXT_UI.md` under `.ai.ui/` or inside `.ai.ui/templates/` except when editing framework templates.
