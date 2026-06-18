# ADRs (pointer)

**Architectural decision records live in [`.work/decisions/`](../.work/decisions/)** in each adopting repo — not under `.ai/`.

ADR template: [`.ai/templates/work/decisions/`](../templates/work/decisions/)

Binding **process** for ADRs during foundation planning is in [`plan-foundation` skill](../skills/plan-foundation/skill.md) P2. **Artifacts** are project working documents.

Portable skills reference `{DECISIONS_ROOT}` — see `.cursorrules` placeholder map.

## Index

Maintain an ADR table in `.work/decisions/README.md` (or the foundation architecture doc §13) with status per file. **ADR headers win** on conflict with summaries.

Example columns:

| ADR | Topic | Status |
|-----|-------|--------|
| 001 | Primary backend stack | Decided |
| 002 | Tenancy model | Decided |
| 003 | Hosting / cloud | Open |

Foundation register in `*-04-foundation-architecture.md` must agree with ADRs; amend the register or the ADR when they diverge.
