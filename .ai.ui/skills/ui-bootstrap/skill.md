---
name: ui-bootstrap
description: >-
  Scaffold .work.ui/, install or merge UI rules in .cursorrules (create if missing,
  merge block with permission), optional DOCS_UI_STACK.md. Never overwrites .work/ or .ai/.
  Use init, init merge-cursorrules, status, cursorrules status.
---

# ui-bootstrap

**Output root:** `<repo-root>/.work.ui/` · **Rules:** `<repo-root>/.cursorrules`

**Hard rules:**

- **Never** overwrite `.work/`, `.ai/`, or existing `.cursorrules` without explicit user permission in the same message.
- **Never** register unprefixed skills or modify Agent OS trees.
- **May create** `.cursorrules` when missing (from `cursorrules.ui.template`).
- **May merge** `cursorrules.ui.snippet.template` when `.cursorrules` exists but lacks `UI_DESIGN_OS_BEGIN` — only after user approves (`merge-cursorrules`, `init merge-cursorrules`, or `overwrite-missing` flow below).

**Shell:** `bash .ai.ui/templates/bootstrap.sh` · **Cursorrules:** `bash .ai.ui/scripts/cursorrules-ui.sh <mode>`

**Adapted from:** Agent OS `project-bootstrap` (brownfield gates only — not duplicated planning skills). See `.ai.ui/docs/adoption/FROM_AGENT_OS.md`.

---

## Parse invocation

| User says | Mode |
|-----------|------|
| `@ui-bootstrap` **init** | `.work.ui/` skeleton + cursorrules status; **does not** auto-merge rules |
| `@ui-bootstrap` **init** **merge-cursorrules** | init + append UI block (or create full rules if missing) |
| `@ui-bootstrap` **init** **create-cursorrules** | init + copy full `cursorrules.ui.template` if missing |
| `@ui-bootstrap` **status** | Read-only: `.work.ui/`, cursorrules, unfilled `REPLACE:UI_*` |
| `@ui-bootstrap` **cursorrules** **status** | Alias: cursorrules section of status |
| `@ui-bootstrap` **cursorrules** **merge-block** | Merge snippet only (requires permission unless user said merge-cursorrules) |
| `@ui-bootstrap` **cursorrules** **create-full** | Full UI template when no `.cursorrules` |

---

## B0 — Brownfield (before any write)

Inventory:

| Path | If exists |
|------|-----------|
| `.cursorrules` | **existing** — do not replace without permission |
| `.work.ui/context/HANDOFF_UI.md` | populated skeleton |
| `REPLACE:UI_TECH_STACK_DOC` (default `DOCS_UI_STACK.md`) | existing stack doc |
| `.ai/` | Agent OS present → recommend merge-block over create-full when `.cursorrules` exists |

If `.cursorrules` exists and user asked plain **`init`** only:

- Run `bootstrap.sh` (overwrite-missing for `.work.ui/`).
- Report cursorrules status; **ask** whether to `merge-cursorrules` if UI block missing.

If user said **`init merge-cursorrules`** or **`cursorrules merge-block`** in the same message → proceed to cursorrules protocol.

**Choices (when `.cursorrules` exists and user wants rules change):**

| Choice | Action |
|--------|--------|
| `merge-cursorrules` | Append snippet if no `UI_DESIGN_OS_BEGIN` |
| `create-cursorrules` | Only if file missing |
| `keep` | status only |
| `confirm-overwrite-cursorrules` | Replace entire `.cursorrules` with UI template — destructive |

---

## B1 — `.work.ui/` skeleton

1. `bash .ai.ui/templates/bootstrap.sh` from repo root.
2. Copy only missing files from `templates/work.ui/`.

---

## B2 — `.cursorrules` protocol

Run: `bash .ai.ui/scripts/cursorrules-ui.sh status`

| Condition | Action |
|-----------|--------|
| No `.cursorrules` | `create-full` → copy `templates/cursorrules.ui.template` |
| Exists, no `UI_DESIGN_OS_BEGIN`, user approved merge | `merge-block` → append snippet |
| Exists, has `UI_DESIGN_OS_BEGIN` | Report unfilled `REPLACE:UI_*` (rg); offer to help fill with user approval per token |
| `.ai/` + no `.cursorrules` | Prefer: suggest `@project-bootstrap init` then `merge-cursorrules`; if user wants UI-only, `create-full` is OK |

**Also:** If `DOCS_UI_STACK.md` (or path in rules) missing → copy `templates/DOCS_UI_STACK.md.template` (copy-if-missing).

**Do not** remove or edit Agent OS skill tables in an existing merged file.

---

## B3 — HANDOFF cross-link

If `.work/context/HANDOFF.md` exists and lacks `### UI layer`, append one stub paragraph linking `.work.ui/context/HANDOFF_UI.md` — **only** with user approval or `init merge-cursorrules` in the same message.

---

## Status protocol

| Check | pass / missing |
|-------|----------------|
| `.work.ui/README.md` | |
| `HANDOFF_UI.md` | |
| `NEXT_UI.md` | |
| `.cursorrules` | |
| UI block (`UI_DESIGN_OS_BEGIN` or standalone) | |
| `REPLACE:UI_*` unfilled count | |
| `DOCS_UI_STACK.md` | |
| `.ai/` present (cohabitation) | |

---

## Next commands

```text
@ui-design-foundation greenfield
@ui-design-foundation certify screen-spec-ready
@session-control start          # when .ai/ present
```

---

## Completion checklist

| # | Check | Result |
|---|-------|--------|
| 1 | `.work.ui/` skeleton | |
| 2 | `.ai/` / `.work/` untouched or user-approved | |
| 3 | `.cursorrules` exists or user declined | |
| 4 | UI block present or standalone template | |
| 5 | User informed of unfilled `REPLACE:UI_*` | |
