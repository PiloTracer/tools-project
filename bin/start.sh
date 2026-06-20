#!/usr/bin/env bash
#
# tools-project — start/stop menu for the **this-repo-only** dev stack.
#
# Safety:
# - Every action runs `docker compose` with a fixed compose file, fixed project directory,
#   profile `dev`, and explicit `--project-name` (default / from .env: COMPOSE_PROJECT_NAME).
# - No global `docker stop`, `docker kill`, prune, or container ID wildcards.
# - Interactive menu (`dev` / no args): `START_SH_MENU=1` streams compose up/down/run to the TTY
#   and pauses for a keypress after each compose step (CLI subcommands keep non-interactive behavior).
#
# Usage: from anywhere —  ./bin/start.sh   or   /path/to/tools-project/bin/start.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROFILE="dev"
# Default compose file — overridden in load_env() for prd mode.
COMPOSE_ABS="$REPO_ROOT/docker-compose.dev.yml"
# Must match the default in docker-compose.dev.yml for ${COMPOSE_PROJECT_NAME:-…}
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

ENV_MODE="${ENV_MODE:-dev}"

load_env() {
  local env_name="${1:-dev}"
  ENV_MODE="$env_name"
  local envf
  case "$env_name" in
    dev|"")
      envf="$REPO_ROOT/.env.dev"
      [[ -f "$envf" ]] || envf="$REPO_ROOT/.env"
      ENV_MODE="dev"
      COMPOSE_ABS="$REPO_ROOT/docker-compose.dev.yml"
      ;;
    prd)
      envf="$REPO_ROOT/.env.prd"
      ENV_MODE="prd"
      COMPOSE_ABS="$REPO_ROOT/docker-compose.prd.yml"
      ;;
    *)
      envf="$REPO_ROOT/.env"
      ENV_MODE="$env_name"
      COMPOSE_ABS="$REPO_ROOT/docker-compose.dev.yml"
      ;;
  esac
  COMPOSE_PROJECT_NAME="$DEFAULT_PROJECT_NAME"
  PUBLIC_HOST="${PUBLIC_HOST:-localhost}"
  WEB_DEV_HOST_PORT="${WEB_DEV_HOST_PORT:-18513}"
  API_HOST_PORT="${API_HOST_PORT:-8300}"
  POSTGRES_USER="${POSTGRES_USER:-prj}"
  POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-prj_dev_change_me}"
  POSTGRES_DB="${POSTGRES_DB:-tools_project}"
  GLOBAL_BASE_PATH="${GLOBAL_BASE_PATH:-/mnt/data}"
  BOOTSTRAP_ADMIN_EMAIL="${BOOTSTRAP_ADMIN_EMAIL:-}"
  BOOTSTRAP_ADMIN_PASSWORD="${BOOTSTRAP_ADMIN_PASSWORD:-}"
  if [[ -f "$envf" ]]; then
    local v
    v="$(read_dotenv_value "$envf" COMPOSE_PROJECT_NAME)" && COMPOSE_PROJECT_NAME="$v"
    v="$(read_dotenv_value "$envf" PUBLIC_HOST)" && PUBLIC_HOST="$v"
    v="$(read_dotenv_value "$envf" WEB_DEV_HOST_PORT)" && WEB_DEV_HOST_PORT="$v"
    v="$(read_dotenv_value "$envf" API_HOST_PORT)" && API_HOST_PORT="$v"
    v="$(read_dotenv_value "$envf" POSTGRES_USER)" && POSTGRES_USER="$v"
    v="$(read_dotenv_value "$envf" POSTGRES_PASSWORD)" && POSTGRES_PASSWORD="$v"
    v="$(read_dotenv_value "$envf" POSTGRES_DB)" && POSTGRES_DB="$v"
    v="$(read_dotenv_value "$envf" GLOBAL_BASE_PATH)" && GLOBAL_BASE_PATH="$v"
    v="$(read_dotenv_value "$envf" BOOTSTRAP_ADMIN_EMAIL)" && BOOTSTRAP_ADMIN_EMAIL="$v"
    v="$(read_dotenv_value "$envf" BOOTSTRAP_ADMIN_PASSWORD)" && BOOTSTRAP_ADMIN_PASSWORD="$v"
  fi
  export COMPOSE_PROJECT_NAME PUBLIC_HOST WEB_DEV_HOST_PORT API_HOST_PORT COMPOSE_ABS
  export POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB GLOBAL_BASE_PATH
  export ENV_MODE BOOTSTRAP_ADMIN_EMAIL BOOTSTRAP_ADMIN_PASSWORD
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

