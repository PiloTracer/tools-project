# What to adapt from Agent OS (`.ai/`) — and what not to

**Purpose:** Guide maintainers and adopters. UI Design OS **reuses patterns and agent discipline** from Agent OS; it **does not duplicate** planning, backend, or session skills.

---

## Do not copy (overlap / conflict)

| Agent OS (`.ai/`) | Why not in `.ai.ui/` |
|-------------------|----------------------|
| Skills: `plan-foundation`, `plan-master`, `code-implementation`, `session-control`, `db-migration`, `feature-spec`, `concept-run` (MOD), … | Different domain; use Agent OS `@` commands |
| `.work/` layout as UI output | UI artifacts → **`.work.ui/`** only |
| MOD-01…06 concept folders | UIS-01…09 only under `.ai.ui/concepts/` |
| Master plan / domain SPEC templates in `.work/features/` | Screen SPECs → `.work.ui/screens/` |
| Duplicate `REPLACE:` tokens for backend (migrations, API service names) | Keep in Agent OS `.cursorrules`; UI uses `REPLACE:UI_*` |

**Rule:** A skill in `.ai.ui/skills/` must not perform the same job as an Agent OS skill. Compose both in one repo instead.

---

## Copy or adapt (applies to UI / design)

| Agent OS source | UI Design OS target | Notes |
|-----------------|----------------------|--------|
| Core Principles §1–7 (`.ai/templates/cursorrules.template`) | `templates/cursorrules.ui.template` | Same honesty, evidence-first, completion gate; add UI verify gates |
| Protected files, security, git, no-attribution | Same sections in UI template | UI adds token/config paths |
| Docker § frontend / host hygiene | UI template § Docker / frontend | Align `REPLACE:SERVICE_FRONTEND` with Agent OS when both present |
| `project-bootstrap` brownfield B0 pattern | `ui-bootstrap` § B0 | overwrite-missing default; never blind overwrite |
| `.work/` skeleton pattern | `.work.ui/` + `templates/work.ui/` | Parallel tree, not nested |
| `HANDOFF.md` / `NEXT.md` structure | `HANDOFF_UI.md` / `NEXT_UI.md` | UI-specific readiness states |
| `FEATURE_STANDARD` §15 concept registry | `SCREEN_SPEC_STANDARD` §12 UIS registry | MOD vs UIS |
| `skills/README.md` naming protocol | `ui-{domain}-{role}` prefix | Prevents `@` collisions |
| `START_HERE.md` decision tree shape | `.ai.ui/START_HERE.md` | UI verbs only |
| `PROCESS_ROUTER.md` read-only router | `ui-process-router` | Route to `ui-*` or defer to `.ai` |
| `framework-verify.sh` | `scripts/framework-verify.sh` | Different required paths |
| Pointer READMEs (`plans/`, `features/`) | `plans/`, `screens/`, `context/` pointers | Point to `.work.ui/` |

---

## `.cursorrules` adoption (three scenarios)

| Scenario | Action (`@ui-bootstrap`) |
|----------|-------------------------|
| **No** `.cursorrules` | **Create** from `templates/cursorrules.ui.template` (full UI rules). If `.ai/` exists, recommend `@project-bootstrap init` first, then `cursorrules merge-block`. |
| `.cursorrules` exists, **no** `UI_DESIGN_OS_BEGIN` | **Merge** `templates/cursorrules.ui.snippet.template` after Agent OS sections — **requires user approval** in the same message (`merge-cursorrules` or `init merge-cursorrules`). |
| `.cursorrules` exists **with** UI block | **Status** only; offer `complete-tokens` to list unfilled `REPLACE:UI_*` (edits need approval). |

Agent OS remains authoritative for § Core Principles when both frameworks merged — UI block must not contradict principles 1–7.

---

## When both frameworks are present

```text
.cursorrules          ← Agent OS base (project-bootstrap) + UI_DESIGN_OS block (ui-bootstrap)
.ai/                  ← sessions, backend, master plan, MOD
.ai.ui/               ← UI skills, UIS, standards
.work/                ← engineering truth
.work.ui/             ← design / screen truth
```

See [`COHABITATION.md`](../../COHABITATION.md).
