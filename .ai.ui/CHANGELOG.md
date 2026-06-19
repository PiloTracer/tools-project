# Changelog

## [Unreleased]

### Added

- **`scripts/token-lint.sh` — machine-enforced design-token contract.** Fails when component source contains raw hex/color literals instead of semantic tokens (`var(--…)`), the deterministic backstop behind `DESIGN_TOKENS_STANDARD` and the "no generic AI chrome" promise: an agent that hardcodes `#3b82f6` is caught here, not graded "looks good" by the same agent in a prose audit. Token files are exempt (`--tokens`); single lines opt out with a `token-lint-ignore` comment. No-op without paths (`$UI_LINT_PATHS` / args). Wired into `@ui-visual-verify` milestone checks; self-tested in `framework-verify`.
- **`scripts/bootstrap-test.sh` — adopter first-run integration test.** Exports the working tree into a throwaway sibling repo, runs `bootstrap.sh create-cursorrules`, and asserts `.work.ui/` + `.cursorrules` + `DOCS_UI_STACK.md` exist and the Intake queue / UI rules propagated. Converts the previously *manual* adopter-install spot-check into an automated gate (run by `framework-verify` and as its own CI step), so a refactor can't silently break the one action every new user performs first.
- **Demo worked examples** — `.work.ui/plans/foundation/20260529-04-screen-map.md` (2 screens, all scheduled) and `.work.ui/plans/foundation/PROBE_LEDGER.md` so `readiness-verify` + `traceability-verify` now run on **real in-repo data** (previously exercised only `/tmp` self-test fixtures), and so a new user sees a filled screen map + ledger.
- **Complete demo foundation** — `.work.ui/` now ships foundation docs 01 (vision), 02 (tokens), 03 (pattern inventory) and `design-system/tokens.css` (light+dark, surface/inset/elevated) for a *Demo SaaS dashboard*, so the demo satisfies the `screen-spec-ready` certify gate end-to-end. Probe ledger advanced to 100% (D4 tokens confirmed); HANDOFF readiness flips `ui-foundation-complete` + `screen-spec-ready` to yes (demo).
- **Admin dashboard archetype split** — `APPROACH.md` splits admin-dashboard into *operational* (real-time, monitoring, activity feeds) and *analytical* (charts, trends, reporting, drill-down) subtypes with separate playbooks; analytical path requires chart library selection in foundation doc 03, chart tokens in doc 02, and UIS-09 at milestone verify.
- **UIS-08 — Intuitive UX** (`concepts/intuitive-ux/`) — discoverability, feedback, error forgiveness, cognitive load check for **all screens** before ship; required at `@ui-component-build complete`.
- **UIS-09 — Data visualization quality** (`concepts/data-visualization-quality/`) — chart integrity, colorblind safety, responsive readability, chart junk audit for **analytical dashboards**; required at milestone verify when archetype = analytical.
- **Chart tokens** in `DESIGN_TOKENS_STANDARD` §5 — categorical palette (colorblind-safe), semantic palette (positive/negative/neutral), axis/grid, tooltip surface, sequential/diverging scales; chart tokens are **separate** from UI surface tokens; dark theme defined independently.
- **Screen SPEC §14 Data visualization** in `SCREEN_SPEC_STANDARD` — chart types, responsive per-chart sizing at breakpoints, chart tokens binding, loading/empty/error/animation states per chart, accessibility (data table fallback, `aria-label`, keyboard nav, color+pattern encoding).
- **Expanded dashboard patterns** in `UI-PATTERNS.md` — operational dashboards (auto-refresh, activity feed, alert highlighting), analytical (date range in URL, cross-filter, drill-down, chart+data table pair), reporting & export (report builder, saved reports, CSV/PDF/PNG export).
- **4 new dashboard examples** D9–D12 in `examples/dashboards/manifest.md` — analytical dashboard, bento chart grid, report builder, KPI wall (text-only, no PNGs; full row schema with extractedRules and primitives).
- **Chart & data-viz library resources** in `resources/control-platforms.md` — Recharts, Nivo, Vega-Lite, Chart.js, Tremor, MUI X Charts with selection rules and shadcn/charts accelerator.
- **`.quick/` quick-reference cheat sheets** — 8 one-page copy-paste workflow references (greenfield start, analytical dashboard, bootstrap existing, deploy to project, screen spec workflow, UI iteration build, pre-ship verify, concept checks) linked from `START_HERE.md` FAQ.
- **`@deploy-files` skill** (`skills/deploy-files/`) — deploy `.ai.ui/` into a target project via clean file copy: enumerates files through `git ls-files --cached --others --exclude-standard` so **anything `.gitignore` excludes is never copied** (enforced by construction); strips `.github/`, `.gitignore`, `.gitattributes`, `.cursorrules`, and deploy scripts. Idempotent, no `--delete`.
- **`@deploy-repo` skill** (`skills/deploy-repo/`) — full git-based deploy of `.ai.ui/` via `clone` (git clone from origin remote with full history) or `archive` (git archive, includes `.github/`/`.cursorrules`, no `.git/`).
- **`scripts/deploy-files.sh`** — shell backend for `@deploy-files`; `git ls-files --cached --others --exclude-standard` file enumeration, `rsync -a --files-from` without `--delete`.
- **`scripts/deploy-repo.sh`** — shell backend for `@deploy-repo`; `git clone` and `git archive` modes.
- **`scripts/setup-target.sh`** — alternative bootstrap script for target projects with profile support (`ecards`, `dashboard`); copies `.ai.ui/` + scaffolds `.work.ui/` + backs up existing `.cursorrules`.