# Optional (MENU_QUIET=1): swallow compose stdout/stderr; print transcript on failure only.
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

# Interactive menu (./bin/start.sh dev): always stream compose pull/build/up/down to the TTY
# so Docker shows progress lines ([+] down n/m, ✔ Removed, …). CLI invocations honor MENU_QUIET.
stream_compose_ops() {
  [[ "${START_SH_MENU:-0}" == "1" ]] && return 0
  ! runs_menu_quiet
}

# After compose start/stop output, let the user read the transcript before the script continues.
wait_ack_if_menu() {
  [[ "${START_SH_MENU:-0}" == "1" ]] || return 0
  printf '\n' >&2
  if [[ -r /dev/tty ]] && [[ -w /dev/tty ]]; then
    read -r -n1 -s -p 'Press any key to continue… ' < /dev/tty || true
  else
    read -r -n1 -s -p 'Press any key to continue… ' || true
  fi
  printf '\n\n' >&2
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
  printf 'Login URLs:\n'
  printf '  Web   http://%s:%s\n' "$host" "$web"
  printf '  API   http://%s:%s/healthz\n' "$host" "$api"
  printf '  Docs  http://%s:%s/docs\n' "$host" "$api"
  printf '\n'
}

confirm_yes() {
  local prompt="${1:-Type \"yes\" to confirm: }"
  local reply
  read -r -p "$prompt" reply
  if [[ "${reply,,}" != "yes" ]]; then
    printf 'Aborted.\n'
    return 1
  fi
  return 0
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
    if stream_compose_ops; then
      wait_ack_if_menu
    fi
    dc ps
    printf '\n'
    urls_hint
    if stream_compose_ops; then
      wait_ack_if_menu
    fi
  fi
  printf '\n----- compose logs (follow) ----------------------------\n\n'
  _dc_loud logs -f --tail=200 || true
  printf '\nLog follow exited.\n\n'
  return 0
}

cmd_start_detached() {
  validate_config
  printf 'Building / starting stack in detached mode…\n'
  if stream_compose_ops; then
    dc up --build -d || return 1
    wait_ack_if_menu
  elif runs_menu_quiet; then
    quiet_dc up --build --quiet-pull -d || return 1
  else
    dc up --build -d || return 1
  fi
  if runs_menu_quiet; then
    dc ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'
  else
    dc ps
  fi
  printf '\nStack is up in the background.\n'
  urls_hint
  if stream_compose_ops; then
    wait_ack_if_menu
  fi
}

cmd_stop() {
  validate_config
  printf 'Stopping stack (containers + project network; named volumes kept)…\n'
  if stream_compose_ops; then
    dc down || return 1
    wait_ack_if_menu
  elif runs_menu_quiet; then
    quiet_dc down || return 1
  else
    dc down || return 1
  fi
  printf 'Done.\n\n'
}

