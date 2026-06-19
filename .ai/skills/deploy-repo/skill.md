---
name: deploy-repo
description: >-
  Full git-based deploy of Agent OS into a target directory. Two modes:
  clone (git clone with full history via origin remote) or archive
  (git archive extract including .github, .gitignore, .cursorrules).
  Use clone for a full git mirror; use archive when no remote is available
  or when updating an existing target. deploy-repo clone - <path>,
  deploy-repo archive - <path>, deploy-repo status.
---

# deploy-repo

**Shell:** `bash .ai/scripts/deploy-repo.sh <clone|archive> <target-path>`

Deploys the entire `.ai` Agent OS repository (including `.git/`, `.github/`, `.gitignore`, and root `.cursorrules`) into a target directory. Two modes cover both git-mirror and snapshot deployments.

**Canonical path:** `.ai/skills/deploy-repo/skill.md` · **Shell:** `.ai/scripts/deploy-repo.sh`

**Contrast with `deploy-files`:** `deploy-repo` includes VCS artifacts. Use `@deploy-files copy` when you only need the `.ai/` directory without git history or `.github/`.

---

## Parse invocation

| User says | Mode |
|-----------|------|
| `@deploy-repo` **clone - /path/to/repo** | Full `git clone` from origin remote to target path |
| `@deploy-repo` **archive - /path/to/repo** | `git archive HEAD \| tar xf` — full tree, no `.git` |
| `@deploy-repo` **status** | Report source remote, existing deploy locations |

**Default:** `status` if no verb matches.

---

## I0 — Pre-checks

| Condition | Action |
|-----------|--------|
| Target parent dir does not exist | **Block**: report missing path |
| No git remote in source (clone mode) | **Block**: suggest `archive` mode instead |
| Target already has `.git` (clone mode) | Report existing; exit (clone requires fresh target) |
| Target exists as non-dir | **Block**: report conflict |

---

## I1 — Clone mode

1. `bash .ai/scripts/deploy-repo.sh clone "<resolved-path>"`
2. Requires git remote `origin` on source repo.
3. Target must not exist or must be empty.
4. Full `git clone` preserves all branches and tags.

**When to use:** You need the full repository with git history, CI/CD workflows (`.github/`), and version tracking in the target.

---

## I2 — Archive mode

1. `bash .ai/scripts/deploy-repo.sh archive "<resolved-path>"`
2. Uses `git archive HEAD` — no remote required.
3. Includes `.github/`, `.gitignore`, `.cursorrules` (everything except `.git` directory).
4. Idempotent — re-runs safely overwrite files.

**When to use:** No remote available, or target already exists and you want to update its `.ai/` tree while keeping VCS artifacts (`.github/`, `.gitignore`, `.cursorrules`).

---

## Completion

| # | Check | Clone | Archive |
|---|-------|-------|---------|
| 1 | Source repo has origin remote (or archive mode) | pass | pass |
| 2 | Target path exists and is populated | | |
| 3 | `.git/` present (clone) / `.github/` present (archive) | | |
| 4 | `.cursorrules` present at target root | | |
| 5 | User informed of next steps | | |

## Next commands (in target project)

```text
@project-bootstrap init
@session-control start
```
