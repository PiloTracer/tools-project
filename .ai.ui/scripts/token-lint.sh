#!/usr/bin/env bash
# UI Design OS token-lint - machine-enforce the design-token contract: component
# source must consume semantic tokens (var(--token), theme object), NEVER raw hex.
# This is the deterministic backstop behind DESIGN_TOKENS_STANDARD / COMPONENT_STANDARD
# and the "no generic AI chrome" promise: an agent that hardcodes #3b82f6 is caught
# here instead of being graded "looks good" by the same agent in a prose audit.
#
# Raw color literals are allowed ONLY in designated token files (--tokens), which is
# where the palette is legitimately defined. A single line may opt out with a
# trailing `token-lint-ignore` comment (use sparingly; document why).
#
# Usage:
#   bash token-lint.sh [--tokens FILE]... [PATH ...]
#     --tokens FILE   token/theme file exempt from the raw-hex rule (repeatable;
#                     also read from $UI_TOKENS_FILE)
#     PATH            file or directory of component source to scan (repeatable;
#                     also read from $UI_LINT_PATHS, space-separated)
#
# Exit 0 = no raw hex in component source (or nothing to scan); exit 1 = violation(s).
set -euo pipefail

note() { echo "==> $*"; }
ok()   { echo "    OK: $*"; }

tokens=()
paths=()

# token files from env
if [[ -n "${UI_TOKENS_FILE:-}" ]]; then
  for t in ${UI_TOKENS_FILE}; do tokens+=("$t"); done
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tokens) shift; [[ $# -gt 0 ]] && tokens+=("$1") ;;
    --tokens=*) tokens+=("${1#--tokens=}") ;;
    -h|--help) grep -E '^#( |$)' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) paths+=("$1") ;;
  esac
  shift
done

# scan paths from env
if [[ ${#paths[@]} -eq 0 && -n "${UI_LINT_PATHS:-}" ]]; then
  for p in ${UI_LINT_PATHS}; do paths+=("$p"); done
fi

if [[ ${#paths[@]} -eq 0 ]]; then
  note "token-lint: no component path given (set args or \$UI_LINT_PATHS) - nothing to check"
  exit 0
fi

# Normalize token-file set for O(1) membership (compare by realpath when possible).
declare -A is_token=()
for t in "${tokens[@]}"; do
  rp="$(realpath -m "$t" 2>/dev/null || echo "$t")"
  is_token["$rp"]=1
done

# Component-source extensions worth linting (skip lockfiles, md, json, etc.).
exts_re='\.(tsx?|jsx?|mjs|cjs|vue|svelte|css|scss|sass|less|styl)$'

# Collect candidate files: directories are walked, explicit files are honored as-is
# (so a single .tsx passed directly is linted regardless of extension).
candidates=()
for p in "${paths[@]}"; do
  if [[ -d "$p" ]]; then
    while IFS= read -r -d '' f; do candidates+=("$f"); done \
      < <(find "$p" -type f -regextype posix-extended -iregex ".*${exts_re}" \
            -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/dist/*' \
            -not -path '*/build/*' -print0 2>/dev/null || true)
  elif [[ -f "$p" ]]; then
    candidates+=("$p")
  fi
done

# Raw hex color literal: #RGB, #RGBA, #RRGGBB, #RRGGBBAA (bounded so SHAs / longer
# strings and #anchors do not match).
hex_re='#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})([^0-9a-fA-F]|$)'

violations=0
scanned=0
for f in "${candidates[@]}"; do
  rp="$(realpath -m "$f" 2>/dev/null || echo "$f")"
  [[ -n "${is_token[$rp]:-}" ]] && continue   # token files may define raw values
  scanned=$((scanned + 1))
  while IFS= read -r m; do
    [[ -z "$m" ]] && continue
    case "$m" in *token-lint-ignore*) continue ;; esac
    echo "    RAW HEX: ${f}:${m}"
    violations=$((violations + 1))
  done < <(grep -nE "$hex_re" "$f" 2>/dev/null || true)
done

if [[ "$violations" -gt 0 ]]; then
  echo ""
  echo "token-lint: ${violations} raw color literal(s) in component source - use semantic tokens (var(--…)) instead" >&2
  exit 1
fi

ok "token-lint: ${scanned} component file(s) scanned, 0 raw color literals"
echo ""
echo "token-lint: component source uses tokens only"
