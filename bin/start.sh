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

load_env() {
  if [[ -f "$REPO_ROOT/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$REPO_ROOT/.env"
    set +a
  fi
  export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-$DEFAULT_PROJECT_NAME}"
}

require_compose_file() {
  if [[ ! -f "$COMPOSE_ABS" ]]; then
    printf 'ERROR: compose file not found: %s\n' "$COMPOSE_ABS" >&2
    exit 1
  fi
}

# Always scope to this repository and this Compose project name — never touch other stacks.
dc() {
  docker compose \
    --project-directory "$REPO_ROOT" \
    -f "$COMPOSE_ABS" \
    -p "$COMPOSE_PROJECT_NAME" \
    --profile "$PROFILE" \
    "$@"
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
  local host="${PUBLIC_HOST:-localhost}"
  local web="${WEB_DEV_HOST_PORT:-18513}"
  local api="${API_HOST_PORT:-8300}"
  printf 'URLs (from env / defaults):\n'
  printf '  Web   http://%s:%s\n' "$host" "$web"
  printf '  API   http://%s:%s/healthz\n' "$host" "$api"
  printf '  Docs  http://%s:%s/docs\n' "$host" "$api"
  printf '\n'
}

validate_config() {
  printf 'Validating compose configuration…\n'
  dc config -q
  printf 'OK\n\n'
}

cmd_start_attached() {
  validate_config
  dc up --build
}

cmd_start_detached() {
  validate_config
  dc up --build -d
  dc ps
  printf '\nStack is up in the background.\n'
  urls_hint
}

cmd_stop() {
  validate_config
  printf 'Stopping stack (containers + project network; named volumes kept)…\n'
  dc down
  printf 'Done.\n\n'
}

cmd_restart() {
  validate_config
  dc down
  dc up --build -d
  dc ps
  printf '\nRestart complete.\n'
  urls_hint
}

cmd_status() {
  validate_config
  dc ps -a
  printf '\n'
}

cmd_logs() {
  validate_config
  printf 'Following logs (Ctrl+C to stop tailing only; stack keeps running)…\n'
  dc logs -f --tail=200 || true
}

cmd_build_only() {
  validate_config
  dc build --pull
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
  dc down -v --remove-orphans
  printf 'Done. Stack and its named volumes for this project are removed.\n\n'
}

show_menu() {
  print_banner
  cat <<EOF
  1) Start stack (foreground, rebuild)     — docker compose up --build
  2) Start stack (detached, rebuild)      — docker compose up --build -d
  3) Stop stack                           — docker compose down
  4) Restart stack (detached)             — down, then up -d
  5) Status                               — docker compose ps -a
  6) Logs (follow)                        — docker compose logs -f
  7) Build images only                     — docker compose build --pull
  8) Destroy stack + volumes (DANGEROUS)  — docker compose down -v (this project only)
  9) Show URL hints
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
    printf '  With no args, runs interactively.\n'
    printf '  Non-interactive: start-fg | start | stop | restart | status | logs | build | nuke | urls\n'
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
    nuke)     cmd_nuke ;;
    urls)     urls_hint ;;
    "")
      while true; do
        show_menu
        read -r -p 'Choose [0-9]: ' choice || true
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
          0) printf 'Bye.\n'; exit 0 ;;
          *) printf 'Invalid option.\n\n' ;;
        esac
      done
      ;;
    *)
      printf 'Unknown command: %s (try --help)\n' "$1" >&2
      exit 1
      ;;
  esac
}

main "$@"
