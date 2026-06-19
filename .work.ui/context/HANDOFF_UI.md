# HANDOFF_UI — UI design session boundary

> **Path:** `<repo-root>/.work.ui/context/HANDOFF_UI.md` · Maintained by **`ui-*` skills**. Session bookends: **`@session-control`** when `.ai/` is present.

## Session status

**Open:** 2026-06-18

**Updated:** 2026-06-18

**Closed:** -

**UI layer state:** Implementation complete — all CRM front-end screens delivered.

**Recommended pick-up:** Visual verification and accessibility audit before milestone close.

**Lost or new?** Read `.ai.ui/START_HERE.md`

---

## UI readiness

| State | Value | Date |
|-------|-------|------|
| ui-foundation-complete | **yes** | 2026-06-18 |
| screen-spec-ready | **yes** | 2026-06-18 |
| ui-implementation-ready | **yes** | 2026-06-18 |

## Active UI milestone

- **Milestone:** Batch J — CRM Pipeline Front-End
- **NEXT_UI:** [.work.ui/plans/NEXT_UI.md](../plans/NEXT_UI.md)

---

## Fresh start — first actions (UI)

1. **`@session-control start`** when `.ai/` is present.
2. Read **`.cursorrules`** (UI block or full UI template).
3. Read **this file** and `.work.ui/plans/NEXT_UI.md`.
4. If foundation missing: **`@ui-design-foundation greenfield`**.
5. Close with **`@session-control close`** (optional commit).

### Conditional reads

| If the task touches… | Read first |
|----------------------|------------|
| Tokens / theme | `.work.ui/plans/foundation/*-02-design-tokens.md` |
| Screen map | `.work.ui/plans/foundation/*-04-screen-map.md` |
| Building UI | Approved `.work.ui/screens/<slug>/*-SCREEN-SPEC.md` |
| API behaviour | `.work/features/<slug>/*-SPEC.md` (link only) |
| Stack / commands | `DOCS_UI_STACK.md` |

---

## Open owner actions (UI)

| # | Action | Blocks | Owner |
|---|--------|--------|-------|
| - | (none) | | |

---

## What this cycle produced (UI)

| Date | Session | Artifacts |
|------|---------|-----------|
| 2025-06-11 | bootstrap | `.work.ui/` skeleton, DOCS_UI_STACK.md, merged .cursorrules |
| 2026-06-18 | foundation | Foundation docs 01-04 under `.work.ui/plans/foundation/` |
| 2026-06-18 | implementation | Full CRM front-end suite (see below) |

### Implementation artifacts

| Artifact | Type | Location |
|----------|------|----------|
| Design tokens (surface stack, spacing, shadows, z-index) | Tokens | `web/src/app/globals.css` |
| Badge | Component | `web/src/components/Badge.tsx` |
| Chip | Component | `web/src/components/Chip.tsx` |
| DataTable | Component | `web/src/components/DataTable.tsx` |
| Dialog | Component | `web/src/components/Dialog.tsx` |
| DropdownMenu | Component | `web/src/components/DropdownMenu.tsx` |
| Skeleton | Component | `web/src/components/Skeleton.tsx` |
| Prospects list page | Screen | `web/src/app/prospects/page.tsx` |
| Prospects detail page | Screen | `web/src/app/prospects/[id]/page.tsx` |
| Clients list page | Screen | `web/src/app/clients/page.tsx` |
| Clients detail page (with contacts) | Screen | `web/src/app/clients/[id]/page.tsx` |
| Project settings: client linking | Section | `web/src/app/projects/[id]/settings/ClientSettingsForm.tsx` |
| AppShell CRM nav links | Navigation | `web/src/components/AppShell.tsx` |
| BFF API proxy routes (10 route files) | API | `web/src/app/api/prospects/`, `api/clients/`, `api/projects/[id]/clients/`, `api/projects/[id]/client-access/` |

---

## Repository UI state

- **Token file:** web/src/app/globals.css
- **Catalog:** `.work.ui/design-system/CATALOG.md` (still needs population)
- **Last visual verify:** 2026-06-18 — PASS with gaps (see audit)
- **Last a11y audit:** 2026-06-18 — PASS with gaps (see audit)
- **ADR location:** `.work.ui/decisions/` (default)

## Recent audit

| Audit | Verdict | Report |
|-------|---------|--------|
| ui-visual-verify milestone | **PASS with gaps** | `.work.ui/audits/20260618-full-ui-audit.md` |
| ui-accessibility-audit milestone | **PASS with gaps** | `.work.ui/audits/20260618-full-ui-audit.md` |
| UIS-01 visual hierarchy | ✓ Pass | `.work.ui/audits/20260618-full-ui-audit.md` |
| UIS-02 responsive layout | ✓ Pass | `.work.ui/audits/20260618-full-ui-audit.md` |
| UIS-04 color contrast | ✓ Pass | `.work.ui/audits/20260618-full-ui-audit.md` |
| UIS-05 interaction patterns | ✓ Pass | `.work.ui/audits/20260618-full-ui-audit.md` |
| UIS-06 AI visual quality | ✓ Pass | `.work.ui/audits/20260618-full-ui-audit.md` |
| UIS-07 surface/control craft | ✓ Pass | `.work.ui/audits/20260618-full-ui-audit.md` |

---

## Cross-link (Agent OS)

Keep **### UI layer** in `.work/context/HANDOFF.md` in sync when milestones close.

### UI layer
- Active UI milestone: Batch J — CRM Pipeline Front-End
- Foundation complete: yes · Screen-spec-ready: yes
- Implementation complete: yes
- NEXT_UI: `.work.ui/plans/NEXT_UI.md`
