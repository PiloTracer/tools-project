# Coexistence with Agent OS (`.ai/`)

**Purpose:** Make `.ai.ui/` and `.ai/` safe to use **together** in one repository. This file is the boundary contract. If anything here conflicts with a `ui-*/skill.md` or a UI standard, the **skill / standard wins** — open a PR to fix this doc.

---

## 1. Separation of concerns

| Owns | Framework | Path | Skill prefix |
|------|-----------|------|--------------|
| Full SDLC, backend, DB, master plans, MOD concepts | Agent OS | `.ai/` | *(no prefix)* — `plan-*`, `code-*`, `session-control`, … |
| UI design system, screens, visual/a11y quality, UIS concepts | UI Design OS | `.ai.ui/` | **`ui-`** only |
| Application planning & code truth | Agent OS | `.work/` | — |
| UI design truth | UI Design OS | **`<repo-root>/.work.ui/`** (sibling to `.ai.ui/`) | — |

**Neither framework may:**

- Edit the other framework's `skills/`, `standards/`, or `concepts/` trees
- Register skills in the other framework's skill registry
- Overwrite the other framework's `HANDOFF` / `NEXT` carrier files wholesale

---

## 2. Session and git (single owner)

| Action | Use |
|--------|-----|
| Open / close day, commit policy, secrets scan on close | `@session-control` (`.ai/`) |
| UI-specific status snapshot | `@ui-process-router` or read `.work.ui/context/HANDOFF_UI.md` |
| UI iteration progress | `@ui-component-build status` + `NEXT_UI.md` |

UI verification runs at the **UI milestone boundary**, not at session close: `@ui-component-build complete` runs `@ui-plan-verify audit` (`readiness-verify` + `traceability-verify`) before updating carriers, so drift is caught at the UI boundary rather than late at `@session-control close`. CI re-runs the same scripts on push/PR (`.github/workflows/framework-verify.yml`).

On `@session-control close`, UI skills should have already updated `HANDOFF_UI.md`. Optionally append one line to `.work/context/HANDOFF.md`:

```markdown
### UI layer (see .work.ui/)
- Active UI milestone: S2 · NEXT_UI: .work.ui/plans/NEXT_UI.md
- Screen-spec-ready: yes · Last visual verify: pass 2026-05-23
```

---

## 3. Planning and SPECs (no duplicate artifacts)

| Artifact type | Agent OS | UI Design OS |
|---------------|----------|--------------|
| Foundation / master **implementation** plan | `.work/plans/foundation/`, `full/*-full-plan.md` | — |
| UI design foundation (tokens, patterns, screen map) | — | `.work.ui/plans/foundation/` |
| Domain / API feature SPEC | `.work/features/<slug>/YYYYMMDD-SPEC.md` | — |
| Screen / flow SPEC | — | `.work.ui/screens/<slug>/YYYYMMDD-SCREEN-SPEC.md` |
| ADR (any layer) | `.work/decisions/` | UI-specific ADRs may live here **or** `.work.ui/decisions/` — pick one per repo in HANDOFF; default **`.work/decisions/`** with `ui-` slug prefix |

**Linking:** Screen SPECs reference domain SPECs by path when a screen implements FRs — never duplicate API contracts in the screen SPEC.

---

## 4. Implementation: who builds what

| Work | Primary skill |
|------|----------------|
| React/Vue/Svelte components, styles, Storybook, visual tests | `@ui-component-build` |
| API, services, migrations, non-UI integration | `@code-implementation` |
| Same PR touches both | Run **both** task gates; `@code-implementation` owns backend files; `@ui-component-build` owns UI file list |

**MOD vs UIS:**

- **MOD-06** (`@concept-run - MOD-06`) — required for agent-assisted **application** code per `.ai/`.
- **UIS-06** (`@ui-concept-run - UIS-06`) — required for agent-assisted **UI** diffs per `.ai.ui/`.
- Running one does **not** satisfy the other.

---

## 5. Cursor rules (one file, two install modes)

Agent OS owns the **base** `.cursorrules` when both frameworks are used (`templates/cursorrules.template` via `@project-bootstrap`).

UI Design OS ships:

| Template | Use when |
|----------|----------|
| `templates/cursorrules.ui.template` | No `.cursorrules` — full UI rules + Core Principles 1–7 |
| `templates/cursorrules.ui.snippet.template` | `.cursorrules` exists — append block between `UI_DESIGN_OS_BEGIN` / `END` |

