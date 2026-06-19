# Directory Map — template

**Status:** Customize for your repo, then treat as binding before first application code.
**Bootstrap:** Copy to `.ai/standards/YYYYMMDD-DIRECTORY_MAP.md`, replace `REPLACE:` tokens, align with foundation doc 04 and `.cursorrules`.

---

## Repository roots

| Path | Purpose |
|------|---------|
| `.ai/` | **Agnostic:** skills, standards, concepts, workflow guides, `START_HERE.md`, `PROCESS_ROUTER.md` |
| `.work/` | **Project:** plans, SPECs, ADRs, prompts, session `HANDOFF.md` |
| `.ai/docs/integration/` | Optional vendor mirror + `MANIFEST.txt` (see `docs/integration/README.md`) |
| `.work/plans/` | Foundation, full plan, registries, `NEXT.md` |
| `.work/features/<slug>/` | Feature SPECs per FEATURE_STANDARD |
| `.work/decisions/` | ADRs |
| `.work/context/` | `HANDOFF.md` |
| `.work/analysis/` | Generated investigation / audit markdown (gap analyses, session postmortems, parity reports) |
| `.work/scripts/` | Markdown runbooks for one-off operational scripts; code lives in application tree |
| `REPLACE:APP_ROOT/` | Primary application (backend, monolith, or service tree) |
| `REPLACE:FRONTEND_ROOT/` | Optional UI (if any) |
| `REPLACE:WORKER_ROOT/` | Optional async workers (if any) |
| `REPLACE:TECH_STACK_DOC` | Pinned stack versions |
| `.cursorrules` | Agent + engineering rules (repo root) |

---

## Application layout (example — adapt)

```
REPLACE:APP_ROOT/
├── pyproject.toml | package.json | go.mod   ← pick per stack
├── REPLACE:MIGRATIONS_DIR/
│   └── 001_init.sql                         ← numbered, idempotent
├── src/
│   ├── main.py | index.ts | …
│   ├── REPLACE:PLATFORM_PACKAGE/            ← shared cross-cutting code
│   └── <bounded-context>/                   ← one folder per domain module
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       ├── http/                            ← if HTTP-facing
│       └── ports/
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

**Dependency rule:** bounded contexts import only `REPLACE:PLATFORM_PACKAGE` and published `ports/` / `events/` from other contexts (see CONVENTIONS).

---

## Documentation map (read order)

| Task | Read first |
|------|------------|
| Any code change | `.cursorrules`, `.work/context/HANDOFF.md` |
| Layout | This file |
| Stack versions | `REPLACE:TECH_STACK_DOC` |
| Feature work | `.work/features/<slug>/*-SPEC.md` |
| API design | `.ai/standards/*-api-style-guide.md` (when present) |
| Security | data-classification + threat-model standards (when present) |
| External APIs | `.work/plans/foundation/*-02-*.md`, `.ai/docs/integration/MANIFEST.txt` |

---

## Gate

Foundation doc 04 should reference this map. Update it when adding a new top-level directory (ADR per FEATURE_STANDARD §9).

**Code-to-registry parity:** After material app-tree changes or brownfield adoption, run `@plan-verify coverage`. Unmapped routes/pages/controllers → `@plan-repair repair - from coverage` (SPEC **Implementation map**, not parallel `feature.yml` registries).
