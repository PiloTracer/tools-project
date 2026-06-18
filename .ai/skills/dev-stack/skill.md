---
name: dev-stack
description: >
  Generate or update a `start.sh` (or `bin/start.sh`) dev-stack management script for
  Docker Compose projects. Use when the user invokes @dev-stack, says dev-stack, or asks
  to create, scaffold, rewrite, or extend a start/stop/manage shell script for a Docker-based
  dev environment, mentions terms like "start script", "dev menu", "docker compose wrapper",
  "stack manager", "nuke volumes", "drop tables", or asks how to safely manage a docker compose
  stack without affecting other projects on the host. Also trigger when the user shares an
  existing start.sh and asks to add commands, adapt it to a new stack, or harden its
  isolation guarantees.
---

# dev-stack

Generate or update a **single-file** POSIX shell script (`bin/start.sh` preferred) that gives developers a **safe, isolated** control plane for **one** Docker Compose project - without affecting other stacks on the host. **Project-agnostic:** adapt compose paths, service names, profiles, and DB tooling to the target repo.

**Tool-agnostic** (Cursor, Claude Code, opencode, Codex). **Pairs with:** project `docker-compose*.yml`, `.env.example`, local `.env` (never committed).

**Canonical path:** `.ai/skills/dev-stack/skill.md` · **Invocation patterns, tables, CI:** `reference.md`

**Hard rules:**

