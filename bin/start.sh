#!/usr/bin/env bash
#
# tools-project — start/stop menu for the **this-repo-only** dev stack.
#
# Safety:
# - Every action runs `docker compose` with a fixed compose file, fixed project directory,
#   profile `dev`, and explicit `--project-name` (default / from .env: COMPOSE_PROJECT_NAME).
# - No global `docker stop`, `docker kill`, prune, or container ID wildcards.
#
# Usage: from anywhere —  ./bin/start.sh   or   /path/to/tools-project/bin/start.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_ABS="$REPO_ROOT/docker-compose.yml"
PROFILE="dev"
# Must match the default in docker-compose.yml for ${COMPOSE_PROJECT_NAME:-…}
DEFAULT_PROJECT_NAME="tools_project_dev"

# Read KEY=value from a dotenv file without `source` (safe for values like `profile email`,
# unquoted URLs, etc.). Splits on the first `=`. Returns via stdout; exit 1 if key missing.
read_dotenv_value() {
  local file="$1" key="$2" line k v
  [[ -f "$file" ]] || return 1
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line//[[:space:]]/}" ]] && continue
    [[ "$line" != *"="* ]] && continue
    k="${line%%=*}"
    v="${line#*=}"
    k="${k#"${k%%[![:space:]]*}"}"
    k="${k%"${k##*[![:space:]]}"}"
    v="${v#"${v%%[![:space:]]*}"}"
    v="${v%"${v##*[![:space:]]}"}"
    if [[ "$k" != "$key" ]]; then
      continue
    fi
    if [[ "$v" == \"*\" ]]; then
      v="${v#\"}"
      v="${v%\"}"
    elif [[ "$v" == \'*\' ]]; then
      v="${v#\'}"
      v="${v%\'}"
    fi
    printf '%s' "$v"
    return 0
  done <"$file"
  return 1
}

load_env() {
  local envf="$REPO_ROOT/.env"
  COMPOSE_PROJECT_NAME="$DEFAULT_PROJECT_NAME"
  PUBLIC_HOST="${PUBLIC_HOST:-localhost}"
  WEB_DEV_HOST_PORT="${WEB_DEV_HOST_PORT:-18513}"
  API_HOST_PORT="${API_HOST_PORT:-8300}"
  POSTGRES_USER="${POSTGRES_USER:-prj}"
  POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-prj_dev_change_me}"
  POSTGRES_DB="${POSTGRES_DB:-tools_project}"
  if [[ -f "$envf" ]]; then
    local v
    v="$(read_dotenv_value "$envf" COMPOSE_PROJECT_NAME)" && COMPOSE_PROJECT_NAME="$v"
    v="$(read_dotenv_value "$envf" PUBLIC_HOST)" && PUBLIC_HOST="$v"
    v="$(read_dotenv_value "$envf" WEB_DEV_HOST_PORT)" && WEB_DEV_HOST_PORT="$v"
    v="$(read_dotenv_value "$envf" API_HOST_PORT)" && API_HOST_PORT="$v"
    v="$(read_dotenv_value "$envf" POSTGRES_USER)" && POSTGRES_USER="$v"
    v="$(read_dotenv_value "$envf" POSTGRES_PASSWORD)" && POSTGRES_PASSWORD="$v"
    v="$(read_dotenv_value "$envf" POSTGRES_DB)" && POSTGRES_DB="$v"
  fi
  export COMPOSE_PROJECT_NAME PUBLIC_HOST WEB_DEV_HOST_PORT API_HOST_PORT
  export POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB
}

require_compose_file() {
  if [[ ! -f "$COMPOSE_ABS" ]]; then
    printf 'ERROR: compose file not found: %s\n' "$COMPOSE_ABS" >&2
    exit 1
  fi
}

# Expanded on each invocation (after load_env sets COMPOSE_PROJECT_NAME) — required for bash `set -u`.
_compose_invoke() {
  docker compose \
    --project-directory "$REPO_ROOT" \
    -f "$COMPOSE_ABS" \
    -p "$COMPOSE_PROJECT_NAME" \
    --profile "$PROFILE" \
    "$@"
}

# Always scope to this repository and this Compose project name — never touch other stacks.
dc() {
  _compose_invoke "$@"
}

# Used from the interactive menu (MENU_QUIET=1): swallow compose noise; print transcript on failure only.
quiet_dc() {
  local log ec
  log=$(mktemp "${TMPDIR:-/tmp}/tpr-startsh-compose.XXXXXX")
  if _compose_invoke "$@" >"$log" 2>&1; then
    rm -f "$log"
    return 0
  fi
  ec=$?
  printf '[docker compose exited %s] output:\n' "$ec" >&2
  cat "$log" >&2
  rm -f "$log"
  return "$ec"
}

# Run docker compose loudly (streams: logs -f, ps).
_dc_loud() {
  _compose_invoke "$@"
}

runs_menu_quiet() {
  [[ "${MENU_QUIET:-0}" == "1" ]]
}

print_banner() {
  printf '\n'
  printf '=== tools-project (siloed Docker Compose stack) ===\n'
  printf '  Repo root:        %s\n' "$REPO_ROOT"
  printf '  Compose file:     %s\n' "$COMPOSE_ABS"
  printf '  COMPOSE_PROJECT_NAME (isolates resources): %s\n' "$COMPOSE_PROJECT_NAME"
  printf '  Profile:          %s\n' "$PROFILE"
  printf '\n'
  printf 'Only containers/networks/volumes for this project name are affected.\n'
  printf '\n'
}

urls_hint() {
  local host="$PUBLIC_HOST"
  local web="$WEB_DEV_HOST_PORT"
  local api="$API_HOST_PORT"
  printf 'URLs (from env / defaults):\n'
  printf '  Web   http://%s:%s\n' "$host" "$web"
  printf '  API   http://%s:%s/healthz\n' "$host" "$api"
  printf '  Docs  http://%s:%s/docs\n' "$host" "$api"
  printf '\n'
}

validate_config() {
  printf 'Checking compose file… '
  if runs_menu_quiet; then
    quiet_dc config -q && printf 'OK\n\n'
  else
    dc config -q && printf 'OK\n\n'
  fi
}

cmd_start_attached() {
  validate_config
  # Foreground `docker compose up --build` stops containers on Ctrl+C — use detached up + logs -f instead.
  if runs_menu_quiet; then
    printf 'Detached start/rebuild + live logs.\n'
    printf 'Ctrl+C stops only this log tail — containers stay up.\n\n'
    quiet_dc up --build --quiet-pull -d || return 1
    dc ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'
    printf '\n'
    urls_hint
  else
    printf '`start-fg`: detached compose up --build -d, then log follow.\n'
    printf 'Ctrl+C stops only the log viewer; containers stay up.\n\n'
    _compose_invoke up --build -d || return 1
    dc ps
    printf '\n'
    urls_hint
  fi
  printf '\n----- compose logs (follow) ----------------------------\n\n'
  _dc_loud logs -f --tail=200 || true
  printf '\nLog follow exited.\n\n'
  return 0
}

cmd_start_detached() {
  validate_config
  printf 'Building / starting stack in detached mode…\n'
  if runs_menu_quiet; then
    quiet_dc up --build --quiet-pull -d
  else
    dc up --build -d
  fi
  if runs_menu_quiet; then
    dc ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'
  else
    dc ps
  fi
  printf '\nStack is up in the background.\n'
  urls_hint
}

cmd_stop() {
  validate_config
  printf 'Stopping stack (containers + project network; named volumes kept)…\n'
  if runs_menu_quiet; then
    quiet_dc down
  else
    dc down
  fi
  printf 'Done.\n\n'
}

cmd_restart() {
  validate_config
  if runs_menu_quiet; then
    quiet_dc down
    quiet_dc up --build --quiet-pull -d
    dc ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'
  else
    dc down
    dc up --build -d
    dc ps
  fi
  printf '\nRestart complete.\n'
  urls_hint
}

cmd_status() {
  validate_config
  _dc_loud ps -a
  printf '\n'
}

cmd_logs() {
  validate_config
  printf 'Following logs (Ctrl+C to stop tailing only; stack keeps running)…\n'
  _dc_loud logs -f --tail=200 || true
}

cmd_build_only() {
  validate_config
  printf 'Building images…\n'
  if runs_menu_quiet; then
    quiet_dc build --pull
  else
    dc build --pull
  fi
  printf 'Images rebuilt.\n\n'
}

cmd_nuke() {
  validate_config
  print_banner
  printf 'WARNING: This removes containers, networks, and Compose-managed NAMED volumes\n'
  printf 'for project %s only (Postgres data + web_node_modules volume).\n' "$COMPOSE_PROJECT_NAME"
  printf 'Other Docker apps and other Compose projects are NOT affected.\n\n'
  read -r -p 'Type the project name to confirm: ' confirm
  if [[ "$confirm" != "$COMPOSE_PROJECT_NAME" ]]; then
    printf 'Aborted (name mismatch).\n'
    return 0
  fi
  read -r -p 'Second confirm: type YES to delete volumes: ' confirm2
  if [[ "$confirm2" != "YES" ]]; then
    printf 'Aborted.\n'
    return 0
  fi
  if runs_menu_quiet; then
    quiet_dc down -v --remove-orphans
  else
    dc down -v --remove-orphans
  fi
  printf 'Done. Stack and its named volumes for this project are removed.\n\n'
}

cmd_wait_postgres() {
  validate_config
  local i
  for i in $(seq 1 45); do
    if _compose_invoke exec -T postgresql pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  printf 'ERROR: Postgres did not become ready.\n' >&2
  return 1
}

cmd_drop_tables() {
  validate_config
  print_banner
  printf 'WARNING: This drops ALL tables in database **%s** (user %s) for Compose project **%s**.\n' \
    "$POSTGRES_DB" "$POSTGRES_USER" "$COMPOSE_PROJECT_NAME"
  printf 'This is like a fresh **public** schema — all application data in this DB is removed.\n'
  printf 'Containers and Docker volumes are NOT removed (unlike option 8).\n\n'
  read -r -p "$(printf 'Type the database name to confirm [%s]: ' "$POSTGRES_DB")" confirm
  if [[ "$confirm" != "$POSTGRES_DB" ]]; then
    printf 'Aborted (database name mismatch).\n'
    return 0
  fi
  read -r -p 'Second confirm: type DROP to proceed: ' confirm2
  if [[ "$confirm2" != "DROP" ]]; then
    printf 'Aborted.\n'
    return 0
  fi
  printf 'Ensuring Postgres is running…\n'
  if runs_menu_quiet; then
    quiet_dc up -d postgresql >/dev/null
  else
    dc up -d postgresql >/dev/null
  fi
  cmd_wait_postgres || return 1
  printf 'Executing DROP SCHEMA public CASCADE…\n'
  local log
  if runs_menu_quiet; then
    log=$(mktemp "${TMPDIR:-/tmp}/tpr-drop-public.XXXXXX")
    if ! dc exec -T postgresql psql -q -v ON_ERROR_STOP=1 \
      -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'EOSQL' >"$log" 2>&1
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO CURRENT_USER;
GRANT ALL ON SCHEMA public TO public;
EOSQL
    then
      printf 'DROP SCHEMA failed:\n' >&2
      cat "$log" >&2
      rm -f "$log"
      return 1
    fi
    rm -f "$log"
  else
    dc exec -T postgresql psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" --set ON_ERROR_STOP=1 <<'EOSQL'
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO CURRENT_USER;
GRANT ALL ON SCHEMA public TO public;
EOSQL
  fi
  printf 'Done. Start the API next (option 2) so sql/schema_*.sql and bootstrap repopulate the DB.\n\n'
}

cmd_rebuild_schema() {
  validate_config
  printf 'Applying sql/schema_changes.sql + sql/schema_indexes.sql (missing objects only)…\n'
  if runs_menu_quiet; then
    quiet_dc up -d postgresql >/dev/null
  else
    dc up -d postgresql >/dev/null
  fi
  cmd_wait_postgres || return 1
  if runs_menu_quiet; then
    quiet_dc run --rm api python -m app.cli_schema apply-ddl
  else
    dc run --rm api python -m app.cli_schema apply-ddl
  fi
  printf 'DDL apply finished. Post-bootstrap scripts run when the API starts.\n\n'
}

show_menu() {
  print_banner
  cat <<EOF
  1) Start + follow logs                     — docker compose up -d --build, then logs -f (Ctrl+C: tail only; stack stays up)
  2) Start stack (detached, rebuild)        — docker compose up --build -d
  3) Stop stack                           — docker compose down
  4) Restart stack (detached)             — down, then up -d
  5) Status                               — docker compose ps -a
  6) Logs (follow)                        — docker compose logs -f
  7) Build images only                     — docker compose build --pull
  8) Destroy stack + volumes (DANGEROUS)  — docker compose down -v (this project only)
  9) Show URL hints
  10) Drop all DB tables (DANGEROUS)      — Postgres: DROP SCHEMA public CASCADE (project DB only)
  11) Rebuild DDL from SQL               — python -m app.cli_schema apply-ddl (missing objects only)
  0) Exit
