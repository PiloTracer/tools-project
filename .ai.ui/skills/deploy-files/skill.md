---
name: deploy-files
description: >-
  Deploy .ai.ui (UI Design OS) files into a target project — copies only
  git-tracked / non-ignored files (anything in .gitignore is never copied),
  then strips skill-level omissions (.github/, .gitignore, .gitattributes,
  .cursorrules, deploy scripts). Idempotent re-copy that preserves target-side
  customizations. Use for bootstrapping a new project with UI Design OS without
  cloning the full repo history. deploy-files copy - <path>, deploy-files status.
---

# deploy-files

**Shell:** `bash .ai.ui/scripts/deploy-files.sh <target-path>`

Deploys this `.ai.ui` framework into a target project so the project can use UI Design OS skills. Path auto-resolution: if the path ends in `.ai.ui` it is used as-is; otherwise `.ai.ui` is appended inside the path.

**Canonical path:** `.ai.ui/skills/deploy-files/skill.md` · **Shell:** `.ai.ui/scripts/deploy-files.sh`

**Security invariant:** The script enumerates files via `git ls-files --cached --others --exclude-standard`, so **anything `.gitignore` excludes (credentials, node_modules, dist, `tmp/`, examples/*.png, …) is never copied** — enforced by construction, not a hand-maintained list. The source must be a git repo with `.ai.ui/` as its root.

**Contrast with `deploy-repo`:** `deploy-files` copies only the `.ai.ui/` directory (no VCS artifacts). Use `@deploy-repo clone` when you need the full repo including `.git` and `.github/`.

---

## Parse invocation

| User says | Mode |
|-----------|------|
| `@deploy-files` **copy - /path/to/repo** | Copy clean files to `/path/to/repo/.ai.ui` |
| `@deploy-files` **copy - /path/to/repo/.ai.ui** | Same, destination explicit |
| `@deploy-files` **status** | Report whether `.ai.ui/` exists at known deploy locations |

**Default:** `status` if no verb matches.

---

## I0 — Pre-checks

| Condition | Action |
|-----------|--------|
| Source is not a git repo, or `.ai.ui/` is not the git root | **Block**: report; deploy-files relies on `git ls-files` as the authority |
| Target parent dir does not exist | **Block**: report missing path |
| Destination exists and is not a dir | **Block**: report conflict |
| Destination already has `.ai.ui/` | Report existing; re-copy (idempotent overwrite; preserves untracked target files) |

---

## I1 — Copy mode

1. `bash .ai.ui/scripts/deploy-files.sh "<resolved-path>"`
2. **File set:** `git ls-files --cached --others --exclude-standard` from the source repo root — i.e. every file **not** excluded by `.gitignore`. Anything gitignored (`.credentials/`, `.private/`, `tmp/`, …) is never copied.
3. **Skill-level omissions** (intentional, on top of the git-based set): `.github/`, `.gitignore`, `.gitattributes`, `.cursorrules`, `scripts/deploy-files.sh`, `scripts/deploy-repo.sh`.
4. Re-copies on re-run (idempotent overwrite). No `--delete` — target-side customizations are preserved.
5. Outputs next steps for the target project.

**When to use:** Target project needs UI Design OS but does not need the full `.ai.ui` repository history. Recommended for most cases.

---

## Completion

| # | Check | Result |
|---|-------|--------|
| 1 | Source repo is this `.ai.ui` project (git root) | pass |
| 2 | Destination `.ai.ui/` exists after copy | |
| 3 | No `.gitignored` content in destination (node_modules, dist, credentials, tmp/, …) | |
| 4 | `.github/` excluded from destination | |
| 5 | `.cursorrules` excluded from destination (created later by `@ui-bootstrap init`) | |
| 6 | User informed of next steps | |

## Next commands (in target project)

```text
@ui-bootstrap init merge-cursorrules
@ui-project-approach - <describe project>
```
