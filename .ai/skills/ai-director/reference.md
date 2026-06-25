# ai-director — orchestration reference

Full skill registry, dependency map, and routing tables for the `@ai-director` orchestrator.

---

## 1. Complete skill registry (all `.ai` skills)

All 16 registered skills + 2 deploy utilities. Source of truth: `skills/README.md`.

| `@` handle | Folder | Role | Modes | Writes? | Depends on |
|------------|--------|------|-------|---------|------------|
| `project-bootstrap` | `project-bootstrap/` | Scaffold `.work/`, `.cursorrules`, stack doc from templates | `init`, `status` | Yes (`.work/`, `.cursorrules`, `DOCS_TECH_STACK.md`) | `.ai/` present |
| `plan-foundation` | `plan-foundation/` | Foundation docs 01–04, ADRs, SPECs, registries; certifies plan-master-ready | `greenfield`, `continue`, `probe`, `probe - status`, `probe - until ready`, `status`, `certify plan-master-ready` | Yes (foundation docs, ADRs, PROBE_LEDGER, registries) | Recommended: `@project-bootstrap init` |
| `plan-master` | `plan-master/` | Master implementation plan with milestones; certifies implementation-ready | `greenfield`, `continue`, `probe`, `probe - status`, `revise`, `integrity`, `status`, `show` | Yes (`*-full-plan.md`, PROBE_LEDGER) | **Required:** plan-master-ready |
| `plan-verify` | `plan-verify/` | Plan audits: foundation, master, alignment, coverage, brownfield | `foundation`, `master`, `alignment`, `brownfield`, `status` | Read-only (report) | Target artifacts exist for mode |
| `plan-repair` | `plan-repair/` | Fix plan gaps; brownfield synthesis from repo evidence | `repair`, `foundation`, `master`, `brownfield`, `status` | Yes (plan docs) | Findings from `@plan-verify` or user goal |
| `session-control` | `session-control/` | Session bookends; updates HANDOFF + NEXT; optional git | `start`, `close`, `close commit`, `close commit push`, `commit`, `commit push`, `status` | Yes (`{HANDOFF}`, `{ITERATION_CARRIER}`, optional git) | Recommended: `@project-bootstrap init` |
| `code-implementation` | `code-implementation/` | Iteration execution from NEXT.md; per-task gates | `plan - M{N}`, `start`, `continue`, `continue - N`, `continue - until blocked`, `complete`, `status` | Yes (code, `{ITERATION_CARRIER}`, `{HANDOFF}`) | **Required:** Approved master plan or HANDOFF waiver |
| `code-verify` | `code-verify/` | Audits: milestone, uncommitted, last commit/push | `milestone`, `uncommitted`, `last`, `status` | Read-only (report) | **Required:** Active milestone (for milestone mode) |
| `code-repair` | `code-repair/` | Fix verifier/migration/SPEC findings; re-verify before pass | `repair - from <source>`, `repair - custom - …`, `status` | Yes (code) | Verifier report or custom brief |
| `feature-spec` | `feature-spec/` | Triage, author, review, or amend feature SPECs | `intake - <sentence>`, `create - <slug>`, `review - <path>`, `amend - <slug>`, `approve`, `status` | Yes (SPECs) | FEATURE_STANDARD |
| `concept-run` | `concept-run/` | Run MOD-01…06 architecture/NFR prompts | `list`, `status`, `run - MOD-0N` | Varies (attachments) | Trigger table in `concepts/README.md` |
| `db-migration` | `db-migration/` | Idempotent numbered SQL migration scripts | `init`, `create - <description>`, `run`, `verify`, `status` | Yes (SQL scripts) | **Required:** `db-migration init` (for create/run) |
| `dev-stack` | `dev-stack/` | Generate/update isolated Docker compose dev helper | `init`, `status` | Yes (`bin/start.sh`) | `docker-compose*.yml` present |
| `process-router` | `process-router/` | Read-only: "how do I…?" → right skill or guide | `- <question>`, `help` | Read-only | — |
| `deploy-files` | `deploy-files/` | Deploy `.ai` files to target project (clean rsync) | `copy - <path>`, `status` | Yes (target `.ai/`) | Source git repo |
| `deploy-repo` | `deploy-repo/` | Full git-based deploy (clone/archive) | `clone - <path>`, `archive - <path>`, `status` | Yes (target repo) | Source git remote (for clone) |

---

## 2. Gate / dependency matrix