EOF
  printf '\n'
}

main() {
  require_compose_file
  load_env

  if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    print_banner
    printf '%s [command]\n' "${0##*/}"
    printf '  With no args (or `dev`), runs interactively.\n'
    printf '  Commands: start-fg (detached up --build, then logs -f; Ctrl+C stops tail only) |\n'
    printf '           start | stop | restart | status | logs | build | nuke | drop-tables | rebuild-schema | urls\n'
    exit 0
  fi

  case "${1:-}" in
    start-fg) cmd_start_attached ;;
    start)    cmd_start_detached ;;
    stop)     cmd_stop ;;
    restart)  cmd_restart ;;
    status)   cmd_status ;;
    logs)     cmd_logs ;;
    build)    cmd_build_only ;;
    nuke)          cmd_nuke ;;
    drop-tables)   cmd_drop_tables ;;
    rebuild-schema) cmd_rebuild_schema ;;
    urls)          urls_hint ;;
    dev|"")
      # Interactive menu: MENU_QUIET uses quiet_dc for noisy compose steps; logs -f stays loud on options 1 and 6.
      MENU_QUIET=1
      while true; do
        show_menu
        read -r -p 'Choose [0-11]: ' choice || true
        set +e
        case "$choice" in
          1) cmd_start_attached ;;
          2) cmd_start_detached ;;
          3) cmd_stop ;;
          4) cmd_restart ;;
          5) cmd_status ;;
          6) cmd_logs ;;
          7) cmd_build_only ;;
          8) cmd_nuke ;;
          9) urls_hint ;;
          10) cmd_drop_tables ;;
          11) cmd_rebuild_schema ;;
          0) printf 'Bye.\n'; exit 0 ;;
          *) printf 'Invalid option.\n\n' ;;
        esac
        set -e
      done
      ;;
    *)
      printf 'Unknown command: %s (try --help)\n' "$1" >&2
      exit 1
      ;;
  esac
}

main "$@"
