# START HERE — UI operator decision tree

**Purpose:** Answer fast: *"What do I do right now for front-end / design work?"*

**Read when:** You sit down on UI, pick up a screen, or feel lost in tokens vs components vs specs.

**Rule:** If this file contradicts a `ui-*/skill.md` or a UI standard, the **skill / standard wins**.

**Paths:** In an app repo, prefix with `.ai.ui/`. When this repo **is** the git root, use `START_HERE.md`, `skills/` with no prefix. See [README § Path convention](README.md#path-convention-read-this-once).

**Using Agent OS too?** Read [`COHABITATION.md`](COHABITATION.md) once.

---

## 0. Three things to know

1. **UI truth lives in `.work.ui/`** — `HANDOFF_UI.md`, `NEXT_UI.md`, screen SPECs under `screens/`.
2. **Sessions still belong to Agent OS** — `@session-control start` / `close` from `.ai/`; UI skills do not commit unless your user rules say otherwise.
3. **Skills orchestrate UI work. Standards bind tokens and components. UIS concepts gate visual quality and craft.**

---

## 0b. Great-looking UI (any product)

Follow [`examples/INDEX.md`](examples/INDEX.md) playbook. **S0 primitives before S1 screens** when craft tier ≥ refined. Craft bar: [`standards/20260523-SURFACE-AND-CONTROL-CRAFT.md`](standards/20260523-SURFACE-AND-CONTROL-CRAFT.md).

---

## 1. Decision tree

```text
┌──────────────────────────────────────────┐
│  Where am I on UI?                        │
└──────────────────────────────────────────┘
       │
       ├── "Bootstrap UI layer / empty .work.ui"  ──► @ui-bootstrap init · init merge-cursorrules
       │
       ├── "Lost / how do I…?" (UI only)          ──► §2 · @ui-process-router
       │
       ├── "Start UI foundation (tokens, map)"    ──► §3
       │
       ├── "Spec a screen or flow"                 ──► §4
       │
       ├── "I have a UI idea (free text)"          ──► @ui-screen-spec intake - <sentence>
       │
       ├── "Build / polish UI components"         ──► §5
       │
       ├── "Check visuals / a11y before ship"     ──► §6
       │
       └── "Understand the UI system"             ──► §7
```

---

## 2. Resume / orient (≤5 minutes)

| Need | Command / file |
|------|----------------|
| UI process question | `@ui-process-router - <question>` |
| Where is UI work? | `.work.ui/context/HANDOFF_UI.md` + `.work.ui/plans/NEXT_UI.md` |
| Full repo session (Agent OS) | `@session-control status` + `.work/context/HANDOFF.md` |
| UI iteration snapshot | `@ui-component-build status` |
| Design foundation done? | `@ui-design-foundation status` |

**Ground truth order:** `HANDOFF_UI.md` → `NEXT_UI.md` (§ Recommended next) → active screen SPEC.

---

## 3. Classify & stack (before foundation)

| You need… | Run |
|-----------|-----|
| What kind of product? | `@ui-project-approach - <one sentence>` → reads [`APPROACH.md`](APPROACH.md) |
| Tailwind vs CSS Modules vs … | `@ui-style-stack set - tailwind` → [`style-stacks/`](style-stacks/README.md) |

## 4. UI foundation (once per product)

| You need… | Run |
|-----------|-----|
| Brand-new UI layer | `@ui-design-foundation greenfield` |
| Agent should ask until it understands the UI (vague brand/users/scope) | `@ui-design-foundation probe` (adaptive loop; fills gaps) |
| Check progress | `@ui-design-foundation status` |
| Ready to author screen SPECs | `@ui-design-foundation certify screen-spec-ready` |
| Design system primitives doc | `@ui-design-system init` (after tokens exist) |

**Readiness:**

```text
ui-foundation-complete  →  screen-spec-ready  →  ui-implementation-ready
   (ui-design-foundation)   (certify)            (ui-component-build + verify)
```

---

## 5. Screen SPECs

| You need… | Run |
|-----------|-----|
| Free-text UI idea (don't know where it goes) | `@ui-screen-spec intake - <free sentence>` (classifies + routes) |
| New screen / flow SPEC | `@ui-screen-spec create - <slug>` |
| Review before build | `@ui-screen-spec review - <path>` |
| UIS prompts in SPEC | List UIS-01…09 in SPEC §12 Concept registry |
| Bind example patterns | SPEC §13: `exampleIds` + `extractedRules` from `examples/*/manifest.md` |

Screen SPECs live under **`.work.ui/screens/<slug>/`** — not `.work/features/`.

---

## 6. Build UI (iteration loop)

**Before code:**

```text
@session-control start                    # from .ai/
@ui-component-build status
```

If no valid UI iteration block:

```text
@ui-component-build plan - S0    # primitives first (craft tier ≥ refined)
@ui-component-build plan - S1    # screens from approved SPECs
```

**Loop:**

```text
@ui-component-build start
@ui-component-build continue
@ui-visual-verify milestone
@ui-accessibility-audit milestone
@ui-component-build complete
```

**Per-task obligations:**

| Obligation | Source |
|------------|--------|
| Read screen SPEC before editing | `ui-component-build` § Start protocol |
| Run UI task gate (lint, type, unit/visual tests per `.cursorrules`) | UI task gate |
| Agent-assisted UI diff → UIS-06 | `@ui-concept-run - UIS-06` |
| Craft tier ≥ refined → UIS-07 | `@ui-concept-run - UIS-07` |
| Any screen before ship → UIS-08 | `@ui-concept-run - UIS-08` |
| Analytical dashboard → UIS-09 | `@ui-concept-run - UIS-09` |
| Cross-screen token change → UIS-04 | `@ui-concept-run - UIS-04` |

Full-stack tasks: also follow `@code-implementation` for non-UI files ([`COHABITATION.md`](COHABITATION.md)).

---

## 7. Verify before ship

| Check | Command |
|-------|---------|
| Visual / token drift | `@ui-visual-verify milestone` |
| Accessibility | `@ui-accessibility-audit milestone` |
| Dirty UI tree | `@ui-visual-verify uncommitted` |
| Applicable UIS rows pending | `@ui-concept-run status` |
| Intuitive UX (all screens) | `@ui-concept-run - UIS-08` |
| Data viz quality (analytical dashboards) | `@ui-concept-run - UIS-09` |
| Plan/roadmap readiness (verifiers + probe coverage + orphan screens) | `@ui-plan-verify audit` |

---

## 8. Reading order

| Step | File | Why |
|------|------|-----|
| 1 | [`COHABITATION.md`](COHABITATION.md) | If `.ai/` present |
| 2 | `.work.ui/context/HANDOFF_UI.md` | UI session state |
| 3 | `.work.ui/plans/NEXT_UI.md` | Next UI action |
| 4 | [`APPROACH.md`](APPROACH.md) | Archetype + skill chain |
| 5 | [`skills/README.md`](skills/README.md) | `ui-*` registry |
| 6 | [`concepts/README.md`](concepts/README.md) | UIS trigger table |
| 7 | The `ui-*/skill.md` you invoke | Verbs and gates |

---

## 9. Forgetfulness check (UI)

- [ ] Screen SPEC read before editing?
- [ ] Tokens/components standards applied (no magic hex in components)?
- [ ] UI task gate run with real exit codes?
- [ ] UIS-06 / UIS-07 per [`ui-visual-verify`](skills/ui-visual-verify/skill.md) when applicable?
- [ ] UIS-08 intuitive UX check before ship?
- [ ] UIS-09 data viz quality if analytical dashboard?
- [ ] `HANDOFF_UI.md` and `NEXT_UI.md` updated?
- [ ] Agent OS `HANDOFF.md` has UI cross-link if milestone closed?

---

## 10. FAQ

| Question | Answer |
|----------|--------|
| vs `@feature-spec`? | Domain SPEC in `.work/features/`; screen SPEC in `.work.ui/screens/` |
| vs `@code-implementation`? | Backend + full-stack iteration in `.work/`; UI iteration in `.work.ui/` |
| Which router? | UI how-to → `@ui-process-router`; general → `@process-router` |
| MOD-06 vs UIS-06? | Both when diff spans API + UI; see [`COHABITATION.md`](COHABITATION.md) |
| Quick-reference cheat sheets? | See [`.quick/`](.quick/README.md) — copy-paste snippets for common workflows |
| Analytical dashboard workflow? | See [`.quick/analytical-dashboard.md`](.quick/analytical-dashboard.md) — chart-aware bootstrap → verify |

---

**Maintenance:** Keep this file short. Grow `ui-*/skill.md`, not this tree.
