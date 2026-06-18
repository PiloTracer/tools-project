#!/usr/bin/env bash
# Consumer adoption smoke - bootstrap + artifact inventory.
# Usage: bash scripts/smoke-consumer.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SMOKE_ROOT="$(mktemp -d)"
trap 'rm -rf "${SMOKE_ROOT}"' EXIT

echo "Consumer smoke: ${SMOKE_ROOT}"

mkdir -p "${SMOKE_ROOT}/.ai"
rsync -a \
  --exclude='.git' \
  --exclude='.work' \
  --exclude='.github' \
  --exclude='.private' \
  --exclude='.credentials' \
  "${REPO_ROOT}/" "${SMOKE_ROOT}/.ai/"

cd "${SMOKE_ROOT}"
git init -q
bash .ai/templates/bootstrap.sh

echo ""
echo "Created artifacts:"
find .work .cursorrules DOCS_TECH_STACK.md -type f 2>/dev/null | sort

echo ""
echo "Skill registry:"
test -f .ai/skills/SKILL_DEPENDENCIES.md
# Derive expected from the source tree (no hardcoded count): the consumer copy
# must carry the same number of skills as the framework it was bootstrapped from.
expected_skills="$(find "${REPO_ROOT}/skills" -mindepth 1 -maxdepth 1 -type d ! -name '.*' | wc -l | tr -d ' ')"
actual_skills="$(find .ai/skills -mindepth 1 -maxdepth 1 -type d ! -name '.*' | wc -l | tr -d ' ')"
test "${actual_skills}" -eq "${expected_skills}"
echo "  ${actual_skills} skills carried into consumer (expected ${expected_skills})"

echo ""
echo "Next (manual / agent chat):"
echo "  1. Edit .cursorrules - replace every REPLACE: token"
echo "  2. @session-control start"
echo "  3. @plan-foundation greenfield  (full pipeline)"
echo "     OR see docs/adoption/minimal-adoption.md (lite path)"
echo ""
echo "smoke-consumer: PASS"
