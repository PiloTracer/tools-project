# UI Design OS templates

## Agent rules (`.cursorrules`)

| File | When to use |
|------|-------------|
| [`cursorrules.ui.template`](cursorrules.ui.template) | **No** `.cursorrules` — UI-only or create full file (`create-cursorrules`) |
| [`cursorrules.ui.snippet.template`](cursorrules.ui.snippet.template) | **Has** Agent OS `.cursorrules` — append block (`merge-cursorrules`) |
| [`../scripts/cursorrules-ui.sh`](../scripts/cursorrules-ui.sh) | `status` · `create-full` · `merge-block` |

**Adapted from:** `.ai/templates/cursorrules.template` (Core Principles, verification, Docker frontend) — see [`docs/adoption/FROM_AGENT_OS.md`](../docs/adoption/FROM_AGENT_OS.md).

**Skill:** `@ui-bootstrap init` · `@ui-bootstrap init merge-cursorrules` · `@ui-bootstrap status`

## Stack doc

| Template | Adopter path |
|----------|--------------|
| [`DOCS_UI_STACK.md.template`](DOCS_UI_STACK.md.template) | `DOCS_UI_STACK.md` at repo root |

## Project memory (`.work.ui/`)

| Template | Adopter path |
|----------|--------------|
| [`work.ui/`](work.ui/) | `<repo-root>/.work.ui/` |

Bootstrap: `bash .ai.ui/templates/bootstrap.sh [merge-cursorrules|create-cursorrules]`

**Rule:** Skills write live artifacts only under adopter `.work.ui/` — templates are copy sources.

## Agent OS

Use `.ai/templates/` for `.work/` and base engineering rules — independent bootstrap.
