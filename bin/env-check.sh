#!/usr/bin/env bash
#
# tools-project — environment check for a stack mode (`bin/env-check.sh dev|prd`).
#
# Verifies that the mode's env file is COMPLETE before anything touches the stack:
#   1. every key the compose file requires hard (`${VAR:?…}`) is present and non-empty
#   2. every key `bin/start.sh` itself consumes from the env file is present
#      (those are exported as shell env, which outranks `--env-file` — a missing key
#      would silently inject that variable's default into the stack)
#   3. key-set parity with `.env.example` (the tracked template)
#   4. no duplicate / malformed keys
# Informational (never fails the run): keys the compose file uses without documenting them
# in `.env.example`, and code the compose file forgets to wire into its service block.
#
# Only `.env.dev` / `.env.prd` are ever read — a bare `.env` is never used (it is reported
# when present so the leftover can be removed).
#
# Usage:  bin/env-check.sh <dev|prd> [--quiet]
# Exit:   0 = all checks pass (informational findings allowed)
#         1 = at least one required key is missing/empty (or a duplicate/malformed key)
#         2 = usage error, or the mode env file does not exist

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
START_SH="$SCRIPT_DIR/start.sh"
EXAMPLE="$REPO_ROOT/.env.example"

# Production env file: repository root first, then an external secret directory
# ($TOOLS_PROJECT_SECRET_DIR, else the sibling `tools-project-secret/`).
# Keep in sync with bin/start.sh.
resolve_prd_file() {
  local cand
  for cand in "$REPO_ROOT/.env.prd" \
              "${TOOLS_PROJECT_SECRET_DIR:-$REPO_ROOT/../tools-project-secret}/.env.prd"; do
    [[ -f "$cand" ]] && { printf '%s' "$cand"; return 0; }
  done
  printf '%s' "$REPO_ROOT/.env.prd"
}

mode=""
quiet=0
diff=0
for arg in "$@"; do
  case "$arg" in
    dev|prd) mode="$arg" ;;
    all|both|--all) mode="all" ;;
    --diff|--compare) diff=1 ;;
    --quiet|-q) quiet=1 ;;
    -h|--help) mode="help" ;;
    *) printf 'env-check: unknown argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

# No mode given → check every mode file that exists on this machine.
[[ -z "$mode" ]] && mode="all"

if [[ "$mode" == "help" ]]; then
  printf 'Usage: %s [dev|prd|all] [--diff] [--quiet]\n' "${0##*/}"
  printf '  (no argument = all)  verify the mode env file(s) are complete:\n'
  printf '    ./bin/env-check.sh            # .env.dev and .env.prd (whichever exist here)\n'
  printf '    ./bin/env-check.sh dev        # dev stack  (.env.dev  + docker-compose.dev.yml)\n'
  printf '    ./bin/env-check.sh prd        # production (.env.prd  + docker-compose.prd.yml)\n'
  printf '    ./bin/env-check.sh --diff     # side-by-side line comparison of all three files\n'
  printf '  A mode file is complete when: every ${VAR:?} the compose file demands is present\n'
  printf '  and non-empty, every key bin/start.sh consumes is present, every key documented\n'
  printf '  in .env.example is present, and each key sits on the SAME LINE as in .env.example.\n'
  printf '  Never reads a bare `.env`. Key names only are ever printed — never values.\n'
  exit 0
fi

