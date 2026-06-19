#!/usr/bin/env bash
# Verify UI Design OS framework structure (run from .ai.ui root or repo with .ai.ui/)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAIL=0

check() {
  if [[ -e "${ROOT}/$1" ]]; then
    echo "ok: $1"
  else
    echo "MISSING: $1"
    FAIL=1
  fi
}

echo "UI Design OS framework-verify"
echo "ROOT=${ROOT}"
echo ""

for p in \
  README.md START_HERE.md COHABITATION.md APPROACH.md \
  .work.ui/README.md .work.ui/context/HANDOFF_UI.md .work.ui/plans/NEXT_UI.md \
  skills/README.md skills/SKILL_DEPENDENCIES.md \
  concepts/README.md \
  templates/bootstrap.sh templates/cursorrules.ui.template templates/cursorrules.ui.snippet.template \
  templates/DOCS_UI_STACK.md.template scripts/cursorrules-ui.sh \
  scripts/token-lint.sh scripts/bootstrap-test.sh \
  docs/adoption/FROM_AGENT_OS.md \
  style-stacks/README.md examples/INDEX.md resources/control-platforms.md \
  standards/20260523-SURFACE-AND-CONTROL-CRAFT.md \
  standards/20260523-UI-PATTERNS.md \
  standards/20260523-SCREEN_SPEC_STANDARD.md \
  standards/20260523-DESIGN_TOKENS_STANDARD.md \
  standards/20260523-COMPONENT_STANDARD.md \
  standards/20260523-ACCESSIBILITY_STANDARD.md \
  standards/20260523-UI-CONVENTIONS.md \
  standards/20260523-FRONTEND_DIRECTORY_MAP.md \
  examples/dashboards/manifest.md examples/mobile-controls/manifest.md \
  examples/mobile/manifest.md examples/websites/manifest.md examples/websites-tecnology/manifest.md; do
  check "$p"
done

# Derived skill count + registration cross-check (no hardcoded list - prevents drift).
SKILL_COUNT=0
while IFS= read -r d; do
  id="$(basename "$d")"
  SKILL_COUNT=$((SKILL_COUNT + 1))
  check "skills/${id}/skill.md"
  if ! grep -qE "^\| ${id} " "${ROOT}/skills/README.md"; then
    echo "UNREGISTERED: skills/${id} not in skills/README.md Registered skills table"
    FAIL=1
  fi
done < <(find "${ROOT}/skills" -mindepth 1 -maxdepth 1 -type d ! -name '.*' | sort)
echo "ok: ${SKILL_COUNT} skills (derived) registered in skills/README.md"

# No Agent OS skill name collisions under .ai.ui/skills
FORBIDDEN="plan-foundation plan-master code-implementation session-control process-router concept-run project-bootstrap"
for name in $FORBIDDEN; do
  if [[ -d "${ROOT}/skills/${name}" ]]; then
    echo "COLLISION: skills/${name} must not exist in .ai.ui (use ui-* prefix)"
    FAIL=1
  fi
done

# UIS concepts present
for id in visual-hierarchy responsive-layout motion-design color-contrast interaction-patterns ai-visual-quality surface-control-craft; do
  check "concepts/${id}/prompt.md"
done

# S0 before S1 in onboarding templates
for f in README.md templates/work.ui/plans/NEXT_UI.md.template .work.ui/plans/NEXT_UI.md; do
  if [[ -f "${ROOT}/${f}" ]] && grep -q 'plan - S1' "${ROOT}/${f}" && ! grep -q 'plan - S0' "${ROOT}/${f}"; then
    echo "WARN: ${f} mentions S1 but not S0 (craft tier refined path)"
  fi
done

# Prose drift guard: skill-count mentions in landing docs must match derived count.
for doc in README.md START_HERE.md skills/README.md; do
  while IFS= read -r num; do
    [[ -z "$num" ]] && continue
    if [[ "$num" -ne "$SKILL_COUNT" ]]; then
      echo "PROSE DRIFT: ${doc} mentions '${num} skills' but ${SKILL_COUNT} skill dirs exist"
      FAIL=1
    fi
  done < <(sed 's/[*`]//g' "${ROOT}/${doc}" | grep -oiE '[0-9]+ (ui-? )?skills?|skills? \([0-9]+\)' | grep -oE '[0-9]+' || true)
done

# Probe engine present (referenced by both probe modes).
check "skills/probe-protocol.md"

