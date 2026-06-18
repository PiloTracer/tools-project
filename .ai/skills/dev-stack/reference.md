# dev-stack - reference

Supplement to `skill.md`. **Compose invocation template**, **safe env parsing**, **command menu**, **dangerous ops**, **CI**, **adaptation checklist**.

---

## Which reference file to use

| File | Use |
|------|-----|
| `.ai/skills/dev-stack/skill.md` | Canonical workflow + hard rules |
| This `reference.md` | Templates and tables |
| `tmp/SKILL.md` (if present) | Historical draft; prefer repo `skill.md` |
| `tmp/*.skill` (if present) | **Not** plain-text skills - do not parse as markdown |

---

## Compose invocation (isolation)

Every `docker compose` call from the generated script should assemble **all** of the following (adjust names to project conventions):

```bash
docker compose \
  --project-directory "$REPO_ROOT" \
  -f "$COMPOSE_ABS" \
  -p "$COMPOSE_PROJECT_NAME" \
  --profile "$PROFILE" \
  "$@"
```

Rules:

- **`COMPOSE_ABS`**: absolute path to the primary compose file (resolve from `SCRIPT_DIR` / `REPO_ROOT`).
- **`COMPOSE_PROJECT_NAME`**: from safe `.env` read - **the isolation key**; never default to Docker's directory basename alone if multiple clones share paths.
- **`PROFILE`**: fixed default (e.g. `dev`) or second safe `.env` key.
- **Never** use bare `docker stop`, `docker kill`, `docker rm`, `docker volume rm`, `docker network rm` for routine teardown - use `docker compose … down` / `down -v` scoped as above.

---

## Safe `.env` parsing

Never `source .env`. Implement `read_dotenv_value(key)` that:

1. Opens `.env` with `IFS= read -r` line by line.
2. Skips blank lines and lines starting with `#`.
3. Splits on the **first** `=` only.
4. Trims surrounding whitespace on key and value.
5. Strips one matching pair of surrounding `'` or `"` from values.
6. Emits with `printf '%s'` for safe capture: `value=$(read_dotenv_value KEY)`.

Export variables needed by compose **after** parsing - do not execute values as shell code.

---

## Script anatomy (checklist)

```
bin/start.sh
├── Shebang + set -euo pipefail
├── SCRIPT_DIR / REPO_ROOT / COMPOSE_ABS (cd + pwd; avoid GNU-only readlink -f unless required)
├── PROFILE + default COMPOSE_PROJECT_NAME
├── read_dotenv_value() / load_env()
├── require_compose_file()
├── _compose_invoke()  → internal; all docker compose goes here
├── dc() / quiet_dc()
├── stream_compose_ops() / wait_ack_if_menu() (TTY: prefer /dev/tty - see skill anti-patterns)
├── print_banner() / urls_hint() / health_summary_line() / render_menu_*()
├── validate_config() (dc config -q)
├── cmd_*() per command
├── show_menu() + dispatch_menu_choice() + main() (--help, CLI dispatch, menu loop)
```

---

## Interactive menu

The default `./bin/start.sh dev` experience should feel like a **control panel**, not a bare numbered list.

**Header (refresh on each draw):**

- Compose project name and stack suffix
- Running / total containers (`docker compose ps -q`)
- Quick health: API `/health`, Postgres `pg_isready`, Redis `PING` (best-effort; show `down` if stack stopped)

**Body:** section headers (Stack, Logs & health, Development, Database, Danger zone) with numbered actions.

**Keys:** `0` exit · `r` refresh · `?` / `h` show `--help` · Enter to continue after most commands.

**Service picker:** reuse compose **service keys** (not container_name) for logs/shell submenus.

**Colors:** use `tput` when stderr is a TTY; empty strings when unavailable (CI-safe).

---

## Commands to implement (adapt per stack)

### Interactive menu (full-fledged)

When `dev` / no args / `menu`:

| Requirement | Detail |
|-------------|--------|
| **Header** | Project name, suffix, running/total container count, quick health (API, DB, Redis) |
| **Sections** | Stack · Logs & health · Development · Database · Danger zone |
| **Navigation** | Numeric choices; `r` refresh (redraw); `?` / `h` help; `0` exit |
| **Feedback** | Pause after commands that return to menu; show non-zero exit status |
| **TTY** | Read choices from `/dev/tty`; optional `tput` colors with plain fallback |
| **Sub-pickers** | Service list for per-service logs/shell (compose service keys) |

Minimum menu items for a stack with Postgres + API (extend per project):

| # | Section | CLI alias | Function |
|---|---------|-----------|----------|
| 1–2 | Stack | `start`, `start-fg` | detached / attached+log tail |
| 3–4 | Stack | `stop`, `restart` | down / down+up |
| 5–6 | Stack | `status`, `validate` | `ps -a`, `config -q` |
| 7–8 | Logs | `logs`, `logs:<svc>` | all / one service |
| 9–10 | Health | `health`, `urls` | probes + URL table |
| 11–14 | Dev | `shell-api`, `shell-psql`, … | exec into services |
| 15–16 | Dev | `pytest`, `ruff` | common in-container checks (adapt) |
| 17–18 | Dev | `pull`, `build` | image pull / build only |
| 19–21 | DB | `wait-pg`, `drop-schema`, `rebuild-schema` | see §Postgres pattern |
| 22 | Danger | `nuke` | `down -v` - double confirm |

### Headless CLI (same functions)