# ── side-by-side view: .env.example | .env.dev | .env.prd, by line number ─────
if [[ "$diff" -eq 1 ]]; then
  prd_file="$(resolve_prd_file)"
  for f in "$EXAMPLE" "$REPO_ROOT/.env.dev" "$prd_file"; do
    [[ -f "$f" ]] || { printf 'env-check --diff: missing file: %s\n' "$f" >&2; exit 2; }
  done
  printf 'env-check --diff (key names only, by line number)\n'
  printf '  example: %s\n  dev:     %s\n  prd:     %s\n\n' "$EXAMPLE" "$REPO_ROOT/.env.dev" "$prd_file"
  awk '
    function key(line) {
      s = line; sub(/^[[:space:]]+/, "", s)
      if (s ~ /^#/ || s !~ /=/) { return (s == "" ? "." : (s ~ /^#/ ? "#" : "?")) }
      k = s; sub(/=.*/, "", k)
      return (k ~ /^[A-Za-z_][A-Za-z0-9_]*$/ ? k : "?")
    }
    FNR == 1 { f++ }
    { rows[f, FNR] = key($0); if (FNR > max) max = FNR }
    END {
      printf "  %4s  %-38s %-38s %-38s\n", "line", "example", "dev", "prd"
      printf "  %s\n", "------------------------------------------------------------------------------------------------"
      bad = 0
      for (i = 1; i <= max; i++) {
        a = (i in rows) ? "" : ""; e = rows[1, i]; d = rows[2, i]; p = rows[3, i]
        if (e == "") e = "-"; if (d == "") d = "-"; if (p == "") p = "-"
        flag = (e == d && d == p) ? "" : "  << MISMATCH"
        if (flag != "") bad++
        printf "  %4d  %-38s %-38s %-38s%s\n", i, e, d, p, flag
      }
      printf "\n  %d of %d lines differ\n", bad, max
    }' "$EXAMPLE" "$REPO_ROOT/.env.dev" "$prd_file"
  exit 0
fi

# `all` = run this same check once per mode and summarise. A mode file that does not
# exist here (e.g. .env.prd on a dev box) is reported as MISSING, not as a failure.
if [[ "$mode" == "all" ]]; then
  overall=0
  printf 'env-check: verifying every mode file present on this machine\n'
  for m in dev prd; do
    case "$m" in
      dev) f="$REPO_ROOT/.env.dev" ;;
      prd) f="$(resolve_prd_file)" ;;
    esac
    if [[ ! -f "$f" ]]; then
      printf '  %-4s MISSING  %s — nothing to verify here (create it on that host)\n' "$m" "${f##*/}"
      continue
    fi
    out="$("$0" "$m")" && rc=0 || rc=$?
    if [[ "$rc" -eq 0 ]]; then
      counts="$(printf '%s\n' "$out" | sed -n '2p' | sed 's/^  //')"
      printf '  %-4s PASS     %s\n' "$m" "$counts"
      notes_block="$(printf '%s\n' "$out" | sed -n '/informational note/,$p' | sed '1d')"
      if [[ -n "$notes_block" ]]; then
        printf '%s\n' "$notes_block" | sed 's/^/         /'
      fi
    else
      printf '  %-4s FAIL     %s\n' "$m" "${f##*/}"
      printf '%s\n' "$out" | sed -n '/problem(s)/,$p' | sed 's/^/         /'
      overall=1
    fi
  done
  if [[ "$overall" -eq 0 ]]; then
    printf 'env-check: PASS — every mode file present on this machine is complete\n'
  else
    printf 'env-check: FAIL — fix the keys listed above\n'
  fi
  exit "$overall"
fi

case "$mode" in
  dev) ENV_FILE="$REPO_ROOT/.env.dev"; COMPOSE_FILE="$REPO_ROOT/docker-compose.dev.yml" ;;
  prd) ENV_FILE="$(resolve_prd_file)"; COMPOSE_FILE="$REPO_ROOT/docker-compose.prd.yml" ;;
esac

fail=0
problems=()
notes=()

problem() { problems+=("$1"); fail=1; }
note() { notes+=("$1"); }

if [[ ! -f "$ENV_FILE" ]]; then
  printf 'env-check: FAIL (%s) — %s not found.\n' "$mode" "$ENV_FILE" >&2
  printf '           Copy .env.example to %s and fill it in (a bare `.env` is never used).\n' \
    "${ENV_FILE##*/}" >&2
  exit 2
fi
if [[ ! -f "$COMPOSE_FILE" ]]; then
  printf 'env-check: FAIL (%s) — compose file not found: %s\n' "$mode" "$COMPOSE_FILE" >&2
  exit 2
fi

# ── key extraction ────────────────────────────────────────────────────────────
# Uncommented KEY=value lines with a valid shell-style name.
dotenv_keys() {
  awk -F= '/^[[:space:]]*#/ {next}
           /^[[:space:]]*$/ {next}
           /=/ {k=$1; gsub(/[[:space:]]/, "", k)
                if (k ~ /^[A-Za-z_][A-Za-z0-9_]*$/) print k}' "$1" | sort
}
# Keys whose value is empty (declared but blank).
dotenv_empty_keys() {
  awk '/^[[:space:]]*#/ {next}
       /=/ {line=$0; sub(/^[[:space:]]*/, "", line)
            k=line; sub(/=.*/, "", k)
            v=line; sub(/^[^=]*=/, "", v); gsub(/[[:space:]]/, "", v)
            if (k ~ /^[A-Za-z_][A-Za-z0-9_]*$/ && v == "") print k}' "$1" | sort
}
# Keys a file documents but ships commented out (`# KEY=…`) — optional-by-design options.
dotenv_commented_keys() {
  awk '/^[[:space:]]*#/ {
         s=$0; sub(/^[[:space:]]*#[[:space:]]*/, "", s)
         if (s ~ /=/) { k=s; sub(/=.*/, "", k); gsub(/[[:space:]]/, "", k)
                        if (k ~ /^[A-Za-z_][A-Za-z0-9_]*$/) print k } }' "$1" | sort -u
}
# Every `${VAR…}` interpolation reference in a compose file.
compose_keys() {
  grep -oE '\$\{[A-Za-z_][A-Za-z0-9_]*' "$1" | sed 's/^\${//' | sort -u
}
# References marked hard-required: `${VAR:?…}` (Compose aborts when unset OR empty).
compose_hard_keys() {
  grep -oE '\$\{[A-Za-z_][A-Za-z0-9_]*:\?' "$1" | sed 's/^\${//; s/:?$//' | sort -u
}
# Keys `bin/start.sh` reads out of the mode env file.
start_sh_keys() {
  grep -oE 'read_dotenv_value "\$ENV_FILE" [A-Z_]+' "$START_SH" | awk '{print $3}' | sort -u
}
# Keys that start.sh exports as shell env — a missing one silently falls back to the
# script's own default, which outranks `--env-file` interpolation.
START_SH_MUST_BE_NONEMPTY="COMPOSE_PROJECT_NAME PUBLIC_HOST WEB_DEV_HOST_PORT POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB"

