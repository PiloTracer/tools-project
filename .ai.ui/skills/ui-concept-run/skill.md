---
name: ui-concept-run
description: >-
  Run UIS-01 through UIS-07 concept prompts from .ai.ui/concepts/. Attach output
  to screen SPEC, NEXT_UI, or PR. Use list, run - UIS-0N, status.
---

# ui-concept-run

**Parallel:** Agent OS `@concept-run` for MOD-* — independent; both may be required.

## Modes

| Mode | Action |
|------|--------|
| `list` | UIS index + trigger table summary |
| `run - UIS-0N` | Execute `concepts/<folder>/prompt.md` for UIS-01…07 |
| `status` | Pending UIS rows in active NEXT_UI |

## Hard rules

- Follow evidence tags in prompt outputs
- **UIS-06 required** for agent-assisted UI before `@ui-component-build complete`
- **UIS-07 required** when craft tier ≥ refined (foundation 01) at milestone verify
- Do not write into `.ai/concepts/`

Trigger table: [`.ai.ui/concepts/README.md`](../../concepts/README.md)