cmd_restart() {
  validate_config
  if stream_compose_ops; then
    dc down || return 1
    wait_ack_if_menu
    dc up --build -d || return 1
    wait_ack_if_menu
    dc ps
  elif runs_menu_quiet; then
    quiet_dc down || return 1
    quiet_dc up --build --quiet-pull -d || return 1
    dc ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'
  else
    dc down || return 1
    dc up --build -d || return 1
    dc ps
  fi
  printf '\nRestart complete.\n'
  urls_hint
  if stream_compose_ops; then
    wait_ack_if_menu
  fi
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

cmd_cleanup_stack() {
  validate_config
  printf 'Cleaning up stack (containers, networks, orphans) for project %s…\n' "$COMPOSE_PROJECT_NAME"
  printf 'Named volumes (data) are KEPT. Other Docker stacks are NOT affected.\n\n'
  if stream_compose_ops; then
    dc down --remove-orphans || return 1
    wait_ack_if_menu
  elif runs_menu_quiet; then
    quiet_dc down --remove-orphans || return 1
  else
    dc down --remove-orphans || return 1
  fi
  printf 'Cleanup complete. Stack containers/networks removed; data volumes preserved.\n\n'
}

cmd_backup() {
  validate_config
  local backup_base="${GLOBAL_BASE_PATH}/backups_${COMPOSE_PROJECT_NAME}"
  local timestamp
  timestamp=$(date +%Y%m%d_%H%M%S)
  local backup_dir="${backup_base}/${timestamp}"

  mkdir -p "$backup_dir"

  # Named volume backups as .tar.gz (no SQL dumps)
  for vol in tpr_pg_data tpr_attachments; do
    local vol_name="${COMPOSE_PROJECT_NAME}_${vol}"
    printf 'Backing up volume: %s…\n' "$vol_name"
    if docker volume inspect "$vol_name" >/dev/null 2>&1; then
      docker run --rm \
        -v "${vol_name}":/source:ro \
        -v "$backup_dir":/dest \
        busybox tar czf "/dest/${vol}.tar.gz" -C /source . 2>/dev/null || {
        printf '  WARNING: tar backup of %s failed (volume may be empty or in use).\n' "$vol_name" >&2
        continue
      }
      printf '  %s.tar.gz: %d bytes\n' "$vol" "$(wc -c < "$backup_dir/${vol}.tar.gz")"
    else
      printf '  WARNING: volume %s does not exist — skipping.\n' "$vol_name" >&2
    fi
  done

  # Write a metadata file
  cat > "$backup_dir/backup.info" <<EOF
timestamp=$timestamp
compose_project_name=$COMPOSE_PROJECT_NAME
created_by=start.sh cmd_backup
EOF

  printf '\nBackup complete: %s\n' "$backup_dir"
}

cmd_restore() {
  validate_config
  local backup_base="${GLOBAL_BASE_PATH}/backups_${COMPOSE_PROJECT_NAME}"

  if [[ ! -d "$backup_base" ]]; then
    printf 'No backups found at %s\n' "$backup_base" >&2
    return 1
  fi

  # List available backups (newest last)
  local backups=()
  while IFS= read -r -d '' d; do
    backups+=("$d")
  done < <(find "$backup_base" -maxdepth 1 -type d -name '????????_??????' -print0 | sort -z)

  if [[ ${#backups[@]} -eq 0 ]]; then
    printf 'No backups found at %s\n' "$backup_base" >&2
    return 1
  fi

  printf 'Available backups:\n'
  for i in "${!backups[@]}"; do
    local name; name=$(basename "${backups[$i]}")
    local info; info=$(cat "${backups[$i]}/backup.info" 2>/dev/null | head -1 || true)
    printf '  %2d) %s  %s\n' $((i+1)) "$name" "${info:+($info)}"
  done

  read -r -p 'Select backup to restore [1-'"${#backups[@]}"']: ' sel
  if [[ ! "$sel" =~ ^[0-9]+$ ]] || [[ "$sel" -lt 1 ]] || [[ "$sel" -gt "${#backups[@]}" ]]; then
    printf 'Invalid selection.\n' >&2
    return 1
  fi

  local restore_dir="${backups[$((sel-1))]}"
  local restore_name; restore_name=$(basename "$restore_dir")

  printf '\nWARNING: This will OVERWRITE the database and named volumes for project\n'
  printf '  %s\n' "$COMPOSE_PROJECT_NAME"
  printf 'with the state from backup: %s\n\n' "$restore_name"
  confirm_yes 'Type "yes" to confirm: ' || return 0

  printf '\nStopping stack…\n'
  if stream_compose_ops; then
    dc down --remove-orphans || return 1
    wait_ack_if_menu
  elif runs_menu_quiet; then
    quiet_dc down --remove-orphans || return 1
  else
    dc down --remove-orphans || return 1
  fi

  # Restore named volumes from .tar.gz (overwrite existing content)
  for vol in tpr_pg_data tpr_attachments; do
    local vol_name="${COMPOSE_PROJECT_NAME}_${vol}"
    local tar_file="${restore_dir}/${vol}.tar.gz"
    if [[ -f "$tar_file" ]]; then
      printf 'Restoring volume: %s from %s…\n' "$vol_name" "$tar_file"
      # Remove existing volume contents, recreate, and restore
      docker volume rm -f "$vol_name" >/dev/null 2>&1 || true
      docker volume create "$vol_name" >/dev/null
      docker run --rm \
        -v "${vol_name}":/target \
        -v "$restore_dir":/source:ro \
        busybox tar xzf "/source/${vol}.tar.gz" -C /target || {
        printf '  ERROR: tar restore of %s failed.\n' "$vol_name" >&2
        return 1
      }
    else
      printf '  WARNING: no backup tar for volume %s — skipping.\n' "$vol_name" >&2
    fi
  done

  printf '\nRestore complete from: %s\n' "$restore_name"
  printf 'Run option 2 (start stack) to bring services back up.\n\n'}]}
}

cmd_nuke() {
  validate_config
  print_banner
  printf 'WARNING: This removes containers, networks, and Compose-managed NAMED volumes\n'
  printf 'for project %s only (Postgres data + web_node_modules volume).\n' "$COMPOSE_PROJECT_NAME"
  printf 'Other Docker apps and other Compose projects are NOT affected.\n\n'
  confirm_yes 'Type "yes" to confirm: ' || return 0
  if stream_compose_ops; then
    dc down -v --remove-orphans || return 1
    wait_ack_if_menu
  elif runs_menu_quiet; then
    quiet_dc down -v --remove-orphans || return 1
  else
    dc down -v --remove-orphans || return 1
  fi
  printf 'Done. Stack and its named volumes for this project are removed.\n\n'
  if stream_compose_ops; then
    wait_ack_if_menu
  fi
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
  printf 'Containers and Docker volumes are NOT removed.\n\n'
  confirm_yes 'Type "yes" to confirm: ' || return 0
  printf 'Ensuring Postgres is running…\n'
  if stream_compose_ops; then
    dc up -d postgresql || return 1
    wait_ack_if_menu
  elif runs_menu_quiet; then
    quiet_dc up -d postgresql || return 1
  else
    dc up -d postgresql || return 1
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
  printf 'Done. Run option 11 (apply sql + bootstrap + seeds) or start the API (option 2) to repopulate.\n\n'
  if stream_compose_ops; then
    wait_ack_if_menu
  fi
}

cmd_rebuild_schema() {
  validate_config
  printf 'Applying sql/schema_*.sql + bootstrap + seeds (same phases as API startup)…\n'
  if stream_compose_ops; then
    dc up -d postgresql || return 1
    wait_ack_if_menu
  elif runs_menu_quiet; then
    quiet_dc up -d postgresql || return 1
  else
    dc up -d postgresql || return 1
  fi
  cmd_wait_postgres || return 1
  if stream_compose_ops; then
    dc run --rm api python -m app.cli_schema apply-ddl || return 1
    wait_ack_if_menu
  elif runs_menu_quiet; then
    quiet_dc run --rm api python -m app.cli_schema apply-ddl || return 1
  else
    dc run --rm api python -m app.cli_schema apply-ddl || return 1
  fi
  printf 'Schema rebuild finished (DDL → bootstrap → backfill/inserts).\n\n'
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
  8) Cleanup stack (gentle)               — docker compose down --remove-orphans (keeps volumes)
  9) Backup (volumes .tar.gz)             — to \$GLOBAL_BASE_PATH/backups_\$COMPOSE_PROJECT_NAME
  10) Restore from backup                  — pick a previous backup to restore
  11) Destroy stack + volumes (DANGEROUS)  — docker compose down -v (this project only)
  12) Drop all DB tables (DANGEROUS)      — Postgres: DROP SCHEMA public CASCADE (project DB only)
  13) Rebuild DDL from SQL                — sql/schema_*.sql + bootstrap + seeds (mirrors API startup)
  0) Exit
