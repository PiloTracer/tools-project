# Prompts (pointer)

**Project prompts live in [`.work/prompts/`](../.work/prompts/)**, not under `.ai/`.

Decision questionnaires and archived owner answers are **project-local** - not a portable standard layout.

| Typical file | Purpose | Read by skills? |
|--------------|---------|-----------------|
| `initial.md` | **Optional user scratch** — founder notes, paste buffer | **No** — only if the user explicitly names this path in the same invocation |
| `decision_<NNN>_<slug>.md` | Owner questionnaire + archived answers | On demand when ADR/SPEC work references it |

**Product intent (canonical):** `@plan-foundation` **greenfield** creates the **P0 initial scope** mini-plan at `{PLANS_ROOT}/foundation/YYYYMMDD-01-<slug>-initial-scope.md` (foundation doc 01). **session-control**, **plan-master**, and **plan-foundation** read doc 01 — not `initial.md`.

Portable skills reference `{PROMPTS_ROOT}` — see `.cursorrules` placeholder map.
