---
name: ui-design-system
description: >-
  Maintain primitives catalog, Storybook coverage, and variant API consistency.
  Use init, add - <component>, status.
---

# ui-design-system

## Modes

| Mode | Action |
|------|--------|
| `init` | Create or refresh `<repo-root>/.work.ui/design-system/CATALOG.md` from foundation doc 03 |
| `add - <component>` | Add primitive: file + story + catalog row per COMPONENT_STANDARD |
| `status` | Missing stories, deprecated components |

## Prerequisites

- Tokens doc exists (`ui-design-foundation` doc 02)

## Hard rules

- New primitives need Storybook default + a11y note
- Variants documented in CATALOG before use in screens
- Cite **example id** from manifests when visual target exists
- Craft tier ≥ refined: optional **behavior source** from [`resources/control-platforms.md`](../../resources/control-platforms.md) in CATALOG; style stays project tokens