### Changed

- **`concepts/README.md`** — UIS-01…07 → UIS-01…09 in index and trigger table; adds UIS-08 (all screens) and UIS-09 (analytical dashboards) trigger rows.
- **`skills/ui-concept-run/skill.md`** — UIS-01…07 → UIS-01…09; hard rules add UIS-08 (all screens before complete) and UIS-09 (analytical dashboards).
- **`skills/README.md`** — registers `deploy-files` and `deploy-repo` (14 skills); ui-concept-run description updated to UIS-01…09.
- **`skills/SKILL_DEPENDENCIES.md`** — adds `deploy-files`/`deploy-repo` to dependency matrix, redirect cheat sheet, and command vocabulary; adds UIS-08 and UIS-09 gates on `@ui-component-build complete`.
- **`START_HERE.md`** — verify section, per-task obligations, forgetfulness checklist, and FAQ updated for UIS-08/09, analytical dashboard path, and `.quick/` reference.
- **`examples/INDEX.md`** — dashboard count 9→13; playbook references UIS-09.
- **`templates/work.ui/screens/example-slug/YYYYMMDD-SCREEN-SPEC.md.template`** — §12 includes UIS-08/09 rows; new §14 Data visualization section with chart types, responsive, tokens, states, and accessibility tables.
- **`templates/work.ui/context/HANDOFF_UI.md.template`** — chart library in repository state; data viz conditional read.
- **`@ui-plan-verify`** documents the adopter-repo path (`.ai.ui/scripts/…`) for the verifier commands.
- **`scripts/framework-verify.sh`** now **enforces the lean invariant** — fails on any tracked binary image (example PNGs must stay gitignored; manifests are the source of truth) and self-reports the tracked-file count. Runs only when `.ai.ui/` is the git top-level, so it is a no-op when nested in an adopter repo. This converted a manually-asserted "0 tracked images / N files" claim (which had drifted 119→125) into a checked figure. Also gained 5 new self-tests (token-lint accept/reject; traceability accepts approved-with-SPEC, rejects approved-without-SPEC and rogue SPEC dirs) and now runs `bootstrap-test`.
- **`scripts/traceability-verify.sh`** extended from screen→milestone scheduling into the full **screen↔SPEC↔milestone chain**: an Approved screen with no SPEC file under `screens/<slug>/` fails (claimed-Approved without an artifact is dishonest, like an uncited probe dimension), and a `screens/<slug>/` directory with no row in the screen map fails (ungoverned UI). SPEC-backing/rogue checks run only when the screens dir exists; scheduling still always runs.

### Verified

- **Lean:** 127 tracked files, 0 tracked images (example PNGs, `tmp/`, `credentials/` are gitignored). The 0-tracked-images invariant is now **enforced** by `framework-verify.sh`, which also self-reports the live tracked-file count — so this figure is checked at every run rather than hand-maintained.
- **Usability:** adopter install simulated from a clean `git archive` — `bootstrap.sh` resolves the parent repo, creates `.work.ui/` + `.cursorrules` + `DOCS_UI_STACK.md`, and the seeded `## Intake queue` propagates.

