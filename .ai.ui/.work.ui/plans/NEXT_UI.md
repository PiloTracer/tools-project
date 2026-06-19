# NEXT_UI — UI planning backlog

> **Demo skeleton.** In an adopter repo, **`@ui-component-build`** owns `## Current UI iteration`; **`ui-*` skills** and session close update **Recommended next**.

**Updated:** YYYY-MM-DD

---

## Done (UI)

| Item | Artifact |
|------|----------|
| UI Design OS bootstrap | `.work.ui/` skeleton |

---

## Blocked on owner (UI)

| # | Item | Notes |
|---|------|-------|
| - | (none) | |

---

## Recommended next

| Priority | Item | Notes |
|----------|------|-------|
| **0** | `@ui-design-foundation greenfield` | Creates foundation docs 01–04 under `.work.ui/plans/foundation/` |
| **1** | `@ui-design-foundation certify screen-spec-ready` | After foundation gates |
| **2** | `@ui-design-system init` | Catalog from foundation doc 03 |
| **3** | `@ui-screen-spec create - <slug>` | Per screen in screen map |
| **4** | `@ui-component-build plan - S0` | P0 primitives when craft tier ≥ refined |
| **5** | `@ui-component-build plan - S1` | After SPECs **Approved** + primitives done |

---

## Intake queue

> Free-text UI requests captured by `@ui-screen-spec intake - <sentence>`. Format: `- <YYYY-MM-DD> · <class> · "<sentence>" → <next command>`. Classes: local / cross-cutting / brownfield / underspecified.

- (none yet)

---

## Current UI iteration

*(No active UI iteration — run `@ui-component-build plan - S0` then `S1` after **screen-spec-ready**.)*

```markdown
## Current UI iteration - S{N}: <milestone name>

**Milestone ref:** S{N} · screen map / UI roadmap
**Status:** planning | in-progress | complete
**Started:** YYYY-MM-DD

### In scope
- …

### Out of scope (explicit)
- …

### Tasks
| ID | Description | Files | Status | Notes |
|----|-------------|-------|--------|-------|
| S1-T1 | … | `REPLACE:UI_APP_ROOT/...` | pending | |

### Acceptance criteria
- …

### UIS registry (this iteration)
| UIS | Applies | Reason | Status |
|-----|---------|--------|--------|
| UIS-06 | yes | agent UI session | pending |

### Done this UI iteration
(move completed tasks here on `@ui-component-build complete`)
```

---

## Shared engineering unknowns

When UI blockers affect backend, add a row to **`.work/plans/UNKNOWNS.md`** (Agent OS) and reference here.
