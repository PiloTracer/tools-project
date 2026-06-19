#!/usr/bin/env bash
# UI Design OS bootstrap-test - prove the one action every adopter performs first
# actually works: copy .ai.ui/ beside an app and run bootstrap.sh. Until now this
# was only *manually* spot-checked; a refactor could silently break first-run setup
# and the first to find out would be a frustrated new user. This automates it.
#
# It exports the current working-tree (tracked files) into a throwaway sibling
# repo, runs bootstrap.sh create-cursorrules, and asserts the expected artifacts
# exist and key content propagated. Leaves the real repo untouched.
#
# Usage: bash scripts/bootstrap-test.sh
# Exit 0 = bootstrap produces a usable .work.ui/ + .cursorrules + DOCS_UI_STACK.md.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
note() { echo "==> $*"; }

if ! git -C "${ROOT}" rev-parse --show-toplevel >/dev/null 2>&1; then
  note "bootstrap-test: not a git repo (cannot export tracked files) - skipping"
  exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

note "bootstrap-test: simulating an adopter repo at ${tmp}"
mkdir -p "${tmp}/.ai.ui"

# Copy working-tree content of tracked files into the fake adopter's .ai.ui/.
( cd "${ROOT}" && git ls-files -z | tar --null -T - -cf - ) | tar -x -C "${tmp}/.ai.ui"

# Make the parent a git repo so bootstrap resolves REPO_ROOT to the adopter root
# (the nested-in-app-repo layout), not to .ai.ui itself.
( cd "${tmp}" && git init -q && git -c user.email=t@t -c user.name=t add -A -q 2>/dev/null || true )

bash "${tmp}/.ai.ui/templates/bootstrap.sh" create-cursorrules >/dev/null

fail=0
check() { if [[ -e "${tmp}/$1" ]]; then echo "    OK: $1"; else echo "    MISSING: $1"; fail=1; fi; }

check ".work.ui/README.md"
check ".work.ui/context/HANDOFF_UI.md"
check ".work.ui/plans/NEXT_UI.md"
check ".work.ui/plans/ASSUMPTIONS.md"
check ".work.ui/plans/RISK_REGISTRY.md"
check ".work.ui/plans/UNKNOWNS.md"
check ".work.ui/design-system/CATALOG.md"
check ".cursorrules"
check "DOCS_UI_STACK.md"

if grep -q "Intake queue" "${tmp}/.work.ui/plans/NEXT_UI.md" 2>/dev/null; then
  echo "    OK: Intake queue propagated into NEXT_UI"
else
  echo "    MISSING: Intake queue not in bootstrapped NEXT_UI"; fail=1
fi

if grep -qE 'ui-component-build|UI Design OS' "${tmp}/.cursorrules" 2>/dev/null; then
  echo "    OK: .cursorrules carries UI rules"
else
  echo "    MISSING: UI rules absent from .cursorrules"; fail=1
fi

echo ""
if [[ "${fail}" -eq 0 ]]; then
  echo "bootstrap-test: PASS (adopter first-run produces a usable UI layer)"
else
  echo "bootstrap-test: FAIL" >&2
  exit 1
fi
