#!/usr/bin/env bash
# Agent OS framework verification - run locally or in CI.
# Usage: bash scripts/framework-verify.sh   (from repo root)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

failures=0
note() { echo "==> $*"; }
ok() { echo "    OK: $*"; }
die() { echo "    FAIL: $*" >&2; failures=$((failures + 1)); }

note "Agent OS framework-verify (root=${REPO_ROOT})"

# --- 1. Self-hosted layout (this repo IS the .ai tree) ---
note "Self-hosted layout"
for f in START_HERE.md README.md skills/README.md skills/SKILL_DEPENDENCIES.md templates/bootstrap.sh; do
  if [[ -f "${REPO_ROOT}/${f}" ]]; then
    ok "${f}"
  else
    die "missing ${f}"
  fi
done

# Derived count + registry cross-check (no hardcoded magic number - prevents
# the silent drift that left smoke-consumer asserting a stale count).
skill_dirs=()
while IFS= read -r d; do skill_dirs+=("$(basename "${d}")"); done \
  < <(find skills -mindepth 1 -maxdepth 1 -type d ! -name '.*' | sort)
skill_count="${#skill_dirs[@]}"
[[ "${skill_count}" -ge 1 ]] || die "no skill directories found under skills/"
for n in "${skill_dirs[@]}"; do
  s="skills/${n}/skill.md"
  if [[ ! -f "${s}" ]]; then die "missing ${s}"; continue; fi
  grep -Eq "^name: ${n}[[:space:]]*$" "${s}" || die "${s}: frontmatter name does not match folder '${n}'"
  grep -q "${n}" skills/README.md || die "skill '${n}' not registered in skills/README.md"
  grep -q "${n}" skills/SKILL_DEPENDENCIES.md || die "skill '${n}' not in SKILL_DEPENDENCIES.md matrix"
done
ok "${skill_count} skills: skill.md + matching frontmatter + README + DEPS rows (derived)"

# Prose drift guard: any "<N> skill(s)" mention in landing docs must match the derived count.
prose_before="${failures}"
for doc in README.md START_HERE.md skills/README.md; do
  while IFS= read -r num; do
    [[ -z "${num}" ]] && continue
    if [[ "${num}" -ne "${skill_count}" ]]; then
      die "${doc} mentions '${num} skills' but ${skill_count} skill dirs exist (stale prose count)"
    fi
  done < <(sed 's/[*`]//g' "${doc}" | grep -oE '[0-9]+ skills?' | grep -oE '^[0-9]+' || true)
done
[[ "${failures}" -eq "${prose_before}" ]] && ok "skill-count prose matches derived count in landing docs"

# Intake contract guard: classification is agent-judged (no executable classifier),
# so we structurally assert the feature-spec intake table keeps all 4 classes + the
# force override - preventing the routing contract from being silently gutted.
intake_md="skills/feature-spec/skill.md"
intake_before="${failures}"
for cls in local cross-cutting brownfield underspecified; do
  grep -qE "\*\*${cls}\*\*" "${intake_md}" || die "feature-spec intake table missing class '${cls}'"
done
grep -qE 'force=<class>' "${intake_md}" || die "feature-spec intake missing 'force=<class>' override"
[[ "${failures}" -eq "${intake_before}" ]] && ok "feature-spec intake contract: 4 classes + force override present"

# --- 2. Consumer bootstrap smoke ---
note "Consumer bootstrap smoke"
SMOKE_ROOT="$(mktemp -d)"
trap 'rm -rf "${SMOKE_ROOT}"' EXIT

mkdir -p "${SMOKE_ROOT}/.ai"
rsync -a \
  --exclude='.git' \
  --exclude='.work' \
  --exclude='.github' \
  --exclude='.private' \
  --exclude='.credentials' \
  --exclude='scripts/smoke-consumer.sh' \
  "${REPO_ROOT}/" "${SMOKE_ROOT}/.ai/"

(
  cd "${SMOKE_ROOT}"
  git init -q
  bash .ai/templates/bootstrap.sh >/dev/null
  for f in .work/context/HANDOFF.md .work/plans/NEXT.md .cursorrules DOCS_TECH_STACK.md; do
    if [[ -f "${f}" ]]; then
      ok "consumer created ${f}"
    else
      die "consumer missing ${f}"
    fi
  done
  if [[ -d .ai/.work ]]; then
    die "bootstrap placed .work inside .ai/ (expected repo root)"
  fi
)

# --- 3. Removed vendor integration paths ---
note "No stale vendor integration paths"
if grep -rqE 'docs/integration/(hacienda|oidc|xades)' --include='*.md' . 2>/dev/null; then
  die "found reference to removed docs/integration vendor paths"
