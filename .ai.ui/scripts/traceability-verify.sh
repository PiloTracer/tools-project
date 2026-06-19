#!/usr/bin/env bash
# UI Design OS traceability-verify - machine-check the full UI chain so nothing
# falls through the cracks on a real (multi-screen) project. UI analogue of Agent
# OS FR->task traceability. For every screen-map doc (foundation doc 04) it asserts:
#
#   1. Scheduling  - every slug in "## Screens" appears in "## Milestones (UI)"
#                    Screens column (an unscheduled screen is an orphan).
#   2. SPEC backing - every screen whose "SPEC status" is Approved has an actual
#                    SPEC file under .work.ui/screens/<slug>/ (claimed-Approved with
#                    no artifact is dishonest, like an uncited probe dimension).
#   3. No rogue SPECs - every screens/<slug>/ directory maps to a row in the screen
#                    map (a built/specced screen nobody governed is ungoverned UI).
#
# Checks 2-3 run only when the screens/ directory exists (derived from the map path);
# scheduling always runs. This keeps the demo + /tmp self-tests deterministic.
#
# Usage:
#   bash traceability-verify.sh                 # scan .work.ui for screen-map docs
#   bash traceability-verify.sh path/to/04-screen-map.md [more...]
#
# Exit 0 = chain intact (or no screen map); exit 1 = orphan / unbacked / rogue.
set -euo pipefail

failures=0
note() { echo "==> $*"; }
ok()   { echo "    OK: $*"; }
die()  { echo "    FAIL: $*" >&2; failures=$((failures + 1)); }

files=()
if [[ $# -gt 0 ]]; then
  files=("$@")
else
  while IFS= read -r -d '' f; do files+=("$f"); done \
    < <(find .work.ui -name '*screen-map*.md' ! -name 'README*' -print0 2>/dev/null || true)
fi

if [[ ${#files[@]} -eq 0 ]]; then
  note "traceability-verify: no screen-map doc found - nothing to check"
  exit 0
fi

note "UI Design OS traceability-verify (${#files[@]} screen map(s))"

for f in "${files[@]}"; do
  if [[ ! -f "${f}" ]]; then die "${f}: not found"; continue; fi

  result="$(awk '
    function trim(s){ gsub(/^[ \t]+|[ \t]+$/, "", s); gsub(/`/, "", s); return s }
    BEGIN{ FS="|"; sec="" }
    /^##[ \t]+Screens/      { sec="screens"; next }
    /^##[ \t]+Milestones/   { sec="milestones"; next }
    /^##[ \t]/              { sec="other"; next }
    sec=="screens" && /^\|/ {
      slug=trim($2)
      if (slug=="" || slug=="Slug" || slug ~ /^-+$/) next
      declared[slug]=1
      st=trim($6)
      print "SCREEN:" slug ":" st
    }
    sec=="milestones" && /^\|/ {
      cell=trim($3)
      if (cell=="" || cell=="Screens" || cell ~ /^-+$/) next
      n=split(cell, arr, /[ ,]+/)
      for (i=1;i<=n;i++){ s=trim(arr[i]); if(s!="") scheduled[s]=1 }
    }
    END{
      total=0; orphans=0
      for (s in declared){ total++; if(!(s in scheduled)){ orphans++; print "ORPHAN:" s } }
      print "SUMMARY: screens=" total " orphans=" orphans
    }
  ' "${f}")"

  file_fail=0
  unset declared status_of 2>/dev/null || true
  declare -A declared=() status_of=()
  while IFS= read -r line; do
    case "${line}" in
      SCREEN:*)
        rest="${line#SCREEN:}"; slug="${rest%%:*}"; st="${rest#*:}"
        declared["${slug}"]=1; status_of["${slug}"]="${st}"
        ;;
      ORPHAN:*) die "${f}: screen '${line#ORPHAN:}' is not scheduled into any milestone (## Milestones)"; file_fail=1 ;;
      SUMMARY:*)
        # shellcheck disable=SC2086
        set -- ${line#SUMMARY: }
        screens="${1#screens=}"
        [[ "${file_fail}" -eq 0 ]] && ok "${f}: all ${screens} screen(s) scheduled into a milestone"
        ;;
    esac
  done <<< "${result}"

  # Checks 2-3: SPEC backing + rogue SPECs. Derive the screens/ dir from the map
  # path (.../.work.ui/plans/.../screen-map.md -> .../.work.ui/screens). Skip when
  # the path has no /plans/ segment (e.g. /tmp self-test fixtures that omit it) or
  # the screens/ dir is absent.
  screens_dir=""
  case "${f}" in */plans/*) screens_dir="${f%/plans/*}/screens" ;; esac
  if [[ -n "${screens_dir}" && -d "${screens_dir}" ]]; then
    # 2. Approved screens must have a SPEC file authored.
    for slug in "${!status_of[@]}"; do
      st="${status_of[$slug]}"
      shopt -s nullglob
      specs=("${screens_dir}/${slug}"/*SCREEN-SPEC*.md)
      shopt -u nullglob
      if [[ "${st,,}" == "approved" && ${#specs[@]} -eq 0 ]]; then
        die "${f}: screen '${slug}' is SPEC status '${st}' but has no SPEC file under screens/${slug}/"
        file_fail=1
      fi
    done
    # 3. Every screens/<slug>/ dir must be a declared screen.
    for d in "${screens_dir}"/*/; do
      [[ -d "${d}" ]] || continue
      sslug="$(basename "${d}")"
      case "${sslug}" in example-slug|README*) continue ;; esac
      if [[ -z "${declared[$sslug]:-}" ]]; then
        die "${f}: screens/${sslug}/ has a SPEC dir but no row in the screen map (ungoverned screen)"
        file_fail=1
      fi
    done
  fi
done

if [[ "${failures}" -gt 0 ]]; then
  echo ""
  echo "traceability-verify: ${failures} orphan screen(s)" >&2
  exit 1
fi

echo ""
echo "traceability-verify: every screen scheduled"
