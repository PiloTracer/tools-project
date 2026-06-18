#!/usr/bin/env bash
# Agent OS readiness-verify - mechanically enforce PROBE_LEDGER honesty rules.
#
# Validates each probe ledger (default: all .work/**/PROBE_LEDGER.md under cwd)
# against the rules in .ai/skills/probe-protocol.md:
#   1. Honesty: a dimension marked confirmed/high MUST cite evidence (no empty / dash / TBD).
#   2. Coverage math: the header "Coverage: NN%" must match the value recomputed from the
#      table within tolerance ( Coverage = Σ weight×conf / Σ weight ; high=1 med=.5 low=0 ;
#      gate-blocking ★ weight=2 else 1 ).
#   3. Readiness: no gate-blocking (★) dimension may be `unknown` while the header claims
#      coverage >= target.
#
# Usage:
#   bash readiness-verify.sh                 # scan .work/ for PROBE_LEDGER.md
#   bash readiness-verify.sh path/to/PROBE_LEDGER.md [more...]
#
# Exit 0 = all ledgers honest (or none found); exit 1 = at least one violation.
set -euo pipefail

TOL=2          # allowed |claimed - computed| coverage percentage points

failures=0
note() { echo "==> $*"; }
ok()   { echo "    OK: $*"; }
die()  { echo "    FAIL: $*" >&2; failures=$((failures + 1)); }

# Collect ledgers: explicit args, else discover under .work/
ledgers=()
if [[ $# -gt 0 ]]; then
  ledgers=("$@")
else
  while IFS= read -r -d '' f; do ledgers+=("$f"); done \
    < <(find .work -name 'PROBE_LEDGER.md' -print0 2>/dev/null || true)
fi

if [[ ${#ledgers[@]} -eq 0 ]]; then
  note "readiness-verify: no PROBE_LEDGER.md found (probe is optional) - nothing to check"
  exit 0
fi

note "Agent OS readiness-verify (${#ledgers[@]} ledger(s))"

for ledger in "${ledgers[@]}"; do
  if [[ ! -f "${ledger}" ]]; then
    die "${ledger}: file not found"
    continue
  fi

  # awk emits one report line per violation prefixed VIOLATION:, plus a SUMMARY line.
  result="$(awk '
    function trim(s){ gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
    function confval(c){ if(c=="high")return 1.0; if(c=="med")return 0.5; return 0.0 }
    BEGIN{ FS="|"; num=0; den=0; rows=0; blocking_unknown=0; claimed=-1; target=85 }
    # Header coverage claim: **Coverage:** NN% (target NN%)
    /[Cc]overage:/ && claimed<0 {
      line=$0
      if (match(line, /[Cc]overage:[^0-9]*[0-9]+%/)) {
        s=substr(line, RSTART, RLENGTH); gsub(/[^0-9]/, "", s); claimed=s+0
      }
      if (match(line, /target[^0-9]*[0-9]+/)) {
        t=substr(line, RSTART, RLENGTH); gsub(/[^0-9]/, "", t); if(t!="") target=t+0
      }
    }
    # Data rows: 2nd cell starts with a dimension id (D1, M-D3, ...)
    {
      dim=trim($2)
      if (dim !~ /^(M-)?D[0-9]+/) next
      rows++
      status=trim($4); conf=trim($5); ev=trim($6)
      gsub(/`/, "", status); gsub(/`/, "", conf)
      weight=(dim ~ /★/)?2:1
      num += weight*confval(conf); den += weight

      # Rule 1: honesty - confirmed/high needs a real cite
      if (status=="confirmed" || conf=="high") {
        if (ev=="" || ev=="-" || ev=="—" || toupper(ev)=="TBD" || ev=="n/a") {
          print "VIOLATION: dimension " dim " is " status "/" conf " but cites no evidence (\"" ev "\")"
        }
      }
      # Rule 3 input: blocking dimension still unknown
      if (weight==2 && status=="unknown") blocking_unknown++
    }
    END{
      computed=(den>0)?(num/den*100):0
      printf "SUMMARY: claimed=%d computed=%.0f target=%d rows=%d blocking_unknown=%d\n", claimed, computed, target, rows, blocking_unknown
    }
  ' "${ledger}")"

  ledger_fail=0
  while IFS= read -r line; do
    case "${line}" in
      VIOLATION:*) die "${ledger}: ${line#VIOLATION: }"; ledger_fail=1 ;;
      SUMMARY:*)
        # shellcheck disable=SC2086
        set -- ${line#SUMMARY: }
        claimed="${1#claimed=}"; computed="${2#computed=}"; target="${3#target=}"
        rows="${4#rows=}"; blocking_unknown="${5#blocking_unknown=}"

        if [[ "${rows}" -eq 0 ]]; then
          die "${ledger}: no dimension rows parsed (is the Coverage table filled?)"; ledger_fail=1
        fi
        # Rule 2: coverage math
        if [[ "${claimed}" -ge 0 ]]; then
          diff=$(( claimed > computed ? claimed - computed : computed - claimed ))
          if [[ "${diff}" -gt "${TOL}" ]]; then
            die "${ledger}: header Coverage ${claimed}% disagrees with table-computed ${computed}% (tol ${TOL})"; ledger_fail=1
          fi
        fi
        # Rule 3: readiness vs blocking unknowns
        if [[ "${claimed}" -ge "${target}" && "${blocking_unknown}" -gt 0 ]]; then
          die "${ledger}: claims coverage ${claimed}% >= target ${target}% but ${blocking_unknown} gate-blocking (★) dimension(s) still 'unknown'"; ledger_fail=1
        fi
        ;;
    esac
  done <<< "${result}"

  [[ "${ledger_fail}" -eq 0 ]] && ok "${ledger}: honest (coverage math + evidence + readiness consistent)"
done

if [[ "${failures}" -gt 0 ]]; then
  echo ""
  echo "readiness-verify: ${failures} violation(s)" >&2
  exit 1
fi

echo ""
echo "readiness-verify: all ledgers honest"
