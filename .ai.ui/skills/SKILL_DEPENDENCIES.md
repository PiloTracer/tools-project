# UI skill dependency graph

**Purpose:** Gates for **ui-*** skills only. Agent OS gates live in `.ai/skills/SKILL_DEPENDENCIES.md`.

## Work tree path resolution (mandatory)

**Repository root** (`.git/`, `.cursorrules`) is **not** `{WORK_UI_ROOT}`. All `ui-*` skills resolve paths from **repo root** (parent of `.ai.ui/` in nested layouts).

| Placeholder | Resolved path | Common wrong path |
|-------------|---------------|-------------------|
| `{WORK_UI_ROOT}` | `.work.ui/` | `.ai.ui/.work.ui/`, `work.ui/`, paths under `templates/work.ui/` |
| `{HANDOFF_UI}` | `.work.ui/context/HANDOFF_UI.md` | `context/HANDOFF_UI.md`, `HANDOFF_UI.md` at repo root |
| `{UI_ITERATION_CARRIER}` | `.work.ui/plans/NEXT_UI.md` | `plans/NEXT_UI.md`, Agent OS `NEXT.md` |
| `{SCREEN_SPEC_ROOT}` | `.work.ui/screens/` | `.work/features/`, `.ai.ui/screens/` |
| `{UI_PLANS_ROOT}` | `.work.ui/plans/` | `plans/` without `.work.ui/` |
| `{UI_DECISIONS_ROOT}` | `.work.ui/decisions/` | `.ai.ui/decisions/` (pointer only) |
| `{UI_DESIGN_SYSTEM_ROOT}` | `.work.ui/design-system/` | catalog only in `.ai.ui/` |
| `{UI_ROADMAP}` | `.work.ui/plans/full/*-ui-roadmap.md` | `.work/plans/full/*-full-plan.md` |

**Write rule:** Every skill artifact (SPECs, foundation docs, `NEXT_UI` iteration, `CATALOG.md`, registry rows) MUST be written under the **Resolved path** column. Framework templates under `.ai.ui/templates/work.ui/` are **copy sources only** — not the live project tree.

**Read rule:** In mandatory-read tables and blocked reports, use resolved paths. Shorthand `HANDOFF_UI` / `NEXT_UI` means the paths above.

---

## Readiness states

```text
ui-bootstrap (scaffold)
        ↓
ui-foundation-complete  →  screen-spec-ready  →  ui-implementation-ready
   ui-design-foundation      ui-design-foundation certify
                             ui-component-build + verify
```

| State | Certified by | Unlocks |
|-------|--------------|---------|
| *(scaffold)* | `@ui-bootstrap init` | `@ui-design-foundation greenfield` |
| **ui-foundation-complete** | `@ui-design-foundation status` | `certify` |
| **screen-spec-ready** | `@ui-design-foundation certify screen-spec-ready` | `@ui-screen-spec create` |
| **ui-implementation-ready** | `@ui-component-build status` + verify pass on active milestone | Broad UI iteration |

---

## Dependency matrix (summary)

| Skill / mode | Depends on | Gate |
|--------------|------------|------|
| **ui-bootstrap** `init` | `.ai.ui/` present; must not overwrite `.work/` or base `.cursorrules` | - |
| **deploy-files** `copy` | Source git repo with `.ai.ui/` as root; target parent dir must exist | - |
| **deploy-repo** `clone` / `archive` | Source git repo; origin remote required for clone mode | - |
| **ui-design-foundation** `greenfield` | `{HANDOFF_UI}`; UI standards paths in `.cursorrules` snippet | Recommended: `@ui-bootstrap init` |
| **ui-design-foundation** `probe` | None; interrogates + fills foundation gaps. Engine: [`probe-protocol.md`](probe-protocol.md). Ledger `{UI_PLANS_ROOT}/foundation/PROBE_LEDGER.md` | Recommended before `certify` when understanding is thin |
| **ui-design-foundation** `certify screen-spec-ready` | **ui-foundation-complete: yes** | **Required** |
| **ui-component-build** `probe` | None; interactive roadmap-completeness check before `ui-implementation-ready`. Ledger `{UI_PLANS_ROOT}/full/PROBE_LEDGER.md` | Recommended before broad iteration |
| **ui-screen-spec** `intake` | None (free-text front door); classifies + routes, only writes a SPEC when class=`local` | - (records to `NEXT_UI` § Intake queue) |
| **ui-screen-spec** `create` | SCREEN_SPEC_STANDARD; **screen-spec-ready** | **Required** (warn if no) |
| **ui-component-build** `plan` | Approved screen SPEC(s) for milestone | **Required** |
| **ui-component-build** `start` / `continue` | Valid `NEXT_UI.md` UI iteration; screen-spec-ready or waiver in HANDOFF_UI | **Required** |
| **ui-component-build** `complete` | `@ui-visual-verify milestone` + `@ui-accessibility-audit milestone` + `@ui-plan-verify audit` pass | **Required** |
| **ui-component-build** `complete` (craft tier ≥ refined) | `@ui-concept-run - UIS-07` on milestone diff | **Required** |
| **ui-component-build** `complete` (any screen) | `@ui-concept-run - UIS-08` on milestone diff | **Required** |
| **ui-component-build** `complete` (analytical dashboard) | `@ui-concept-run - UIS-09` on milestone diff | **Required** |
| **ui-visual-verify** / **ui-accessibility-audit** | Active UI milestone in NEXT_UI | Per skill |
| **ui-concept-run** `run` | UIS trigger table | Per `.ai.ui/concepts/README.md` |
| **ui-plan-verify** | - | Read-only (runs verifiers; reports + routes, never fixes) |
| **ui-process-router** | - | Read-only |
| **ui-project-approach** | - | Read-only (optional write to HANDOFF_UI on user request) |
| **ui-style-stack** `set` | Recommended: before `ui-design-foundation greenfield` | Warn if missing |
| **ui-component-build** `start` | Active style stack in HANDOFF_UI or user-named in message | Recommended |