else
  ok "no hacienda/oidc/xades integration paths in markdown"
fi

# --- 4. Template placeholders present ---
note "REPLACE: token hygiene"
if grep -rq 'REPLACE:PROJECT_NAME' templates/cursorrules.template templates/work/ 2>/dev/null; then
  ok "REPLACE:PROJECT_NAME in templates"
else
  die "REPLACE:PROJECT_NAME missing from templates/"
fi
if grep -rq 'REPLACE:' standards/ 2>/dev/null; then
  ok "REPLACE: tokens in standards/"
else
  die "REPLACE: tokens missing from standards/"
fi

# --- 5. Markdown relative link check ---
note "Markdown relative links"
while IFS= read -r -d '' md; do
  dir="$(dirname "${md}")"
  while IFS= read -r link; do
    [[ -z "${link}" ]] && continue
    [[ "${link}" =~ ^https?:// ]] && continue
    [[ "${link}" =~ ^# ]] && continue
    target="${link%%#*}"
    target="${target%%\?*}"
    [[ -z "${target}" ]] && continue
    resolved="${dir}/${target}"
    if [[ ! -e "${resolved}" ]]; then
      die "broken link in ${md}: (${link}) -> ${resolved}"
    fi
  done < <(rg -o '\]\([^)]+\)' "${md}" 2>/dev/null | sed 's/^(//' | sed 's/)$//' | grep -v '^https\?://' | grep -v '^#' || true)
done < <(find . -name '*.md' ! -path './.git/*' ! -path './.work/*' -print0 2>/dev/null)

ok "markdown link scan complete"

# --- 6. readiness-verify self-test (exercise the probe-ledger linter) ---
note "readiness-verify self-test"
RV_ROOT="$(mktemp -d)"
RV_LEDGER="${RV_ROOT}/PROBE_LEDGER.md"

# Honest ledger: D1 confirmed/high with a cite; computed = claimed = 100%.
cat > "${RV_LEDGER}" <<'EOF'
**Coverage:** 100% (target 85%)

| Dim | Topic | Status | Conf | Evidence / source | Iter |
|-----|-------|--------|------|-------------------|------|
| D1 ★ | Intent | confirmed | high | doc01 §scope | 1 |
EOF
if bash "${REPO_ROOT}/scripts/readiness-verify.sh" "${RV_LEDGER}" >/dev/null 2>&1; then
  ok "readiness-verify accepts an honest ledger"
else
  die "readiness-verify rejected an honest ledger"
fi

# Dishonest ledger: confirmed/high with no evidence -> must exit non-zero.
cat > "${RV_LEDGER}" <<'EOF'
**Coverage:** 100% (target 85%)

| Dim | Topic | Status | Conf | Evidence / source | Iter |
|-----|-------|--------|------|-------------------|------|
| D1 ★ | Intent | confirmed | high | — | 1 |
EOF
if bash "${REPO_ROOT}/scripts/readiness-verify.sh" "${RV_LEDGER}" >/dev/null 2>&1; then
  die "readiness-verify accepted a dishonest ledger (confirmed/high, no cite)"
else
  ok "readiness-verify rejects an uncited confirmed/high dimension"
fi
rm -rf "${RV_ROOT}"

# --- 7. traceability-verify self-test (exercise the FR->task linter) ---
note "traceability-verify self-test"
TV_ROOT="$(mktemp -d)"
TV_PLAN="${TV_ROOT}/x-full-plan.md"
# Orphan: FR-02 never on a task line -> must fail.
printf '## reqs\n- FR-01 - FR-02\n| signup | FR-01 | M2-T1 |\n' > "${TV_PLAN}"
if bash "${REPO_ROOT}/scripts/traceability-verify.sh" "${TV_PLAN}" >/dev/null 2>&1; then
  die "traceability-verify missed an orphan FR (FR-02 not on any task line)"
else
  ok "traceability-verify catches an FR with no task"
fi
# Fully mapped -> must pass.
printf '## reqs\n| signup | FR-01 | M2-T1 |\n| reset | FR-02 | M2-T2 |\n' > "${TV_PLAN}"
if bash "${REPO_ROOT}/scripts/traceability-verify.sh" "${TV_PLAN}" >/dev/null 2>&1; then
  ok "traceability-verify passes a fully-mapped plan"
else
  die "traceability-verify rejected a fully-mapped plan"
fi
rm -rf "${TV_ROOT}"

if [[ "${failures}" -gt 0 ]]; then
  echo ""
  echo "framework-verify: ${failures} check(s) failed" >&2
  exit 1
fi

echo ""
echo "framework-verify: all checks passed"
