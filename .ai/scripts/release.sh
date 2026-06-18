#!/usr/bin/env bash
# Agent OS release preflight - a tag cannot ship while verification is red.
#
# Usage: bash scripts/release.sh <version>        # e.g. 0.3.1   (no leading 'v')
#
# Runs every verifier, asserts CHANGELOG has a dated section for <version> and a
# clean tree, and ONLY THEN creates annotated tag v<version>. It never pushes -
# review, then `git push origin main --follow-tags` yourself.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

if [[ $# -lt 1 ]]; then
  echo "usage: bash scripts/release.sh <version>   (e.g. 0.3.1)" >&2
  exit 2
fi
version="${1#v}"
tag="v${version}"

fail=0
step() { echo "==> $*"; }
bad() { echo "    BLOCK: $*" >&2; fail=1; }

step "Release preflight for ${tag}"

# 1. All verifiers must pass.
for v in framework-verify smoke-consumer readiness-verify traceability-verify gate-verify; do
  if bash "scripts/${v}.sh" >/dev/null 2>&1; then
    echo "    OK: ${v}"
  else
    bad "${v} failed - run 'bash scripts/${v}.sh' and fix before releasing"
  fi
done

# 2. CHANGELOG must document this version (not still under [Unreleased]).
if grep -qE "^## \[${version}\]" CHANGELOG.md; then
  echo "    OK: CHANGELOG has [${version}] section"
else
  bad "CHANGELOG.md has no '## [${version}]' section - finalize [Unreleased] first"
fi

# 3. Working tree clean.
if [[ -z "$(git status --porcelain)" ]]; then
  echo "    OK: working tree clean"
else
  bad "working tree dirty - commit the release first"
fi

# 4. Tag must not already exist.
if git rev-parse -q --verify "refs/tags/${tag}" >/dev/null; then
  bad "tag ${tag} already exists"
fi

if [[ "${fail}" -ne 0 ]]; then
  echo ""
  echo "release: BLOCKED - not tagging ${tag}" >&2
  exit 1
fi

git tag -a "${tag}" -m "release ${tag}"
echo ""
echo "release: created ${tag}. Review, then push:"
echo "    git push origin main --follow-tags"
