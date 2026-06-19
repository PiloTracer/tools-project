# `.work/analysis/` — investigations and audits

**Purpose:** Host-side markdown for deep-dive investigations, gap analyses, parity reports, session postmortems, and audit outputs. Keeps these artifacts out of application source trees.

## What goes here

| Kind | Examples |
|------|----------|
| Gap analysis | `20260527-m4-prorrata-macro-parity.md` |
| Session postmortem | `session_005_edge_case_review.md` |
| Excel / data audits | `20260601-workbook-audit.md` |
| Macro parity matrices | `migration-parity-v2.md` |

## What does NOT go here

- Feature SPECs → `.work/features/<slug>/`
- ADRs → `.work/decisions/`
- Verify/coverage snapshots → `.work/reports/`
- The analysis code itself → lives in the application tree (e.g. `fastapis/tests/`)

## Conventions

- Files are **markdown** (`.md`).
- Name by date or session: `YYYYMMDD-<topic>.md`, `session_NNN_<topic>.md`.
- Link from `RISK_REGISTRY.md`, `NEXT.md`, or feature SPECs when the analysis informs a decision.

## How skills interact with this folder

- **Not read automatically** by `@session-control` or `@code-implementation`.
- Referenced explicitly from feature SPECs, `NEXT.md`, `HANDOFF.md`, or `RISK_REGISTRY.md`.
- Bootstrap templates do not create it — the folder appears when the first investigation runs.
