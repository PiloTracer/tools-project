#!/usr/bin/env bash
# Install or merge UI Design OS rules into <repo-root>/.cursorrules
set -euo pipefail

AI_UI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FULL_TPL="${AI_UI_ROOT}/templates/cursorrules.ui.template"
SNIP_TPL="${AI_UI_ROOT}/templates/cursorrules.ui.snippet.template"

if [[ -d "${AI_UI_ROOT}/.git" ]] && [[ ! -d "${AI_UI_ROOT}/../.ai.ui" ]]; then
  REPO_ROOT="${AI_UI_ROOT}"
elif [[ -d "${AI_UI_ROOT}/../.git" ]]; then
  REPO_ROOT="$(cd "${AI_UI_ROOT}/.." && pwd)"
else
  REPO_ROOT="${AI_UI_ROOT}"
fi

RULES="${REPO_ROOT}/.cursorrules"
MODE="${1:-status}"

has_ui_block() {
  [[ -f "${RULES}" ]] && grep -q 'UI_DESIGN_OS_BEGIN' "${RULES}" 2>/dev/null
}

has_ui_standalone() {
  [[ -f "${RULES}" ]] && grep -qE 'ui-component-build|UI Design OS' "${RULES}" 2>/dev/null
}

count_ui_replace() {
  if [[ -f "${RULES}" ]]; then
    grep -c 'REPLACE:UI_' "${RULES}" 2>/dev/null || true
  else
    echo 0
  fi
}

case "${MODE}" in
  status)
    echo "cursorrules-ui status"
    echo "  REPO_ROOT=${REPO_ROOT}"
    echo "  RULES=${RULES}"
    if [[ ! -f "${RULES}" ]]; then
      echo "  .cursorrules: missing"
      echo "  action: run create-full (or @ui-bootstrap init create-cursorrules)"
    else
      echo "  .cursorrules: present"
      if has_ui_block; then
        echo "  UI block: merged (UI_DESIGN_OS_BEGIN found)"
      elif has_ui_standalone; then
        echo "  UI block: standalone (full UI template)"
      else
        echo "  UI block: missing"
        echo "  action: run merge-block with user approval"
      fi
      echo "  REPLACE:UI_* count: $(count_ui_replace)"
    fi
  if [[ -d "${REPO_ROOT}/.ai" ]]; then
    echo "  Agent OS (.ai/): present — prefer merge-block over create-full if .cursorrules exists"
  fi
    ;;
  create-full)
    if [[ -f "${RULES}" ]]; then
      echo "refuse: ${RULES} already exists — use merge-block or overwrite with explicit user confirm-overwrite-cursorrules"
      exit 1
    fi
    cp "${FULL_TPL}" "${RULES}"
    echo "created: ${RULES} from cursorrules.ui.template"
    echo "next: replace REPLACE: tokens; run @ui-bootstrap status"
    ;;
  merge-block)
    if [[ ! -f "${RULES}" ]]; then
      echo "no .cursorrules — creating full UI template instead"
      cp "${FULL_TPL}" "${RULES}"
      echo "created: ${RULES}"
      exit 0
    fi
    if has_ui_block; then
      echo "skip: UI_DESIGN_OS_BEGIN already present"
      exit 0
    fi
    {
      echo ""
      cat "${SNIP_TPL}"
    } >> "${RULES}"
    echo "merged: UI block appended to ${RULES}"
    ;;
  *)
    echo "usage: $0 status|create-full|merge-block"
    exit 1
    ;;
esac