| CLI arg | Menu # | Function | Behaviour |
|---------|--------|----------|-----------|
| `start-fg` | 2 | `cmd_start_attached` | `up --build -d` then `logs -f --tail=200`; Ctrl-C stops tail only |
| `start` | 1 | `cmd_start_detached` | `up --build -d`; status + URL hints |
| `stop` | 3 | `cmd_stop` | `down` (keep volumes) |
| `restart` | 4 | `cmd_restart` | `down` then `up --build -d` |
| `status` | 5 | `cmd_status` | `ps -a` |
| `validate` | 6 | `cmd_validate_config` | `config -q` |
| `logs` | 7 | `cmd_logs_all` | `logs -f --tail=200` |
| `logs:<svc>` | 8 | `cmd_logs_service` | one service |
| `health` | 9 | `cmd_health` | HTTP + exec probes |
| `urls` | 10 | `urls_hint` | Print URLs from env |
| `shell-api` | 11 | `cmd_shell_api` | `exec api bash` |
| `shell-psql` | 12 | `cmd_shell_psql` | `exec pg psql …` |
| `shell:<svc>` | 14 | `cmd_shell_pick` | exec into named service |
| `pytest` / `ruff` | 15–16 | in-container dev checks | project-specific |
| `pull` | 17 | `cmd_pull` | `compose pull` |
| `build` | 18 | `cmd_build_only` | `build --pull` |
| `wait-pg` | 19 | `cmd_wait_postgres` | pg_isready loop |
| `drop-schema` | 20 | `cmd_drop_schema` | DROP SCHEMA - **DANGEROUS** |
| `rebuild-schema` | 21 | `cmd_rebuild_schema` | drop + restart api |
| `nuke` | 22 | `cmd_nuke` | `down -v --remove-orphans` - **DANGEROUS** |
| - | 0 | - | Exit menu |

---

## Postgres helpers (default - adapt service name)

### Wait for DB

```bash
cmd_wait_postgres() {
  local i
  for i in $(seq 1 45); do
    if _compose_invoke exec -T <db_service> pg_isready \
        -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  printf 'ERROR: Postgres did not become ready.\n' >&2
  return 1
}
```

### `cmd_drop_tables` (sketch)

1. `print_banner` + WARNING naming DB + `COMPOSE_PROJECT_NAME`.
2. First confirm: user types **exact database name**.
3. Second confirm: user types `DROP`.
4. `dc up -d <db_service>` → `cmd_wait_postgres` → `exec` psql / SQL file running `DROP SCHEMA public CASCADE; CREATE SCHEMA public;` + grants.

Adapt for non-Postgres or remove.

---

## Dangerous commands - double confirmation

Pattern (nuke volumes - adapt prompts):

```bash
read -r -p 'Type the project name to confirm: ' confirm
if [[ "$confirm" != "$COMPOSE_PROJECT_NAME" ]]; then
  printf 'Aborted (name mismatch).\n' >&2; return 0
fi
read -r -p 'Second confirm: type YES to delete volumes: ' confirm2
if [[ "$confirm2" != "YES" ]]; then
  printf 'Aborted.\n' >&2; return 0
fi
```

Always show **which** compose project and repo root before prompts.

---

## CI / headless

| Variable | Effect |
|----------|--------|
| `MENU_QUIET=1` | Capture compose output to temp file; on failure print full log to stderr and exit non-zero; on success delete temp |

Example:

```yaml
- run: MENU_QUIET=1 ./bin/start.sh start
```

Ensure `start`, `stop`, `build`, `status` never block on `read` when `MENU_QUIET=1`.

---

## Code quality (generated script)

- Prefer `printf` over `echo`.
- User messages to `>&2`; let compose stream to stdout/stderr as appropriate.
- Temp logs: `mktemp "${TMPDIR:-/tmp}/startsh.XXXXXX"`; `rm -f` on all paths.
- No `eval`; no command substitution on untrusted input.
- Prefer `[[ … ]]` over `[ … ]`.
- Works when invoked from any cwd: resolve `REPO_ROOT` from script location.

---

## `.env` variables (typical - extend per project)

| Variable | Role |
|----------|------|
| `COMPOSE_PROJECT_NAME` | Docker Compose **project** name - isolation |
| `PUBLIC_HOST` | URL hints (default `localhost`) |
| `*_HOST_PORT` | Published ports for hints |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | DB ops (if applicable) |

Document in script header which keys are read and their fallbacks.

---

## Example instance (customize per repo)

Document your project's values in `.cursorrules` and here after `@dev-stack` generates the script:

| Item | Typical placeholder |
|------|---------------------|
| Compose file | `docker-compose.yml` at repo root |
| Script | `REPLACE:DEV_STACK_SCRIPT` (e.g. `bin/start.sh`) |
| Project isolation | `COMPOSE_PROJECT_NAME` from `.env` |
| Stack suffix | `REPLACE:STACK_SUFFIX_VAR` → `container_name` `{role}-${suffix}` |
| Service keys | `REPLACE:SERVICE_API`, `REPLACE:SERVICE_DB`, … |
| Host ports | `*_HOST_PORT` vars in `.env` |
| `urls_hint` | `PUBLIC_HOST` + port vars |

**Never** `source .env`. `load_env` reads keys via `read_dotenv_value` (see §Safe `.env` parsing).

After compose changes, run `sh -n` on the script and a smoke command (`urls`, `health`, or equivalent).
