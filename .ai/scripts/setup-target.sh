#!/usr/bin/env bash
# setup-target.sh — Bootstrap .ai (Agent OS) into a target project repo
#
# Usage: bash scripts/setup-target.sh <target-dir>
#   target-dir: absolute path to the application repo (e.g. /mnt/data/Projects/EPIC/tools-ecards)
#
# Idempotent: skips existing .work/ files; re-copies .ai/ directory.
# Backs up existing .cursorrules before overwriting.
set -euo pipefail

TARGET="$(cd "$1" && pwd)"
AI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TPL="${AI_ROOT}/templates/work"

if [[ ! -d "$TARGET" ]]; then
  echo "ERROR: target dir does not exist: $TARGET" >&2
  exit 1
fi

echo "=== Setting up .ai (Agent OS) → ${TARGET} ==="

# ── 1. Backup existing .ai/ then force-copy fresh .ai/ tree ──────────
if [[ -d "${TARGET}/.ai" ]]; then
  mv "${TARGET}/.ai" "${TARGET}/.ai.bak"
  echo "  backup: .ai/ → .ai.bak/"
fi
cp -r "$AI_ROOT" "${TARGET}/.ai"
echo "  copied: ${AI_ROOT} → ${TARGET}/.ai"

# ── 2. Create .work/ scaffolding ──────────────────────────────────────
WORK="${TARGET}/.work"
mkdir -p "${WORK}/context" "${WORK}/decisions" "${WORK}/features" "${WORK}/prompts" "${WORK}/analysis" "${WORK}/scripts"
mkdir -p "${WORK}/plans/foundation" "${WORK}/plans/full" "${WORK}/plans/operations" "${WORK}/plans/proposals" "${WORK}/plans/archives"

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

copy_if_missing "${TPL}/README.md.template"              "${WORK}/README.md"
copy_if_missing "${TPL}/context/HANDOFF.md.template"     "${WORK}/context/HANDOFF.md"
copy_if_missing "${TPL}/plans/NEXT.md.template"          "${WORK}/plans/NEXT.md"
copy_if_missing "${TPL}/plans/ASSUMPTIONS.md.template"   "${WORK}/plans/ASSUMPTIONS.md"
copy_if_missing "${TPL}/plans/RISK_REGISTRY.md.template" "${WORK}/plans/RISK_REGISTRY.md"
copy_if_missing "${TPL}/plans/UNKNOWNS.md.template"      "${WORK}/plans/UNKNOWNS.md"
copy_if_missing "${TPL}/decisions/README.md.template"    "${WORK}/decisions/README.md"
copy_if_missing "${TPL}/prompts/README.md.template"      "${WORK}/prompts/README.md"
copy_if_missing "${TPL}/features/README.md.template"     "${WORK}/features/README.md"

# keep-plan-dirs: ensure empty plan subdirs exist even if templates didn't produce files
for dir in foundation full operations proposals archives; do
  mkdir -p "${WORK}/plans/${dir}"
  touch "${WORK}/plans/${dir}/.gitkeep"
done

echo "  .work/ scaffolding complete"

# ── 3. Overwrite cursorrules (template) + backup existing ────────────
if [[ -f "${TARGET}/.cursorrules" ]]; then
  cp "${TARGET}/.cursorrules" "${TARGET}/.cursorrules.agent-os.bak"
  echo "  backup: .cursorrules → .cursorrules.agent-os.bak"
fi
cp "${AI_ROOT}/templates/cursorrules.template" "${TARGET}/.cursorrules"
echo "  overwritten: .cursorrules (from template — fill REPLACE: tokens)"

# ── 4. Overwrite standards ────────────────────────────────────────────
# Copy contents into existing .ai/standards/ (full tree copy already created the dir)
cp -r "${AI_ROOT}/standards/." "${TARGET}/.ai/standards/"
echo "  overwritten: .ai/standards/"

echo ""
echo "=== Setup scaffold done ==="
echo ""
echo "Next steps (for each target repo):"
echo "  1. Edit .cursorrules — fill every REPLACE: token"
echo "  2. Edit .ai/standards/ — customize CONVENTIONS, FEATURE_STANDARD, etc."
echo "  3. Run @plan-foundation greenfield (or minimal: @session-control start)"
echo ""
echo "Lite path (existing repo, fast start):"
echo "  docs/adoption/minimal-adoption.md"
echo ""
echo "Full pipeline (new product):"
echo "  @plan-foundation greenfield → certify plan-master-ready"
echo "  @plan-master greenfield → status (implementation-ready)"