# Intake contract guard: ui-screen-spec intake table must keep all 4 classes + force
# override (classification is agent-judged, so this is a structural contract guard).
INTAKE_MD="${ROOT}/skills/ui-screen-spec/skill.md"
intake_ok=1
for cls in local cross-cutting brownfield underspecified; do
  grep -qE "\*\*${cls}\*\*" "${INTAKE_MD}" || { echo "INTAKE: ui-screen-spec missing class '${cls}'"; FAIL=1; intake_ok=0; }
done
grep -qE 'force=<class>' "${INTAKE_MD}" || { echo "INTAKE: ui-screen-spec missing force=<class> override"; FAIL=1; intake_ok=0; }
[[ $intake_ok -eq 1 ]] && echo "ok: ui-screen-spec intake contract (4 classes + force override)"

# Self-tests: the new verifiers must not silently rot (cf. honesty rules).
tmpd="$(mktemp -d)"
trap 'rm -rf "${tmpd}"' EXIT

cat > "${tmpd}/honest.md" <<'EOF'
**Coverage:** 100% (target 85%)
| Dim | Topic | Status | Conf | Evidence / source | Iter |
|-----|-------|--------|------|-------------------|------|
| D1 ★ | intent | confirmed | high | doc 01 §intent | 1 |
| D2 | tokens | confirmed | high | doc 02 | 1 |
EOF
cat > "${tmpd}/uncited.md" <<'EOF'
**Coverage:** 100% (target 85%)
| Dim | Topic | Status | Conf | Evidence / source | Iter |
|-----|-------|--------|------|-------------------|------|
| D1 ★ | intent | confirmed | high | — | 1 |
EOF
cat > "${tmpd}/sm-ok.md" <<'EOF'
## Screens
| Slug | Route | Priority | Domain SPEC link | SPEC status |
|------|-------|----------|------------------|-------------|
| home | `/` | P0 | - | Draft |
## Milestones (UI)
| Milestone | Screens | Notes |
|-----------|---------|-------|
| S1 | home | shell |
EOF
cat > "${tmpd}/sm-orphan.md" <<'EOF'
## Screens
| Slug | Route | Priority | Domain SPEC link | SPEC status |
|------|-------|----------|------------------|-------------|
| home | `/` | P0 | - | Draft |
| settings | `/settings` | P1 | - | Draft |
## Milestones (UI)
| Milestone | Screens | Notes |
|-----------|---------|-------|
| S1 | home | shell |
EOF

selftest() { # desc expected_exit script args...
  local desc="$1" exp="$2"; shift 2
  if bash "$@" >/dev/null 2>&1; then got=0; else got=1; fi
  if [[ "$got" -eq "$exp" ]]; then
    echo "ok: selftest ${desc}"
  else
    echo "SELFTEST FAIL: ${desc} (expected exit ${exp}, got ${got})"; FAIL=1
  fi
}
selftest "readiness-verify accepts honest"   0 "${ROOT}/scripts/readiness-verify.sh"   "${tmpd}/honest.md"
selftest "readiness-verify rejects uncited"  1 "${ROOT}/scripts/readiness-verify.sh"   "${tmpd}/uncited.md"
selftest "traceability-verify accepts scheduled" 0 "${ROOT}/scripts/traceability-verify.sh" "${tmpd}/sm-ok.md"
selftest "traceability-verify rejects orphan"    1 "${ROOT}/scripts/traceability-verify.sh" "${tmpd}/sm-orphan.md"

# token-lint self-tests: the design-token gate must reject raw hex in component
# source and accept token usage (cf. DESIGN_TOKENS_STANDARD - no magic hex).
printf 'const c = "var(--color-accent)";\n' > "${tmpd}/tl-clean.tsx"
printf 'const c = "#2f6df6";\n' > "${tmpd}/tl-dirty.tsx"
selftest "token-lint accepts token usage" 0 "${ROOT}/scripts/token-lint.sh" "${tmpd}/tl-clean.tsx"
selftest "token-lint rejects raw hex"     1 "${ROOT}/scripts/token-lint.sh" "${tmpd}/tl-dirty.tsx"