## [0.5.0] - 2026-05-29

### Added

- **`probe` mode** for `@ui-design-foundation` (foundation understanding → `screen-spec-ready`) and `@ui-component-build` (roadmap completeness → `ui-implementation-ready`) — adaptive, gap-driven interrogation that scores coverage across fixed dimensions, asks ≤5 targeted questions per pass, records answers into foundation docs / screen map / registries, and loops to a confidence target (85%).
- **`skills/probe-protocol.md`** — shared engine (loop, Coverage Score, ledger, ease-of-use rules) referenced by both probe modes; skills supply only a coverage profile. Not a skill folder.
- **`@ui-plan-verify`** — read-only UI plan audit skill (`audit` / `probe-coverage` / `traceability`): runs the verifiers, reports probe coverage + orphan screens, and routes each gap to a command (skill-level analogue of `plan-verify`). Brings the registry to **12 skills**.
- **`.github/workflows/framework-verify.yml`** — CI runs `framework-verify` + `readiness-verify` + `traceability-verify` on push, PR, and tag (was manual-only).
- **`docs/guides/probe-and-intake.md`** — operator guide for the probe loop and the free-text intake front door.
- **`skills/ui-screen-spec/reference.md`** — intake/create invocation examples (good vs wrong prompts, slug derivation).
- **`## Intake queue`** section seeded in the NEXT_UI template + demo so the free-text front door is discoverable before first use.
- **Command-vocabulary table** in `skills/SKILL_DEPENDENCIES.md` (canonical verb list); `probe - status` / `probe - until ready` sub-modes added to the foundation + build Modes tables.
- **`templates/work.ui/plans/foundation/PROBE_LEDGER.md.template`** — resumable, auditable probe state.
- **`@ui-screen-spec intake - <free sentence>`** — free-text front door: classifies a UI request (`local` / `cross-cutting` / `brownfield` / `underspecified`), routes to the right executor, and records it to `NEXT_UI § Intake queue`. `; force=<class>` overrides. Also: free-text `create` now derives a slug from a sentence.
- **`scripts/readiness-verify.sh`** — machine-checkable honesty linter for probe ledgers (evidence backing claims, coverage math, gate-blocking unknowns). Exits 0 when no ledger.
- **`scripts/traceability-verify.sh`** — checks every screen in the screen map is scheduled into a milestone (UI analogue of FR→task). Exits 0 when no screen map.
- **`scripts/release.sh <version>`** — release preflight; tag cannot ship while verification is red or CHANGELOG/ tree are not ready.

### Changed

- **`scripts/framework-verify.sh`** — now **derives** the skill count (no hardcoded list), cross-checks each skill is registered in `skills/README.md`, guards skill-count prose drift in landing docs, asserts the `ui-screen-spec` intake contract, **self-tests** `readiness-verify` + `traceability-verify`, and **scans markdown for broken relative links** (skips external / placeholder / cross-framework refs).
- **`@ui-component-build complete`** now runs `@ui-plan-verify audit` (readiness + traceability) at the UI milestone boundary, so an orphan screen or dishonest ledger blocks close rather than surfacing late at `@session-control close`. Documented in `COHABITATION.md`.
- **`ui-process-router`** — fixed bucket drift: `skill.md` no longer keeps a stale inline bucket list (was 10, missing the 16 in `reference.md`); it now points to `reference.md` as the single source and adds a no-match fallback to `START_HERE` §1. Added `probe`, `screen-request`, and `plan-verify` buckets.
- **`START_HERE.md`** surfaces `probe`, `intake`, and `@ui-plan-verify`; **`SKILL_DEPENDENCIES.md`** adds probe/intake/plan-verify matrix + redirect rows; **`CONTRIBUTING.md`** documents `release.sh`; **`DESIGN_TOKENS_STANDARD`** adds dark/scoped theme token-completeness requirements.

## [0.4.3] - 2026-05-23

### Changed (audit / lean)

- Onboarding aligned: S0 primitives before S1 in README, NEXT_UI template, demo `.work.ui`
- `framework-verify.sh`: all 11 skills, all 8 standards, all 5 example manifests; S0/S1 drift warning
- `examples/INDEX.md`: honest partial rating for mobile; PNG gitignore documented
- Trimmed README skills table + extending bullets; fixed START_HERE §8 numbering
- `FROM_AGENT_OS.md` UIS-07; workflows guide stub trimmed