---

## Redirect cheat sheet

| User tried | Run next |
|------------|----------|
| `@deploy-files copy - /path` | `bash scripts/deploy-files.sh /path` |
| `@deploy-repo clone - /path` | `bash scripts/deploy-repo.sh clone /path` |
| `@deploy-repo archive - /path` | `bash scripts/deploy-repo.sh archive /path` |
| `@ui-screen-spec create` | `@ui-design-foundation certify screen-spec-ready` |
| `@ui-component-build start` | `@ui-component-build plan - S{N}` |
| Free-text UI request, unsure where it goes | `@ui-screen-spec intake - <sentence>` |
| Brand/users/scope vague; "do you understand the UI?" | `@ui-design-foundation probe` (then `certify`) |
| Roadmap completeness unclear before broad build | `@ui-component-build probe` |
| Audit readiness (verifiers + coverage + orphans) | `@ui-plan-verify audit` |
| UI session close / commit | `@session-control close` (Agent OS) |
| Backend migration | `@db-migration` (Agent OS) — not a ui-* skill |

---

## Command vocabulary (canonical verbs)

One verb set across `ui-*` skills. New verbs go here first, then into the matrix.

| Verb | Skills | Writes? | Meaning |
|------|--------|---------|---------|
| `init` | ui-bootstrap | yes | Scaffold `.work.ui/` + cursorrules |
| `copy` | deploy-files | yes | Deploy `.ai.ui` files into target project |
| `clone` / `archive` | deploy-repo | yes | Full git-based deploy of `.ai.ui` repo |
| `set` | ui-style-stack | yes (HANDOFF_UI) | Record active style stack |
| `greenfield` | ui-design-foundation | yes | Create foundation docs 01–04 |
| `probe` | ui-design-foundation, ui-component-build | yes (docs + ledger) | Interrogate until coverage target; sub-modes `- status`, `- until ready` |
| `intake` | ui-screen-spec | records only | Classify + route a free-text request |
| `create` | ui-screen-spec | yes (SPEC) | New screen SPEC (slug or derived) |
| `review` / `amend` | ui-screen-spec | yes | Check / amend a SPEC |
| `plan` | ui-component-build | yes (NEXT_UI) | Write a milestone iteration |
| `start` / `continue` | ui-component-build | yes (code) | Execute iteration tasks |
| `complete` | ui-component-build | yes | Close milestone after verify gates |
| `init` | ui-design-system | yes (CATALOG) | Primitives catalog from doc 03 |
| `run` | ui-concept-run | varies | Run a UIS prompt |
| `milestone` / `uncommitted` | ui-visual-verify, ui-accessibility-audit | read | Verify before ship |
| `audit` / `probe-coverage` / `traceability` | ui-plan-verify | read | Report + route readiness gaps |
| `status` | most skills | read | Read-only state |
| *(question)* | ui-process-router, ui-project-approach | read | Classify / orient |

---

## Blocked report shape

```markdown
## @<ui-skill> <command> - blocked (prerequisite)
**Required:** …
**Detected:** …
**Run first:** `@…`
```