- **Never `source .env`.** Parse key=value safely (see `reference.md` §Safe env parsing).
- **Stack isolation is mandatory.** Every `docker compose` call uses the full scoping pattern in `reference.md` §Compose invocation - no bare `docker stop` / `docker rm` / wildcard volume nukes for "cleanup".
- **Dangerous operations** (`down -v`, drop schema, flush caches) require **double confirmation** with project/database identity - pattern in `reference.md` §Dangerous commands.
- **Dual mode:** interactive **full menu** when invoked with no args or `dev`; headless subcommands (`start`, `stop`, …) for CI; `MENU_QUIET=1` for non-interactive, capture-on-failure logging - see `reference.md` §CI.
- **Menu UX:** categorized sections, live stack summary (running/total, health probes), optional terminal colors, `r` refresh, `?` help - see `reference.md` §Interactive menu.
- **`set -euo pipefail`** at top; in interactive menu loops, scope `set +e` / `set -e` around compose calls so failures return to the menu instead of exiting the shell.
- **Respect protected files** where the repo marks them (e.g. this project's `.cursorrules` §Protected Files): do not change `docker-compose*.yml`, `Dockerfile.*`, or `.env*` **unless the user explicitly permits** those edits in the same message. The skill may still **generate** `bin/start.sh` without touching compose.
- **Host hygiene:** Do not document or script host-side `npm`/`yarn`/`pip install` for stack services. Package installs belong **inside** compose services (`.cursorrules` § Host hygiene); `start.sh` may offer `exec` into a service for installs when appropriate.

---

## Parse invocation

Normalize the user message to **verb** + optional **target path**.

| User says | Verb | Action |
|-----------|------|--------|
| `@dev-stack` **status** | status | [Status protocol](#status-protocol) - read-only: report whether `bin/start.sh` exists, is executable, and matches the current skill contract |
| `@dev-stack` **init** | init | Generate fresh `bin/start.sh` (see [Generation protocol](#generation-protocol)) |
| `@dev-stack` **update** \| **rewrite** | init | Same as `init` - overwrite existing file after isolation audit |
| `@dev-stack` (no verb) | init | Default to generate / update |

**Aliases:** `update`, `rewrite`, `scaffold`, `generate` → **init**.

---

## Step 0 - Pick a mode

| Mode | Condition | Action |
|------|-----------|--------|
| **status** | user asks "is start.sh ready?", "do we have it?", "what version?" | [Status protocol](#status-protocol) - read-only |
| **init** | user asks to create, update, or rewrite the script | [Generation protocol](#generation-protocol) |

---

## Default output

| Artifact | Rule |
|----------|------|
| **Path** | Prefer **`bin/start.sh`** at the repository root (create `bin/` if missing). Use another path only if the user names it. |
| **Executable** | Instruct `chmod +x bin/start.sh` (or apply in the same change if the user asked to create the file). |
| **Self-contained** | One file; no required sibling `lib/` scripts unless the user explicitly wants a split layout. |

---

## Status protocol

Read-only. No file writes.

1. Check `bin/start.sh` (or user-named path) exists.
2. If exists: check executable bit (`test -x`), file size, and run `bash -n` for syntax.
3. Detect compose project name (`grep -E 'COMPOSE_PROJECT_NAME|--project-name' bin/start.sh`).
4. Detect dangerous-command pattern presence (`grep -E '_double_confirm|print_banner' bin/start.sh`).
5. Output:

```markdown
## dev-stack status

**Path:** bin/start.sh · **Exists:** yes/no · **Executable:** yes/no
**Syntax:** pass | fail (`bash -n` exit code)
**Compose scoping:** detected | missing
**Dangerous-command guard:** detected | missing
**Recommendation:** ok | run `@dev-stack init` to regenerate
```

If `bin/start.sh` is missing → recommend `@dev-stack init`.
If syntax / scoping / guard missing → recommend `@dev-stack init` (will regenerate; confirm before overwrite - see Brownfield below).

---

## Brownfield gate (init mode)

Before generating:

1. If `bin/start.sh` already exists, **stop** and report:
   - Current file size, last-modified, executable bit, detected compose scoping.
   - Ask once: **overwrite | keep | abort**.
2. On **keep**: exit with a status summary; do not write.
3. On **abort**: exit silently.
4. On **overwrite**: proceed to [Generation protocol](#generation-protocol).

Do not silently overwrite a customized script.

---

## When the user has not asked for a file yet

If they only want the **skill** or "how to": output the **script body** in a fenced `sh` block and state that they should save it as `bin/start.sh` and chmod. If they asked to **create** the file, write `bin/start.sh` and verify syntax (`sh -n`) when possible.

---

## Generation protocol

### S1 - Discover the stack (ask or read)

Minimum inputs (record gaps as **Unverified** until filled):

1. Compose file path(s) - default `docker-compose.yml` at repo root.
2. **`COMPOSE_PROJECT_NAME`** (or equivalent) - must be stable and unique per clone; recommend reading from `.env` with a documented default.
3. **Compose profile** - e.g. `dev`, `local` (omit `--profile` only if the project truly uses no profiles).
4. Service names for DB/Redis waits and one-off `exec` targets.
5. DB engine (Postgres, MySQL, none) and how schema is applied (migrations CLI, raw SQL, none).
6. URL/port hints - which env vars expose host ports (project-specific).

### S2 - Scaffold from the contract

Implement the **anatomy** and **command set** in `reference.md`. Adapt:

- `_compose_invoke` / `dc` / `quiet_dc` to the repo's compose files and profile.
- `urls_hint` to actual env vars.
- DB commands: include, omit, or rename per stack.

### S3 - Isolation audit (mandatory before delivery)

Confirm in the generated script:

- [ ] No bare `docker` mutations outside `docker compose` with project name + project directory + compose file(s).
- [ ] No `source .env` or `eval` on env content.
- [ ] Destructive paths use double confirmation + `print_banner` (or equivalent) showing **which** project.

### S4 - Completion checklist

| # | Check | Result |
|---|--------|--------|
| 1 | `bin/start.sh` path (or user path) agreed | pass |
| 2 | Compose scoping pattern present | pass |
| 3 | Safe `.env` reader present | pass |
| 4 | `--help` lists subcommands | pass |
| 5 | `MENU_QUIET=1` + CI path documented | pass |
| 6 | `bash -n bin/start.sh` (or `sh -n` for POSIX scripts) | pass / skip |

---

## Anti-patterns

- `docker compose down` without `-p` / wrong project directory (destroys wrong stack).
- Sourcing `.env` for convenience.
- Single `y/n` for volume wipe.
- Hard-coded container names from other projects.
- Embedding secrets in the script; read from env only.

---

## Source note

Plain-text authoring for this skill lives in **`skill.md` + `reference.md`**. If a collaborator provides a `*.skill` binary blob, do not treat it as canonical - extract requirements in chat or replace with this markdown skill.
