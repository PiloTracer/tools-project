#!/usr/bin/env bash
# setup-target.sh — Bootstrap .ai.ui into a target project
#
# Alternative to templates/bootstrap.sh for multi-project workspaces.
# While bootstrap.sh creates .work.ui/ scaffolding in the current repo,
# setup-target.sh copies the full .ai.ui/ framework into an external target
# project and scaffolds .work.ui/ there — useful for monorepos or when
# developing multiple UIs against one framework checkout.
#
# Usage: bash scripts/setup-target.sh <target-dir> <profile>
#   profile: ecards | dashboard
#
# Idempotent: skips existing .work.ui/ files; re-copies .ai.ui on re-run.
set -euo pipefail

TARGET="$(cd "$1" && pwd)"
PROFILE="${2}"
AI_UI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TPL="${AI_UI_ROOT}/templates/work.ui"

if [[ ! -d "$TARGET" ]]; then
  echo "ERROR: target dir does not exist: $TARGET" >&2
  exit 1
fi

echo "=== Setting up .ai.ui → ${TARGET} (profile: ${PROFILE}) ==="

# ── 1. Copy .ai.ui into target ──────────────────────────────────────
if [[ -d "${TARGET}/.ai.ui" ]] && [[ ! -L "${TARGET}/.ai.ui" ]]; then
  echo "  exists: .ai.ui (directory — skipping copy)"
elif [[ -L "${TARGET}/.ai.ui" ]]; then
  echo "  exists: .ai.ui (symlink — removing and re-copying)"
  rm "${TARGET}/.ai.ui"
  cp -r "$AI_UI_ROOT" "${TARGET}/.ai.ui"
  echo "  copied: ${AI_UI_ROOT} → ${TARGET}/.ai.ui"
else
  cp -r "$AI_UI_ROOT" "${TARGET}/.ai.ui"
  echo "  copied: ${AI_UI_ROOT} → ${TARGET}/.ai.ui"
fi

# ── 2. Create .work.ui/ scaffolding ─────────────────────────────────
WORK_UI="${TARGET}/.work.ui"
mkdir -p "${WORK_UI}"/{context,plans/{foundation,full},screens,screens/example-slug,design-system,prompts,decisions}

copy_if_missing() {
  local src="$1" dest="$2"
  if [[ -e "$dest" ]]; then
    echo "  skip (exists): ${dest}"
  else
    mkdir -p "$(dirname "${dest}")"
    cp "$src" "$dest"
    echo "  created: ${dest}"
  fi
}

copy_if_missing "${TPL}/README.md.template"                    "${WORK_UI}/README.md"
copy_if_missing "${TPL}/context/HANDOFF_UI.md.template"        "${WORK_UI}/context/HANDOFF_UI.md"
copy_if_missing "${TPL}/plans/NEXT_UI.md.template"             "${WORK_UI}/plans/NEXT_UI.md"
copy_if_missing "${TPL}/plans/ASSUMPTIONS.md.template"         "${WORK_UI}/plans/ASSUMPTIONS.md"
copy_if_missing "${TPL}/plans/RISK_REGISTRY.md.template"       "${WORK_UI}/plans/RISK_REGISTRY.md"
copy_if_missing "${TPL}/plans/UNKNOWNS.md.template"            "${WORK_UI}/plans/UNKNOWNS.md"
copy_if_missing "${TPL}/screens/README.md.template"            "${WORK_UI}/screens/README.md"
copy_if_missing "${TPL}/decisions/README.md.template"          "${WORK_UI}/decisions/README.md"
copy_if_missing "${TPL}/prompts/README.md.template"            "${WORK_UI}/prompts/README.md"
copy_if_missing "${TPL}/design-system/CATALOG.md.template"     "${WORK_UI}/design-system/CATALOG.md"

for dir in foundation full; do
  if [[ -f "${TPL}/plans/${dir}/README.md.template" ]]; then
    copy_if_missing "${TPL}/plans/${dir}/README.md.template" "${WORK_UI}/plans/${dir}/README.md"
  fi
done

# Copy example screen spec template
copy_if_missing "${TPL}/screens/example-slug/YYYYMMDD-SCREEN-SPEC.md.template" \
                "${WORK_UI}/screens/example-slug/YYYYMMDD-SCREEN-SPEC.md"

echo "  .work.ui/ scaffolding complete"

# ── 3. Backup existing .cursorrules ──────────────────────────────────
if [[ -f "${TARGET}/.cursorrules" ]]; then
  cp "${TARGET}/.cursorrules" "${TARGET}/.cursorrules.agent-os.bak"
  echo "  backup: .cursorrules → .cursorrules.agent-os.bak"
fi

echo ""
echo "=== Setup scaffold done ==="
echo ""
echo "Next steps (manual / via chat):"
echo "  1. Fill token values in ${TARGET}/DOCS_UI_STACK.md"
echo "  2. Write merged .cursorrules (agent-os + UI block)"
echo "  3. @ui-design-foundation greenfield"
echo "  4. @ui-design-foundation certify screen-spec-ready"
