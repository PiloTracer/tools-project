#!/usr/bin/env bash
# Agent OS traceability-verify - machine-check that every FR in a master plan
# maps to at least one execution task (turns MASTER_PLAN_STANDARD Phase 4 gate
# "every FR1... maps to >=1 task M{N}-T{N}" into a test).
#
# Heuristic (documented, conservative to avoid false failures):
#   - An FR id is any token matching  FR-?<digits>  (e.g. FR-01, FR1, FR12).
#   - An FR is "covered" if it appears on a line that also contains a task id
#     matching  M<digits>-T<digits>  (e.g. the §19 roadmap / traceability matrix row).
#   - Orphan = declared FR never co-located with a task id -> FAIL.
#   - NFRs are reported for visibility but NOT failed (often cross-cutting, not 1:1 task).
#
# Scope: scans the latest {PLANS_ROOT}/full/*-full-plan.md and its *-full-plan-trace.md
# sibling, or explicit file path args. Exits 0 when no master plan exists (planning optional).
set -euo pipefail

failures=0
note() { echo "==> $*"; }
ok() { echo "    OK: $*"; }
die() { echo "    FAIL: $*" >&2; failures=$((failures + 1)); }

files=()
if [[ $# -gt 0 ]]; then
  files=("$@")
else
  plan="$(find .work/plans/full -name '*-full-plan.md' 2>/dev/null | sort | tail -1 || true)"
  if [[ -z "${plan}" ]]; then
    note "traceability-verify: no master plan found (planning optional) - nothing to check"
    exit 0
  fi
  files=("${plan}")
  trace="${plan%-full-plan.md}-full-plan-trace.md"
  [[ -f "${trace}" ]] && files+=("${trace}")
fi

note "Agent OS traceability-verify (${#files[@]} file(s))"
for f in "${files[@]}"; do
  [[ -f "${f}" ]] || { die "${f}: not found"; continue; }
done

result="$(awk '
  function norm(tok,   p,d){ if (tok ~ /^NFR/) p="NFR"; else p="FR"; d=tok; gsub(/[^0-9]/,"",d); return p (d+0) }
  {
    has_task = ($0 ~ /M[0-9]+-T[0-9]+/)
    s=$0
    while (match(s, /N?FR-?[0-9]+/)) {
      id=norm(substr(s,RSTART,RLENGTH))
      declared[id]=1
      if (has_task) linked[id]=1
      s=substr(s, RSTART+RLENGTH)
    }
  }
  END{
    fr=0; frlinked=0; nfr=0
    for (id in declared) {
      if (id ~ /^FR/) { fr++; if (id in linked) frlinked++; else print "ORPHAN:" id }
      else nfr++
    }
    print "SUMMARY: fr=" fr " fr_linked=" frlinked " nfr=" nfr
  }
' "${files[@]}")"

orphans=()
while IFS= read -r line; do
  case "${line}" in
    ORPHAN:*) orphans+=("${line#ORPHAN:}") ;;
    SUMMARY:*)
      # shellcheck disable=SC2086
      set -- ${line#SUMMARY: }
      fr="${1#fr=}"; fr_linked="${2#fr_linked=}"; nfr="${3#nfr=}"
      if [[ "${fr}" -eq 0 ]]; then
        die "no FR ids found in plan - is the plan using FR-NN ids per MASTER_PLAN_STANDARD?"
      elif [[ "${#orphans[@]}" -gt 0 ]]; then
        die "FR not mapped to any task M{N}-T{N}: ${orphans[*]}"
      else
        ok "all ${fr} FR ids map to a task (${fr_linked}/${fr}); ${nfr} NFR ids noted"
      fi
      ;;
  esac
done <<< "${result}"

if [[ "${failures}" -gt 0 ]]; then
  echo ""
  echo "traceability-verify: ${failures} gap(s)" >&2
  exit 1
fi

echo ""
echo "traceability-verify: FR coverage complete"
