#!/usr/bin/env bash
# Agent OS gate-verify - mechanically enforce the completion gate (.cursorrules
# Core Principle 7) on the iteration carrier. A task may only be marked done when
# it records gate evidence (test/lint/type result or an exit code) in its Notes.
#
# It parses the `### Tasks` table inside `## Current iteration` of a NEXT.md:
#   | ID | Description | Files | Status | Notes |
# A row whose ID looks like M{N}-T{N} and whose Status is done/complete MUST carry
# an evidence token in Notes (exit <code>, pass(ed), tests, lint, type, gate,
# green, ok, evidence, or a check mark). An empty / dash Notes cell is a violation
# - that is exactly the "claimed PASS without proof" failure the framework forbids.
#
# Usage:
#   bash gate-verify.sh                 # scan .work/ for NEXT.md
#   bash gate-verify.sh path/to/NEXT.md [more...]
#
# Exit 0 = every done task cites evidence (or no NEXT.md / no done tasks found);
# exit 1 = at least one done task lacks recorded gate evidence.
set -euo pipefail

failures=0
note() { echo "==> $*"; }
ok()   { echo "    OK: $*"; }
die()  { echo "    FAIL: $*" >&2; failures=$((failures + 1)); }

# Preflight: gate-verify only needs POSIX awk + find (kept portable on purpose).
command -v awk >/dev/null 2>&1 || { echo "FAIL: missing required tool: awk" >&2; exit 3; }

# Collect carriers: explicit args, else discover under .work/
carriers=()
if [[ $# -gt 0 ]]; then
  carriers=("$@")
else
  while IFS= read -r -d '' f; do carriers+=("$f"); done \
    < <(find .work -name 'NEXT.md' -print0 2>/dev/null || true)
fi

if [[ ${#carriers[@]} -eq 0 ]]; then
  note "gate-verify: no NEXT.md found - nothing to check"
  exit 0
fi

note "Agent OS gate-verify (${#carriers[@]} carrier(s))"

total_done=0
for carrier in "${carriers[@]}"; do
  if [[ ! -f "${carrier}" ]]; then
    die "${carrier}: file not found"
    continue
  fi

  # awk emits VIOLATION: lines per offending task and a SUMMARY: line with counts.
  result="$(awk '
    function trim(s){ gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
    BEGIN{ FS="|"; done=0; rows=0 }
    {
      id=trim($2); gsub(/`/, "", id)
      # Task rows: ID is M{N}-T{N} and the row is the full 5-column Tasks table
      # (| ID | Desc | Files | Status | Notes | -> NF==7 with empty edge fields).
      if (id !~ /^M[0-9]+-T[0-9]+/ || NF < 7) next
      rows++
      status=trim($5); gsub(/`/, "", status); status=tolower(status)
      notes=trim($6)
      if (status=="done" || status=="complete" || status=="✓" || status=="pass") {
        done++
        ev=tolower(notes)
        # Evidence = recorded proof a gate ran (matches .cursorrules § Completion gate).
        has_ev = (ev ~ /exit[ ]*[0-9]/) || (ev ~ /pass|passed|tests?|lint|type|gate|green|[ ]ok|^ok|evidence|✓|✔/)
        empty  = (notes=="" || notes=="-" || notes=="—" || tolower(notes)=="n/a" || tolower(notes)=="tbd")
        if (empty) {
          print "VIOLATION: task " id " is marked \"" status "\" with no Notes - completion gate needs recorded evidence (tests/lint/type exit codes)"
        } else if (!has_ev) {
          print "VIOLATION: task " id " is marked \"" status "\" but Notes record no gate evidence (\"" notes "\")"
        }
      }
    }
    END{ printf "SUMMARY: tasks=%d done=%d\n", rows, done }
  ' "${carrier}")"

  carrier_done=0
  carrier_fail=0
  while IFS= read -r line; do
    case "${line}" in
      VIOLATION:*) die "${carrier}: ${line#VIOLATION: }"; carrier_fail=1 ;;
      SUMMARY:*)
        # shellcheck disable=SC2086
        set -- ${line#SUMMARY: }
        carrier_done="${2#done=}"
        ;;
    esac
  done <<< "${result}"

  total_done=$(( total_done + carrier_done ))
  if [[ "${carrier_fail}" -eq 0 ]]; then
    if [[ "${carrier_done}" -eq 0 ]]; then
      ok "${carrier}: no done tasks to gate (nothing claimed complete)"
    else
      ok "${carrier}: ${carrier_done} done task(s), all cite gate evidence"
    fi
  fi
done

if [[ "${failures}" -gt 0 ]]; then
  echo ""
  echo "gate-verify: ${failures} task(s) marked done without recorded gate evidence" >&2
  exit 1
fi

echo ""
echo "gate-verify: completion gate satisfied (${total_done} done task(s) checked)"
