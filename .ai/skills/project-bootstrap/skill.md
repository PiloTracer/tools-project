---
name: project-bootstrap
description: >-
  Bootstrap Agent OS into a repository: copy .work skeleton from templates,
  install .cursorrules and DOCS_TECH_STACK from templates, report missing
  REPLACE tokens. Use when adopting Agent OS, project-bootstrap init, or
  bootstrap .work.
---

# project-bootstrap

One-time (or reset) setup for repositories using Agent OS. **Does not** replace `plan-foundation greenfield` (foundation docs 01–04) or `plan-master greenfield` (master plan).

**Downstream (after init):** See [`.ai/skills/SKILL_DEPENDENCIES.md`](../SKILL_DEPENDENCIES.md) - `plan-foundation` → certify → `plan-master` → `code-implementation`.

**Canonical path:** `.ai/skills/project-bootstrap/skill.md`  
**Templates:** `.ai/templates/` · **Shell:** `.ai/templates/bootstrap.sh`

---

## Parse invocation

| User says | Mode |
|-----------|------|
| `@project-bootstrap` **init** | Create missing `.work/` files, `.cursorrules`, `DOCS_TECH_STACK.md` from templates |
| `@project-bootstrap` **status** | Read-only: what exists, which `REPLACE:` tokens remain in `.cursorrules` |
| `@project-bootstrap` **work-only** | Copy `.work/` skeleton only (never overwrite existing files) |

**Default:** `status` if unclear; suggest `init` when `.work/context/HANDOFF.md` is missing.

---

## Init protocol

### B0 - Brownfield detection (mandatory before any write)

Before copying anything, inventory existing artifacts and decide what to do:

| Path | If exists |
|------|-----------|
| `.cursorrules` (at repo root) | Mark as **existing - protected** |
| `.work/context/HANDOFF.md` | Mark as **existing - populated** |
| `.work/plans/NEXT.md` | Mark as **existing - populated** |
| `.work/plans/ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md` | Mark as **existing - populated** |
| `REPLACE:TECH_STACK_DOC` (stack doc) | Mark as **existing - protected** |
| `.work/features/`, `.work/plans/foundation/`, `.work/plans/full/` (any contents) | Mark as **existing - populated** |

If **any** of the above are marked:

1. **Stop** - do not write.
2. Emit the brownfield summary:

```markdown
## @project-bootstrap init - brownfield detected

The repository is already partially bootstrapped. Choose how to proceed:

| Existing | Path | Action choice |
|----------|------|---------------|
| {list every detected file or folder}    | … | overwrite / keep / abort |

### Choose one (reply in the same message)
- **`overwrite-all`** - replace every existing file with the template (destroys current content)
- **`overwrite-missing`** - copy only files that are missing; never touch existing
- **`keep`** - run `@project-bootstrap status` instead (read-only) and exit init
- **`abort`** - exit silently
```

3. On **`overwrite-missing`** (default safest): proceed to step B1 below, copying only files that don't exist.
4. On **`overwrite-all`**: require an extra `confirm-overwrite-all` token in the same message; otherwise treat as `abort`.
5. On **`keep`** / **`abort`**: exit; do not write.

### B1 - Copy templates (only after B0 resolved)

1. **Confirm repo root** - directory containing `.ai/` (or this tree when `.ai` is the git root).
2. **Run** (preferred):
   ```bash
   bash .ai/templates/bootstrap.sh
   ```
   Or copy manually from `.ai/templates/work/*.template` → `.work/` (strip `.template` suffix). Honor the B0 choice - `overwrite-missing` skips existing paths; `overwrite-all` replaces them.
3. **`.cursorrules`** - if created from template, list every line containing `REPLACE:` and stop until user fills them (or use `status` output).
4. **Standards** - remind user to customize `.ai/standards/20260517-*.md` and point `.cursorrules` `REPLACE:*_FILE` tokens at dated filenames.
5. **Integration** - if external APIs: add `.ai/docs/integration/MANIFEST.txt` from `MANIFEST.template.txt`.
6. **Next commands** (report in output):
   ```
   @plan-foundation greenfield
   @plan-foundation certify plan-master-ready
   @plan-master greenfield
   @session-control start
   ```

**Do not** run `plan-foundation greenfield` automatically unless the user asked for full bootstrap in the same message.

---

## Status protocol

Report:

| Check | Path | pass / missing |
|-------|------|----------------|
| Agent rules | `.cursorrules` | |
| Stack doc | `REPLACE:TECH_STACK_DOC` path from rules | |
| HANDOFF | `.work/context/HANDOFF.md` | |
| NEXT | `.work/plans/NEXT.md` | |
| Registries | `ASSUMPTIONS`, `RISK_REGISTRY`, `UNKNOWNS` | |
| Foundation 01 | `.work/plans/foundation/*-01-*` | |
| Master plan | `.work/plans/full/*-full-plan.md` | |
| Unfilled tokens | `rg 'REPLACE:' .cursorrules` count | |

---

## Template index

| Template | Purpose |
|----------|---------|
| `templates/cursorrules.template` | Repo-root agent rules |
| `templates/DOCS_TECH_STACK.md.template` | Stack pins |
| `templates/work/context/HANDOFF.md.template` | Session handoff |
| `templates/work/plans/NEXT.md.template` | Backlog + iteration block |
| `templates/work/plans/foundation/YYYYMMDD-01-*.template` | P0 scope (plan-foundation may author instead) |
| `templates/work/plans/full/YYYYMMDD-full-plan.md.template` | Master plan outline |
| `templates/work/features/example-slug/…` | Feature SPEC |
| `templates/work/decisions/…` | ADR |

---

## Hard rules

- **Never overwrite** existing `.work/` or `.cursorrules` without explicit user permission.
- **Never commit** secrets; templates contain no credentials.
- **Do not** mark foundation or implementation-ready - other skills own those gates.
