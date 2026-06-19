---
name: ui-project-approach
description: >-
  Read-only classifier: project archetype, complexity, skill chain, and pattern
  checklist pointers. Use when starting UI work or unsure which ui-* skills to run.
  Does not write files unless user asks to record archetype in HANDOFF_UI.
---

# ui-project-approach

**Canonical source:** [`APPROACH.md`](../../APPROACH.md) · **Patterns:** [`standards/20260523-UI-PATTERNS.md`](../../standards/20260523-UI-PATTERNS.md) · **Examples:** [`examples/INDEX.md`](../../examples/INDEX.md)

**Hard rules:** Default **read-only**. Do not duplicate Agent OS planning skills.

## Modes

| Mode | Action |
|------|--------|
| `- <description>` | Classify archetype + complexity + skill chain + pattern §§ |
| `status` | Read `{HANDOFF_UI}` archetype/stack if set |
| `help` | List archetypes |

## Protocol

1. Parse user description (or `status` → read HANDOFF).
2. Match **one primary** archetype from APPROACH §1 (`marketing-site`, `saas-product`, `admin-dashboard`, `mobile-app`, `design-system`, `hybrid`).
3. Suggest **complexity** S/M/L (APPROACH §4).
4. Output skill chain from APPROACH §2.
5. List **UI-PATTERNS** sections to apply.
6. Point to **examples/manifest.md** folder if relevant.
7. If `.ai/` present, note `@session-control` + link domain SPECs in `.work/features/`.

## Optional write (user must ask)

Record in `{HANDOFF_UI}` § Repository UI state:

```markdown
**Archetype:** saas-product · **Complexity:** M
```

## Output shape

```markdown
## ui-project-approach

**Archetype:** … · **Complexity:** …
**Style stack:** (from HANDOFF or "run @ui-style-stack set - …")

### Run next
1. …

### Pattern checklist
- UI-PATTERNS § …

### Examples (optional)
- examples/…/manifest.md

### Do not run
- (Agent OS skills that would duplicate)
```