EOF
  printf '\n'
  urls_hint
  if [[ "$ENV_MODE" == "dev" ]]; then
    printf -- '--- Test credentials (dev) ---\n'
    if [[ -n "$BOOTSTRAP_ADMIN_EMAIL" ]] && [[ -n "$BOOTSTRAP_ADMIN_PASSWORD" ]]; then
      printf '  Admin:  %s / %s\n' "$BOOTSTRAP_ADMIN_EMAIL" "$BOOTSTRAP_ADMIN_PASSWORD"
    fi
    printf '  Client: alice@umbrella-corp.test / client-demo\n'
    printf '\n'
  fi
}

main() {
  load_env "${1:-}"
  require_compose_file

  if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    print_banner
    printf '%s [command]\n' "${0##*/}"
    printf '  With no args (or `dev`), opens interactive dev menu (uses .env.dev / .env).\n'
    printf '  `prd` opens interactive production menu (uses .env only).\n'
    printf '  Commands: start-fg (detached up --build, then logs -f; Ctrl+C stops tail only) |\n'
    printf '           start | stop | restart | status | logs | build | cleanup |\n'
    printf '           backup | restore | nuke | drop-tables | rebuild-schema | urls\n'
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
    cleanup)       cmd_cleanup_stack ;;
    backup)        cmd_backup ;;
    restore)       cmd_restore ;;
    nuke)          cmd_nuke ;;
    drop-tables)   cmd_drop_tables ;;
    rebuild-schema) cmd_rebuild_schema ;;
    urls)          urls_hint ;;
    dev)
      START_SH_MENU=1
      MENU_QUIET=0
      while true; do
        show_menu
        read -r -p 'Choose [0-13]: ' choice || true
        set +e
        case "$choice" in
          1) cmd_start_attached ;;
          2) cmd_start_detached ;;
          3) cmd_stop ;;
          4) cmd_restart ;;
          5) cmd_status ;;
          6) cmd_logs ;;
          7) cmd_build_only ;;
          8) cmd_cleanup_stack ;;
          9) cmd_backup ;;
          10) cmd_restore ;;
          11) cmd_nuke ;;
          12) cmd_drop_tables ;;
          13) cmd_rebuild_schema ;;
          0) printf 'Bye.\n'; exit 0 ;;
          *) printf 'Invalid option.\n\n' ;;
        esac
        set -e
      done
      ;;
    prd)
      START_SH_MENU=1
      MENU_QUIET=0
      while true; do
        show_menu
        read -r -p 'Choose [0-13]: ' choice || true
        set +e
        case "$choice" in
          1) cmd_start_attached ;;
          2) cmd_start_detached ;;
          3) cmd_stop ;;
          4) cmd_restart ;;
          5) cmd_status ;;
          6) cmd_logs ;;
          7) cmd_build_only ;;
          8) cmd_cleanup_stack ;;
          9) cmd_backup ;;
          10) cmd_restore ;;
          11) cmd_nuke ;;
          12) cmd_drop_tables ;;
          13) cmd_rebuild_schema ;;
          0) printf 'Bye.\n'; exit 0 ;;
          *) printf 'Invalid option.\n\n' ;;
        esac
        set -e
      done
      ;;
    "")
      # Default (no args): same as dev mode.
      load_env dev
      START_SH_MENU=1
      MENU_QUIET=0
      while true; do
        show_menu
        read -r -p 'Choose [0-13]: ' choice || true
        set +e
        case "$choice" in
          1) cmd_start_attached ;;
          2) cmd_start_detached ;;
          3) cmd_stop ;;
          4) cmd_restart ;;
          5) cmd_status ;;
          6) cmd_logs ;;
          7) cmd_build_only ;;
          8) cmd_cleanup_stack ;;
          9) cmd_backup ;;
          10) cmd_restore ;;
          11) cmd_nuke ;;
          12) cmd_drop_tables ;;
          13) cmd_rebuild_schema ;;
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
