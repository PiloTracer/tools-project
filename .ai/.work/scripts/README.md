# `.work/scripts/` — operational runbooks

**Purpose:** Markdown runbooks for one-off operational scripts: backfills, data repairs, migrations, and other dangerous or rare operations. Each `.md` file documents **how and why** — the executable code lives in the application tree, not here.

## What goes here

| File | Purpose |
|------|---------|
| `backfill_period_id.md` | Runbook for stamping `period_id` on L1 rows; executable at `fastapis/tests/backfill_period_id.py` |
| `repair_duplicate_keys.md` | Runbook for deduplication; executable at `fastapis/tests/repair_duplicate_keys.py` |

## What does NOT go here

- The Python / shell implementation → lives in the application tree (e.g. `fastapis/tests/`, `.ai/scripts/`)
- Feature SPECs → `.work/features/<slug>/`
- ADRs → `.work/decisions/`

## Runbook format

Each runbook should document:

1. **Purpose** — what problem this script solves
2. **Contract** — inputs, outputs, side effects
3. **Execution** — exact `docker exec` / shell command
4. **Safety** — what it touches, rollback plan, dry-run option
5. **Evidence** — expected output, verification steps

## How skills interact with this folder

- **Not read automatically** by `@session-control` or `@code-implementation`.
- Referenced explicitly from `NEXT.md`, `HANDOFF.md`, or feature SPECs when a runbook step is needed.
- Bootstrap templates do not create it — the folder appears when the first runbook is written.