# traceability SPEC-backing + rogue-SPEC self-tests (need a .work.ui/plans + screens
# layout so the screens dir is derivable from the map path).
mkdir -p "${tmpd}/.work.ui/plans/foundation" "${tmpd}/.work.ui/screens/home"
cat > "${tmpd}/.work.ui/plans/foundation/sm-approved.md" <<'EOF'
## Screens
| Slug | Route | Priority | Domain SPEC link | SPEC status |
|------|-------|----------|------------------|-------------|
| home | `/` | P0 | - | Approved |
## Milestones (UI)
| Milestone | Screens | Notes |
|-----------|---------|-------|
| S1 | home | shell |
EOF
SM_APPROVED="${tmpd}/.work.ui/plans/foundation/sm-approved.md"
selftest "traceability rejects approved-without-SPEC" 1 "${ROOT}/scripts/traceability-verify.sh" "${SM_APPROVED}"
echo "# spec" > "${tmpd}/.work.ui/screens/home/20260530-SCREEN-SPEC.md"
selftest "traceability accepts approved-with-SPEC"    0 "${ROOT}/scripts/traceability-verify.sh" "${SM_APPROVED}"
mkdir -p "${tmpd}/.work.ui/screens/rogue"; echo "# x" > "${tmpd}/.work.ui/screens/rogue/20260530-SCREEN-SPEC.md"
selftest "traceability rejects rogue SPEC dir"        1 "${ROOT}/scripts/traceability-verify.sh" "${SM_APPROVED}"

# Adopter first-run integration: bootstrap.sh must produce a usable .work.ui/.
# Only when ROOT is the git top-level (the test exports tracked files); skipped
# when .ai.ui/ is nested in an adopter repo.
if git -C "${ROOT}" rev-parse --show-toplevel >/dev/null 2>&1 \
   && [[ "$(git -C "${ROOT}" rev-parse --show-toplevel)" == "${ROOT}" ]]; then
  if bash "${ROOT}/scripts/bootstrap-test.sh" >/dev/null 2>&1; then
    echo "ok: bootstrap-test (adopter first-run produces usable .work.ui/)"
  else
    echo "BOOTSTRAP: scripts/bootstrap-test.sh failed - adopter first-run is broken"; FAIL=1
  fi
fi

# Markdown local-link scan: relative links in .md files must resolve. Skips
# external (http/mailto), anchors (#...), placeholders ({ < REPLACE:), and Agent
# OS cross-refs (.ai/ .work/ are sibling trees, not part of this repo).
link_breaks=0
while IFS= read -r md; do
  d="$(dirname "${md}")"
  while IFS= read -r tgt; do
    [[ -z "${tgt}" ]] && continue
    case "${tgt}" in
      http://*|https://*|mailto:*|\#*) continue ;;
      *REPLACE:*|*"{"*|*"<"*) continue ;;
      .ai/*|*/.ai/*|.work/*|*/.work/*) continue ;;
    esac
    path="${tgt%% *}"; path="${path%%#*}"
    [[ -z "${path}" ]] && continue
    if [[ "${path}" = /* ]]; then resolved="${path}"; else resolved="${d}/${path}"; fi
    if [[ ! -e "${resolved}" ]]; then
      echo "BROKEN LINK: ${md#"${ROOT}"/} → ${tgt}"
      FAIL=1; link_breaks=$((link_breaks + 1))
    fi
  done < <(grep -oE '\]\([^)]+\)' "${md}" | sed -E 's/^\]\(//; s/\)$//')
done < <(find "${ROOT}" -name '*.md' -not -path '*/.git/*' | sort)
[[ "${link_breaks}" -eq 0 ]] && echo "ok: markdown local-link scan (no broken relative links)"

# Lean invariant + count self-report. Example PNGs are gitignored (manifests are
# the agent source of truth), so this repo must track 0 binary images; an
# accidental commit is caught here instead of silently bloating the tree. The
# tracked-file count is printed so the "lean" claim in CHANGELOG/HANDOFF stays
# honest. No-op unless ROOT is the git top-level (skips when .ai.ui/ is nested
# inside an adopter repo, where image tracking is the app's concern).
if git -C "${ROOT}" rev-parse --show-toplevel >/dev/null 2>&1 \
   && [[ "$(git -C "${ROOT}" rev-parse --show-toplevel)" == "${ROOT}" ]]; then
  tracked_total="$(git -C "${ROOT}" ls-files | wc -l | tr -d ' ')"
  tracked_imgs="$(git -C "${ROOT}" ls-files | grep -ciE '\.(png|jpe?g|gif|webp|svg)$' || true)"
  if [[ "${tracked_imgs}" -ne 0 ]]; then
    echo "LEAN: ${tracked_imgs} tracked image(s) — example PNGs must stay gitignored (manifests are source of truth)"
    FAIL=1
  else
    echo "ok: lean (${tracked_total} tracked files, 0 tracked images)"
  fi
fi

echo ""
if [[ $FAIL -eq 0 ]]; then
  echo "framework-verify: PASS"
else
  echo "framework-verify: FAIL"
  exit 1
fi