| Gate state | Meaning | Certified by |
|------------|---------|--------------|
| *(scaffold)* | `.work/` skeleton exists | `@project-bootstrap init` |
| **foundation-complete** | All P0–P6 foundation gates done | `@plan-foundation status` |
| **plan-master-ready** | Blueprint solid enough for master roadmap | `@plan-foundation certify plan-master-ready` |
| **implementation-ready** | Master plan Approved | `@plan-master status` |

**Gate blocking rules:**

| Attempted skill/mode | Blocked unless | Route instead |
|----------------------|----------------|---------------|
| `@plan-foundation greenfield` | `.work/` exists (or bootstrap complete) | `@project-bootstrap init` |
| `@plan-foundation certify` | **foundation-complete** | `@plan-foundation greenfield` or `continue` |
| `@plan-master greenfield` | **plan-master-ready** | `@plan-foundation certify plan-master-ready` |
| `@plan-master probe` | **plan-master-ready** + draft plan | `@plan-master greenfield` or `continue` |
| `@code-implementation plan` | Approved `*-full-plan.md` or HANDOFF waiver | `@plan-master status` |
| `@code-implementation start` | Valid NEXT.md iteration block + **implementation-ready** or waiver | `@code-implementation plan - M{N}` |
| `@code-implementation complete` | `@code-verify milestone` pass | `@code-verify milestone` |
| `@db-migration create` | `db-migration init` already run | `@db-migration init` |
| `@feature-spec create` | FEATURE_STANDARD exists; SPEC folder not taken | `@feature-spec status` |

---

## 3. Skill chain templates by phase

| Phase | Chain |
|-------|-------|
| **Greenfield bootstrap** | `@project-bootstrap init` → `@plan-foundation greenfield` → `@plan-foundation certify` → `@plan-master greenfield` → `@plan-master status` |
| **Brownfield adoption** | `@plan-verify brownfield` → `@plan-repair brownfield` → `@plan-verify brownfield` → `@plan-foundation certify` → `@plan-master greenfield` or `continue` |
| **Daily session** | `@session-control start` → `@code-implementation status` → work → `@session-control close` |
| **Per milestone** | `@code-implementation plan - M{N}` → `@code-implementation start` → `@code-implementation continue` (loop) → `@code-verify milestone` → `@code-implementation complete` |
| **Feature intake to code** | `@feature-spec intake` → `@feature-spec create` → `@feature-spec review` → `@feature-spec approve` → plan → implement |
| **Schema change** | `@db-migration init` (once) → `@db-migration create - <desc>` → `@db-migration verify` |
| **Architecture review** | `@concept-run - MOD-01` through `MOD-06` as triggered |
| **Plan audit + repair** | `@plan-verify foundation` → `@plan-verify master` → findings → `@plan-repair repair - from <mode>` → re-verify |
| **Deploy framework** | `@deploy-files copy - <path>` or `@deploy-repo clone - <path>` → next steps in target |

---

## 4. Concept trigger table

From `concepts/README.md`. Run these as required during the build cycle:

| Trigger | Run | Required? |
|---------|-----|-----------|
| AI-assisted code session | `@concept-run - MOD-06` | **Required** (unless human-only) |
| Diff crosses >1 hard boundary | `@concept-run - MOD-01` | **Required** |
| Significant new Bounded Context | `@concept-run - MOD-02` | Recommended |
| Performance-sensitive change | `@concept-run - MOD-03` | Recommended |
| Ops/infra/cost change | `@concept-run - MOD-04` | Recommended |
| Security review | `@concept-run - MOD-05` | Recommended |
| Plan-foundation P6 | `@concept-run - MOD-06` | Required per P6 gate |

---

## 5. Verify gate checklist (pre-complete)

Before `@code-implementation complete`, ensure these all pass:

| Check | Command | Required for |
|-------|---------|-------------|
| Milestone audit | `@code-verify milestone` | All builds |
| Uncommitted check | `@code-verify uncommitted` | Dirty tree |
| Plan alignment | `@plan-verify alignment` | If plan exists |
| Architecture prompts | `@concept-run - MOD-06` | AI-assisted diffs |
| Boundary check | `@concept-run - MOD-01` | Cross-boundary diffs |
| Security review | `@concept-run - MOD-05` | If applicable |

---

## 6. Common user request routing table

