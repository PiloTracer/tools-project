#!/usr/bin/env bash
# Bootstrap UI Design OS: .work.ui/ + optional .cursorrules / DOCS_UI_STACK.md
# Usage: bash .ai.ui/templates/bootstrap.sh [merge-cursorrules|create-cursorrules]
set -euo pipefail

AI_UI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TPL="${AI_UI_ROOT}/templates/work.ui"
CURSORRULES_MODE="${1:-}"

if [[ -d "${AI_UI_ROOT}/.git" ]]; then
  REPO_ROOT="${AI_UI_ROOT}"
elif [[ -d "${AI_UI_ROOT}/../.git" ]] && [[ -d "${AI_UI_ROOT}/templates" ]]; then
  REPO_ROOT="$(cd "${AI_UI_ROOT}/.." && pwd)"
else
  REPO_ROOT="${AI_UI_ROOT}"
fi

WORK_UI="${REPO_ROOT}/.work.ui"

copy_if_missing() {
  local src="$1" dest="$2"
  if [[ -e "${dest}" ]]; then
    echo "skip (exists): ${dest}"
  else
    mkdir -p "$(dirname "${dest}")"
    cp "${src}" "${dest}"
    echo "created: ${dest}"
  fi
}

echo "UI Design OS bootstrap"
echo "  AI_UI_ROOT=${AI_UI_ROOT}"
echo "  REPO_ROOT=${REPO_ROOT}"
echo "  WORK_UI=${WORK_UI}"
echo ""

mkdir -p "${WORK_UI}"

copy_if_missing "${TPL}/README.md.template" "${WORK_UI}/README.md"
copy_if_missing "${TPL}/context/HANDOFF_UI.md.template" "${WORK_UI}/context/HANDOFF_UI.md"
copy_if_missing "${TPL}/plans/NEXT_UI.md.template" "${WORK_UI}/plans/NEXT_UI.md"
copy_if_missing "${TPL}/plans/ASSUMPTIONS.md.template" "${WORK_UI}/plans/ASSUMPTIONS.md"
copy_if_missing "${TPL}/plans/RISK_REGISTRY.md.template" "${WORK_UI}/plans/RISK_REGISTRY.md"
copy_if_missing "${TPL}/plans/UNKNOWNS.md.template" "${WORK_UI}/plans/UNKNOWNS.md"
copy_if_missing "${TPL}/screens/README.md.template" "${WORK_UI}/screens/README.md"
copy_if_missing "${TPL}/decisions/README.md.template" "${WORK_UI}/decisions/README.md"
copy_if_missing "${TPL}/prompts/README.md.template" "${WORK_UI}/prompts/README.md"
copy_if_missing "${TPL}/design-system/CATALOG.md.template" "${WORK_UI}/design-system/CATALOG.md"

for dir in foundation full; do
  mkdir -p "${WORK_UI}/plans/${dir}"
  if [[ -f "${TPL}/plans/${dir}/README.md.template" ]]; then
    copy_if_missing "${TPL}/plans/${dir}/README.md.template" "${WORK_UI}/plans/${dir}/README.md"
  fi
done

mkdir -p "${WORK_UI}/screens" "${WORK_UI}/design-system"

copy_if_missing "${AI_UI_ROOT}/templates/DOCS_UI_STACK.md.template" "${REPO_ROOT}/DOCS_UI_STACK.md"

echo ""
echo "--- .cursorrules ---"
if [[ -x "${AI_UI_ROOT}/scripts/cursorrules-ui.sh" ]]; then
  case "${CURSORRULES_MODE}" in
    merge-cursorrules)
      bash "${AI_UI_ROOT}/scripts/cursorrules-ui.sh" merge-block
      ;;
    create-cursorrules)
      if [[ -f "${REPO_ROOT}/.cursorrules" ]]; then
        echo "skip: .cursorrules exists — use merge-cursorrules or @ui-bootstrap status"
      else
        bash "${AI_UI_ROOT}/scripts/cursorrules-ui.sh" create-full
      fi
      ;;
    *)
      bash "${AI_UI_ROOT}/scripts/cursorrules-ui.sh" status
      echo "To install rules: bash .ai.ui/templates/bootstrap.sh create-cursorrules"
      echo "  or (with Agent OS .cursorrules): bash .ai.ui/templates/bootstrap.sh merge-cursorrules"
      echo "  or: @ui-bootstrap init merge-cursorrules"
      ;;
  esac
else
  echo "warn: scripts/cursorrules-ui.sh not executable"
fi

HANDOFF_MAIN="${REPO_ROOT}/.work/context/HANDOFF.md"
if [[ -f "${HANDOFF_MAIN}" ]] && ! grep -q 'UI layer' "${HANDOFF_MAIN}" 2>/dev/null; then
  echo ""
  echo "OPTIONAL: add ### UI layer to ${HANDOFF_MAIN} → .work.ui/context/HANDOFF_UI.md"
fi

echo ""
echo "Next: @ui-design-foundation greenfield · fill REPLACE:UI_* in .cursorrules"
echo "Docs: ${AI_UI_ROOT}/docs/adoption/FROM_AGENT_OS.md"