**Install (`@ui-bootstrap`):**

| Situation | Action |
|-----------|--------|
| Missing `.cursorrules` | **Create** full template (no permission needed for missing file) |
| Exists, no UI block | **Merge** snippet — requires user approval (`init merge-cursorrules`) |
| Exists with UI block | **Status** + list unfilled `REPLACE:UI_*`; fill with user approval |

```bash
bash .ai.ui/scripts/cursorrules-ui.sh status
bash .ai.ui/templates/bootstrap.sh merge-cursorrules   # after user approves
```

**Rules:**

1. One `.cursorrules` at repo root — no `.cursorrules.ui` unless the team explicitly adopts that.
2. UI placeholders: `REPLACE:UI_*` only — do not collide with Agent OS `REPLACE:` tokens.
3. Core Principles 1–7 apply to all work; UI Completion Gate adds visual/a11y/UIS-06 (see full template).
4. Protected files: union both lists.

**What we adapted from Agent OS:** honesty, evidence-first, completion gate, Docker frontend hygiene, git/attribution — **not** backend skills or `.work/` planning. See [`docs/adoption/FROM_AGENT_OS.md`](docs/adoption/FROM_AGENT_OS.md).

---

## 6. Placeholder map (no collisions)

| UI Design OS | Agent OS | Notes |
|--------------|----------|-------|
| `{WORK_UI_ROOT}` → `.work.ui/` | `{WORK_ROOT}` → `.work/` | Different trees |
| `{UI_SKILLS_ROOT}` → `.ai.ui/skills/` | `{SKILLS_ROOT}` → `.ai/skills/` | |
| `{UI_STANDARDS_ROOT}` → `.ai.ui/standards/` | `.ai/standards/` | |
| `{UI_CONCEPTS_ROOT}` → `.ai.ui/concepts/` | `{CONCEPTS_ROOT}` → `.ai/concepts/` | MOD ≠ UIS |
| `{SCREEN_SPEC_ROOT}` → `.work.ui/screens/` | `{FEATURE_SPEC_ROOT}` → `.work/features/` | |
| `{UI_ITERATION_CARRIER}` → `.work.ui/plans/NEXT_UI.md` | `{ITERATION_CARRIER}` → `.work/plans/NEXT.md` | |
| `{HANDOFF_UI}` → `.work.ui/context/HANDOFF_UI.md` | `{HANDOFF}` → `.work/context/HANDOFF.md` | |

---

## 7. Bootstrap order (recommended)

```text
1. bash .ai/templates/bootstrap.sh          # if Agent OS not yet present
2. bash .ai.ui/templates/bootstrap.sh         # creates .work.ui/ only
3. Merge cursorrules UI snippet
4. @plan-foundation greenfield                # product/engineering (optional order)
5. @ui-design-foundation greenfield           # UI layer (can run in parallel after bootstrap)
```

`ui-bootstrap` **must not** overwrite `.cursorrules` or `.work/` — only missing `.work.ui/` files and optional snippet instructions.

---

## 8. Failure modes to avoid

| Anti-pattern | Fix |
|--------------|-----|
| Two session-close rituals | Only `@session-control close` commits |
| Screen SPEC in `.work/features/` | Move to `.work.ui/screens/` |
| `ui-code-implementation` skill duplicating `code-implementation` | Use `@ui-component-build` + `@code-implementation` |
| Renaming MOD prompts to UIS in `.ai/concepts/` | Keep MOD in `.ai/`, UIS in `.ai.ui/` |
| Agent OS `NEXT.md` iteration for pure UI polish | Use `NEXT_UI.md` § Current UI iteration |

---

## 9. Verification checklist (both frameworks present)

- [ ] `.ai/` and `.ai.ui/` are siblings; neither is nested inside the other
- [ ] All skill invocations use correct prefix (`@session-control` vs `@ui-screen-spec`)
- [ ] `.cursorrules` contains `UI_DESIGN_OS_BEGIN` block
- [ ] `HANDOFF.md` links to `HANDOFF_UI.md`
- [ ] No skill id exists in both `skills/README.md` files

---

**Maintenance:** Update this file when adding a skill that touches `.work/` or `.cursorrules`.