| User says (paraphrased) | Classified bucket | Execute |
|------------------------|-------------------|---------|
| "Start a new project" | `bootstrap` | `@project-bootstrap init` → `@plan-foundation greenfield` |
| "Create foundation docs" | `foundation` | `@plan-foundation greenfield` |
| "I'm not sure about the requirements" | `foundation-probe` | `@plan-foundation probe` |
| "Certify the plan" | `foundation-certify` | `@plan-foundation certify plan-master-ready` |
| "Write the master implementation plan" | `master-plan` | Check plan-master-ready → `@plan-master greenfield` |
| "Is the plan complete?" | `master-probe` | `@plan-master probe` → `@plan-master integrity` |
| "Audit the plans" | `plan-verify` | `@plan-verify foundation` → `@plan-verify master` |
| "Fix planning gaps" | `plan-repair` | `@plan-repair repair - from <mode>` |
| "Start a session" | `session-control` | `@session-control start` |
| "Close the session" | `session-control` | `@session-control close` |
| "Where am I?" | `session-control` | `@session-control status` |
| "Build feature X" | `code-implementation` | `@code-implementation status` → plan → start |
| "Continue coding" | `code-implementation` | `@code-implementation continue` |
| "Complete the milestone" | `code-implementation` | `@code-verify milestone` → `@code-implementation complete` |
| "Check the code" | `code-verify` | `@code-verify uncommitted` |
| "Fix the failed checks" | `code-repair` | `@code-repair repair - from uncommitted` |
| "I have a feature idea" | `feature-spec` | `@feature-spec intake - <sentence>` |
| "Write a SPEC for X" | `feature-spec-create` | `@feature-spec create - <slug>` |
| "Run MOD-06" | `concept` | `@concept-run - MOD-06` |
| "Create a migration" | `db-migration` | `@db-migration init` (first) → `@db-migration create - <desc>` |
| "Set up Docker" | `dev-stack` | `@dev-stack init` |
| "How do I...?" | `process-router` | `@process-router - <question>` |
| "Deploy to /path/to/project" | `deploy` | `@deploy-files copy - /path/to/project` |
| "I need a UI" | `ui-work` | Route to `@ui-director` (`.ai.ui` framework) |
| "Business strategy work" | `biz-work` | Route to `@biz-director` (`.ai.biz` framework) |

---

## 7. State files (paths)

| Placeholder | Resolved path | Purpose |
|-------------|---------------|---------|
| `{WORK_ROOT}` | `.work/` | Project memory root |
| `{HANDOFF}` | `.work/context/HANDOFF.md` | Session state |
| `{ITERATION_CARRIER}` | `.work/plans/NEXT.md` | Active iteration + intake queue |
| `{PLANS_ROOT}` | `.work/plans/` | Plans, foundation docs, registries |
| `{FEATURE_SPEC_ROOT}` | `.work/features/` | Feature SPECs |
| `{DECISIONS_ROOT}` | `.work/decisions/` | Architecture Decision Records |
| `{MASTER_PLAN}` | `.work/plans/full/*-full-plan.md` | Full master plan |
| `{PROMPTS_ROOT}` | `.work/prompts/` | User scratch; questionnaires |
| `{UNKNOWNS}` | `.work/plans/UNKNOWNS.md` | Open unknowns registry |
| `{PROBE_LEDGER}` | `.work/plans/foundation/PROBE_LEDGER.md` | Probe state ledger |

---

## 8. Verifier scripts

| Script | Purpose | Called by |
|--------|---------|-----------|
| `.ai/scripts/readiness-verify.sh` | PROBE_LEDGER honesty check | `@session-control close`, audit |
| `.ai/scripts/traceability-verify.sh` | FR→task traceability check | `@plan-verify alignment` |

---

## 9. Cross-framework routing

When a user request spans multiple domains (e.g. "build a backend API and a UI for it"), the `ai-director` should:

1. Identify the primary domain (engineering)
2. Route the engineering parts through `.ai` skills
3. Route UI parts to `@ui-director` via `.ai.ui`
4. Route business parts to `@biz-director` via `.ai.biz`
5. Coordinate by updating all relevant HANDOFF files

For complex cross-framework orchestration, escalate to `@x-director`.

---

## 10. Notable non-skills (shared engines & patterns)

| Resource | Location | Purpose |
|----------|----------|---------|
| Probe protocol | `skills/probe-protocol.md` | Shared adaptive interrogation loop |
| Standards | `standards/*.md` | Binding engineering templates |
| Concepts | `concepts/*/` (MOD-01..06) | Architecture/NFR quality prompts |
| Guides | `docs/guides/workflows/` | Tutorials + artifact matrix |
| Templates | `templates/` | cursorrules.template, bootstrap scripts |
| Decision tree | `START_HERE.md` | Operator entry point |
| Process router | `PROCESS_ROUTER.md` | Process Q&A reference |
