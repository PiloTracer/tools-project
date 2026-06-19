---
name: ui-style-stack
description: >-
  Set or report the active styling approach (tailwind, css-modules, vanilla-css,
  styled-components). Records in HANDOFF_UI; implementation rules in style-stacks/.
  Use set - <stack>, status.
---

# ui-style-stack

**Registry:** [`style-stacks/README.md`](../../style-stacks/README.md)

**Hard rules:**

- One active stack per repo phase — record in `{HANDOFF_UI}`.
- `ui-component-build` must follow active stack doc when emitting styles.
- Do not add dependencies (Tailwind, styled-components) without user approval (protected files).

## Modes

| Mode | Action |
|------|--------|
| `set - tailwind` \| `css-modules` \| `vanilla-css` \| `styled-components` | Write stack to HANDOFF_UI; point to `style-stacks/<stack>.md` |
| `status` | Read HANDOFF + confirm stack doc exists |

## set protocol

1. Validate stack id against `style-stacks/README.md`.
2. Update `{HANDOFF_UI}` § Repository UI state with `**Style stack:** <id> · **Date:** …`
3. Remind: map tokens in foundation doc 02 to stack per `style-stacks/<id>.md`.
4. If `REPLACE:UI_STYLE_SYSTEM` in `.cursorrules` unfilled, suggest filling to match.

## Pairs with

- `@ui-design-foundation greenfield` (doc 02 tokens)
- `@ui-component-build` (implementation)