ENV_KEYS="$(dotenv_keys "$ENV_FILE")"
ENV_EMPTY="$(dotenv_empty_keys "$ENV_FILE")"
ENV_DUPES="$(dotenv_keys "$ENV_FILE" | uniq -d)"
COMPOSE_ALL="$(compose_keys "$COMPOSE_FILE")"
COMPOSE_HARD="$(compose_hard_keys "$COMPOSE_FILE")"
SCRIPT_KEYS="$(start_sh_keys)"
EXAMPLE_KEYS="$(dotenv_keys "$EXAMPLE")"

in_list() { grep -qxF "$1" <<<"$2"; }

# ── 1. hard requirements from the compose file ────────────────────────────────
for key in $COMPOSE_HARD; do
  if ! in_list "$key" "$ENV_KEYS"; then
    problem "missing required key (compose \${${key}:?}): $key"
  elif in_list "$key" "$ENV_EMPTY"; then
    problem "empty but required (compose \${${key}:?}): $key"
  fi
done

# ── 2. keys this control plane consumes itself ────────────────────────────────
for key in $SCRIPT_KEYS; do
  if ! in_list "$key" "$ENV_KEYS"; then
    problem "missing key used by bin/start.sh: $key"
  elif in_list "$key" "$ENV_EMPTY" && in_list "$key" "$START_SH_MUST_BE_NONEMPTY"; then
    problem "empty key used by bin/start.sh: $key"
  fi
done

# ── 3. parity with the tracked template ───────────────────────────────────────
for key in $EXAMPLE_KEYS; do
  in_list "$key" "$ENV_KEYS" || problem "missing key documented in .env.example: $key"
done

# ── 4. duplicates / malformed keys (reported before alignment: most actionable) ─
if [[ -n "$ENV_DUPES" ]]; then
  while read -r key; do
    [[ -n "$key" ]] && problem "duplicate key in ${ENV_FILE##*/}: $key (last value wins)"
  done <<<"$ENV_DUPES"
fi
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  note "line ignored (malformed key): $line"
done < <(grep -nE '^[[:space:]]*[^#[:space:]=]+[[:space:]]*=' "$ENV_FILE" |
  grep -vE ':[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=' || true)

# ── 5. 1-to-1 line alignment with the template (last: noisiest, least urgent) ──
# Same key on the same line in all three files, so they can be compared side by side.
line_of_key() { grep -nE "^$1=" "$2" 2>/dev/null | head -1 | cut -d: -f1; }
for key in $EXAMPLE_KEYS; do
  in_list "$key" "$ENV_KEYS" || continue   # missing keys are already reported above
  ex_line="$(line_of_key "$key" "$EXAMPLE")"
  mf_line="$(line_of_key "$key" "$ENV_FILE")"
  if [[ -n "$ex_line" && -n "$mf_line" && "$ex_line" != "$mf_line" ]]; then
    problem "line ${ex_line} in .env.example but line ${mf_line} in ${ENV_FILE##*/}: $key"
  fi
done

# ── 4. duplicates / malformed keys ────────────────────────────────────────────
if [[ -n "$ENV_DUPES" ]]; then
  while read -r key; do
    [[ -n "$key" ]] && problem "duplicate key in ${ENV_FILE##*/}: $key (last value wins)"
  done <<<"$ENV_DUPES"
fi
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  note "line ignored (malformed key): $line"
done < <(grep -nE '^[[:space:]]*[^#[:space:]=]+[[:space:]]*=' "$ENV_FILE" |
  grep -vE ':[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=' || true)