## [0.4.2] - 2026-05-23

### Added

- [`resources/control-platforms.md`](resources/control-platforms.md) — MIT/Apache OSS behavior platforms; one-page adoption guide
- CATALOG **Behavior source** column in template; router + SURFACE related link

## [0.4.1] - 2026-05-23

### Changed (bloat control)

- Trimmed duplicate playbook prose from SURFACE-AND-CONTROL-CRAFT, START_HERE, README, skills — canonical path: `examples/INDEX.md`
- Added **Implementation priority** to SURFACE-AND-CONTROL-CRAFT §4 (pixels before paperwork)
- Merged duplicate craft rows in `ui-process-router/reference.md`
- `framework-verify.sh` now checks SURFACE standard, UIS-07, mobile-controls manifest

## [0.4.0] - 2026-05-23

### Added

- [`standards/20260523-SURFACE-AND-CONTROL-CRAFT.md`](standards/20260523-SURFACE-AND-CONTROL-CRAFT.md) — surfaces, controls, native-vs-custom, verify checklist
- **UIS-07** — [`concepts/surface-control-craft/`](concepts/surface-control-craft/README.md) positive craft review
- Example manifests — full row schema (surfaces, controls, extractedRules, primitives) for mobile-controls, dashboards, websites, websites-tecnology
- [`examples/INDEX.md`](examples/INDEX.md) — example → foundation → catalog → SPEC → verify playbook
- Screen SPEC §13 binding shape (exampleIds, extractedRules, regionMap)
- Primitive-first milestone ordering in `ui-component-build`; craft gates in `ui-screen-spec`, `ui-visual-verify`, `ui-design-foundation`

### Changed

- UI-PATTERNS § forms + mobile-native — craft pointers
- Foundation + screen SPEC templates — craft tier, surface tokens, example id column
- START_HERE, APPROACH, README, concepts registry — UIS-01…07

## [0.3.0] - 2026-05-23

### Added

- [`APPROACH.md`](APPROACH.md) — archetypes, skill chains (replaces bloated decision-engine tree)
- [`standards/20260523-UI-PATTERNS.md`](standards/20260523-UI-PATTERNS.md) — forms, nav, data, mobile checklists
- [`style-stacks/`](style-stacks/README.md) — tailwind, css-modules, vanilla-css, styled-components
- [`examples/INDEX.md`](examples/INDEX.md) + per-folder `manifest.md` (annotated samples)
- Skills: `ui-project-approach`, `ui-style-stack`
- README rewrite — 60-second human + agent path

### Rejected (by design)

- 12 single-purpose skills from feedback (`ui-landing-page`, `ui-data-display`, …) — see APPROACH §6

## [0.2.0] - 2026-05-23

### Added

- Full `templates/cursorrules.ui.template` (Core Principles 1–7, UI completion gate, skills, Docker, verification)
- `scripts/cursorrules-ui.sh` — create-full / merge-block / status
- `@ui-bootstrap` cursorrules modes: `init merge-cursorrules`, `create-cursorrules`, brownfield gates
- `docs/adoption/FROM_AGENT_OS.md` — what to adapt from Agent OS vs avoid
- `templates/DOCS_UI_STACK.md.template`
- Substantive framework `.cursorrules` and richer `work.ui` HANDOFF/NEXT templates

## [0.1.0] - 2026-05-23

### Added

- Demo **`.work.ui/`** skeleton at framework repo root (mirrors Agent OS `.work/`)
- Pointer READMEs under `.ai.ui/plans/`, `screens/`, `context/`, `decisions/`, `design-system/`
- Expanded `templates/work.ui/` (foundation 01–04, registries, screen SPEC example)
- **Work tree path resolution** in `skills/SKILL_DEPENDENCIES.md` — all skill outputs at `<repo-root>/.work.ui/`
- Initial UI Design OS framework structure
- Nine `ui-*` skills with dependency graph
- Six UIS concept prompts (visual hierarchy through AI visual quality)
- Six binding standard templates (conventions, screen SPEC, components, tokens, a11y, directory map)
- `.work.ui/` bootstrap templates and `cursorrules.ui.snippet` for coexistence with Agent OS
- [`COHABITATION.md`](COHABITATION.md) boundary contract with `.ai/`