# ── informational: documentation gaps + stack wiring ──────────────────────────
# "Documented" = active key OR commented-out option (`# KEY=…`) in the template.
DOCUMENTED_KEYS="$( { printf '%s\n' "$EXAMPLE_KEYS"; dotenv_commented_keys "$EXAMPLE"; } | sort -u | grep -v '^$' )"
undocumented="$(comm -23 <(printf '%s\n' "$COMPOSE_ALL") <(printf '%s\n' "$DOCUMENTED_KEYS") | grep -v '^$' || true)"
if [[ -n "$undocumented" ]]; then
  while read -r key; do
    [[ -n "$key" ]] && note "compose uses $key with a built-in default; not documented in .env.example (active or commented)"
  done <<<"$undocumented"
fi
service_block_has() { # file service key
  awk -v svc="$1:" -v key="$2" '
    /^  [A-Za-z_]+:/ { cur = $1 }
    cur == svc && index($0, key) { found = 1 }
    END { exit(found ? 0 : 1) }' "$3"
}
if [[ -d "$REPO_ROOT/web/src" ]]; then
  for var in $(grep -rhoE 'process\.env\.[A-Z0-9_]+' "$REPO_ROOT/web/src" 2>/dev/null |
    sed 's/process\.env\.//' | sort -u); do
    case "$var" in
      NODE_ENV|PORT|HOSTNAME|WATCHPACK_POLLING) continue ;;
    esac
    service_block_has web "$var" "$COMPOSE_FILE" ||
      note "web reads process.env.$var but docker-compose.$mode.yml never passes it to the web service"
  done
fi
if [[ -d "$REPO_ROOT/api/app" ]]; then
  for var in $( { grep -E '^    [a-z_]+: [a-zA-Z]' "$REPO_ROOT/api/app/config.py" 2>/dev/null |
                    sed 's/^    \([a-z_]*\):.*/\1/' | tr '[:lower:]' '[:upper:]'
                  grep -rhoE 'os\.environ(\.get)?\(?"[A-Z0-9_]+"' "$REPO_ROOT/api/app" 2>/dev/null |
                    grep -oE '"[A-Z0-9_]+"' | tr -d '"'; } | sort -u); do
    case "$var" in
      # Set by compose / the mounts by design, not by the env file.
      ATTACHMENTS_DIR|CORS_ALLOWED_ORIGINS|GITHUB_TOKEN_ENCRYPTION_KEY) continue ;;
    esac
    service_block_has api "$var" "$COMPOSE_FILE" ||
      note "API reads $var but docker-compose.$mode.yml never passes it to the api service"
  done
fi

# ── leftover bare `.env` (never read by this control plane) ───────────────────
if [[ -f "$REPO_ROOT/.env" ]]; then
  note "a bare .env exists in the repo root — it is NEVER read (modes use .env.dev / .env.prd); consider deleting it"
fi

# ── report ────────────────────────────────────────────────────────────────────
if [[ "$quiet" -eq 0 || "$fail" -ne 0 ]]; then
  printf 'env-check (%s): %s\n' "$mode" "$ENV_FILE"
  printf '  keys in file: %s | compose refs: %s (hard %s) | start.sh keys: %s | .env.example: %s\n' \
    "$(printf '%s\n' "$ENV_KEYS" | grep -c . || true)" \
    "$(printf '%s\n' "$COMPOSE_ALL" | grep -c . || true)" \
    "$(printf '%s\n' "$COMPOSE_HARD" | grep -c . || true)" \
    "$(printf '%s\n' "$SCRIPT_KEYS" | grep -c . || true)" \
    "$(printf '%s\n' "$EXAMPLE_KEYS" | grep -c . || true)"
fi

if [[ "$fail" -ne 0 ]]; then
  printf 'env-check (%s): FAIL — %s problem(s):\n' "$mode" "${#problems[@]}"
  shown=0
  for p in "${problems[@]}"; do
    [[ "$shown" -ge 40 ]] && { printf '  x … and %s more\n' "$(( ${#problems[@]} - shown ))"; break; }
    printf '  x %s\n' "$p"
    shown=$((shown + 1))
  done
fi
if [[ "${#notes[@]}" -gt 0 ]]; then
  printf 'env-check (%s): %s informational note(s):\n' "$mode" "${#notes[@]}"
  for n in "${notes[@]}"; do printf '  ! %s\n' "$n"; done
fi
if [[ "$fail" -ne 0 ]]; then
  printf 'env-check (%s): FAIL\n' "$mode"
  exit 1
fi
[[ "$quiet" -eq 0 ]] && printf 'env-check (%s): PASS\n' "$mode"
exit 0
