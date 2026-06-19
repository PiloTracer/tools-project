# Skill dependency graph

**Purpose:** Single source of truth for **which skill may run before which**. Skills implement these rules in their own `skill.md` § Prerequisite gates; this file is the registry operators and maintainers read first.

**Invocation punctuation:** Use ASCII hyphen **`-`** between verb and argument (e.g. `@code-implementation plan - M1`, `@feature-spec create - my-slug`, `@process-router - how do I close?`). Do **not** use em dash `—` in commands (hard to type on most keyboards).

## Work tree path resolution (mandatory)

**Repository root** (`.git/`, `.cursorrules`) is **not** `{WORK_ROOT}`. All skills resolve placeholders from **repo root** per `.cursorrules` placeholder map (or this table).

| Placeholder | Resolved path | Common wrong path (missing `.work/`) |
|-------------|---------------|--------------------------------------|
| `{WORK_ROOT}` | `.work/` | repo root, `work/` |
| `{HANDOFF}` | `.work/context/HANDOFF.md` | `context/HANDOFF.md`, `HANDOFF.md` |
| `{ITERATION_CARRIER}` | `.work/plans/NEXT.md` | `plans/NEXT.md`, bare `NEXT.md` at repo root |
| `{PLANS_ROOT}` | `.work/plans/` | `plans/` |
| `{FEATURE_SPEC_ROOT}` | `.work/features/` | `features/` |
| `{DECISIONS_ROOT}` | `.work/decisions/` | `decisions/` |
| `{PROMPTS_ROOT}` | `.work/prompts/` | `prompts/` |
| `{MASTER_PLAN}` | `.work/plans/full/*-full-plan.md` (latest **Approved**) | `plans/full/…` |

**Rule for agents:** In mandatory-read tables, `Read` tool calls, and blocked reports, use the **Resolved path** column. Do not strip the `.work/` prefix. Shorthand (`HANDOFF`, `NEXT.md`) in prose must still mean the resolved path above.

**Readiness states** (do not conflate):

```text
project-bootstrap (scaffold)
        ↓
foundation-complete  →  plan-master-ready  →  implementation-ready
   plan-foundation        plan-foundation       plan-master status
                          certify
```

| State | Certified by | Unlocks |
|-------|--------------|---------|
| *(scaffold only)* | `@project-bootstrap init` | `@plan-foundation greenfield`, `@session-control` (minimal) |
| **foundation-complete** | `@plan-foundation status` (P0–P6 gates) | `@plan-foundation certify`, foundation **continue** |
| **plan-master-ready** | `@plan-foundation certify` | `@plan-master greenfield` / **continue** / **revise** |
| **implementation-ready** | `@plan-master status` | `@code-implementation start` / **continue** (broad); `@code-implementation plan` *(alias: `plan-iteration`)* with Approved plan |

**M1 early start:** `plan-foundation` may authorize M1 skeleton when **plan-master-ready: yes** and HANDOFF/NEXT document a waiver - that is **not** implementation-ready. `code-implementation` honors HANDOFF milestone waivers per its skill.

---

## Dependency matrix

**Legend:** **Required** = stop and redirect if unmet. **Recommended** = warn, proceed only if user confirms in the same message. **-** = no gate. **Read-only** modes never mutate artifacts.

| Skill / mode | Depends on | Gate |
|--------------|------------|------|
| **project-bootstrap** `init` | Repo contains `.ai/` (or is Agent OS root); **B0** brownfield gate detects existing `.work/` / `.cursorrules` / stack doc | - (brownfield prompts overwrite-all / overwrite-missing / keep / abort) |
| **project-bootstrap** `status` | - | Read-only |
| **session-control** `start` | `{HANDOFF}` (offer bootstrap if missing) | Recommended: `@project-bootstrap init` |
| **session-control** `close` | Prior `start` or dirty tree | - |
| **session-control** `status` | - | Read-only |
| **plan-foundation** `greenfield` | `.cursorrules`, `{HANDOFF}` (GF0 gate) | Recommended: `@project-bootstrap init` |
| **plan-foundation** `continue` | Prior foundation work started | - |
| **plan-foundation** `probe` | `{HANDOFF}` + foundation doc 01 to record into (GF0 gate) | Recommended: `@plan-foundation greenfield` if nothing to probe |
| **plan-foundation** `certify` | **foundation-complete: yes** (CF0 gate) | **Required** |
| **plan-foundation** `status` | - | Read-only |
| **plan-master** `greenfield` | **plan-master-ready: yes** (PG1 gate) | **Required** (see exceptions below) |
| **plan-master** `continue` | **plan-master-ready: yes**; draft or partial `*-full-plan.md` | **Required** |
| **plan-master** `probe` | **plan-master-ready: yes** (PG1); Draft/partial `*-full-plan.md` (PG2) | **Required**; run before `integrity` |
| **plan-master** `revise` | Existing `*-full-plan.md`; **plan-master-ready** still valid | **Required** |
| **plan-master** `integrity` | Target artifacts exist (foundation set **or** master plan for P5) | Invoked by plan-foundation certify **or** standalone |
| **plan-master** `status` / `show` *(alias: `task`)* | - | Read-only |
| **plan-verify** `foundation` / `master` / `alignment` | Target artifacts exist for mode (alignment: valid `NEXT` iteration + `{MASTER_PLAN}`) | Read-only; orchestrates plan-foundation status + plan-master integrity; **BF branch** when brownfield |
| **plan-verify** `brownfield` | Code-first or legacy-doc repo; formal plan-foundation/master may never have run | Read-only; framework slot map + substitute paths |
| **plan-verify** `status` | - | Read-only |
| **plan-repair** `repair` / `foundation` / `master` / `brownfield` | Findings from `@plan-verify`, user goal after `-`, or brownfield discovery (R0 gate) | **Recommended:** run source verify if no report in chat |
| **plan-repair** `brownfield` | BF0 = yes; may synthesize `.work/` without prior formal greenfield | May write; re-verify with `@plan-verify brownfield`; formal certify optional after |
| **plan-repair** `status` | - | Read-only |
| **code-implementation** `plan` *(alias: `plan-iteration`)* | Approved `*-full-plan.md` **or** HANDOFF M{N} waiver (PI1 gate) | **Required** |
| **code-implementation** `start` / `continue` | Valid `NEXT.md` iteration block; **implementation-ready** or HANDOFF waiver (ST0 gate); auto-invokes `@code-verify uncommitted` at batch end (see § Self-verify auto-invoke) | **Required** |
| **code-implementation** `complete` | Active iteration; `@code-verify milestone` pass | **Required** |
| **code-implementation** `status` | - | Read-only |
| **code-verify** `milestone` | Active milestone exists in `{MASTER_PLAN}` §19 **or** `NEXT.md` § Current iteration (M0 gate) | **Required** |
| **code-verify** `uncommitted` / `last` | - | - |
| **code-verify** `status` | - | Read-only |
| **code-repair** `repair` (open language / **custom**) | R0-free implementation alignment when no verifier report in chat | **Recommended** before F* rows |
| **code-repair** `repair` | Findings from verifier report, fresh `@code-verify` / `@db-migration verify` / `@feature-spec review`, or **custom** brief (R0 gate) | **Recommended:** run source verifier if no report in chat |
| **code-repair** `status` | - | Read-only |
| **feature-spec** `intake` | None (free-text front door); classifies + routes, only writes a SPEC when class=`local` (then follows `create` gates) | - (read/route; records to `NEXT.md § Intake queue`) |
| **feature-spec** `create` | FEATURE_STANDARD; **CR0** hard-stops if `<slug>/` folder exists; warns if `plan-master-ready: no` | **Required** (brownfield) + **Recommended** (readiness) |
| **feature-spec** `review` / `amend` / `status` / `approve` | FEATURE_STANDARD; `approve` runs `review` first and only flips Status on pass | - |
| **feature-spec** before **Approved** | §15 concept registry | **Required** per FEATURE_STANDARD |
| **concept-run** `run` | Applicable trigger (SPEC §15, iteration registry, diff scope) | Per `.ai/concepts/README.md` |
| **concept-run** `list` / `status` | - | Read-only |
| **db-migration** `init` | Repo at Agent OS root; **IB0** brownfield gate detects existing runner + `001_init.sql` | - (brownfield prompts keep / overwrite-runner / overwrite-all / abort) |
| **db-migration** `create` / `add` / `run` / `verify` | `db-migration init` already run (runner module + `001_init.sql` baseline present); `create` / `add` auto-invokes idempotency double-run (`@db-migration verify` on the new script, see § Self-verify auto-invoke) | **Required** |
| **db-migration** `status` | - | Read-only |
| **deploy-files** `copy` | Target parent dir must exist (I0 gate); source is this `.ai` repo | - |
| **deploy-files** `status` | - | Read-only |
| **deploy-repo** `clone` | Target must not exist; source must have origin remote (I0 gate) | - |
| **deploy-repo** `archive` | Target parent dir must exist (I0 gate) | - |
| **deploy-repo** `status` | - | Read-only |
| **dev-stack** `init` | User request / `docker-compose*.yml` present; brownfield gate refuses to silently overwrite existing `bin/start.sh` | - |
| **dev-stack** `status` | - | Read-only |
| **process-router** `route` / `help` | - | Read-only |

---

## Exceptions and waivers

| Situation | Rule |
|-----------|------|
| **plan-master greenfield** without prior certify | **Forbidden** unless HANDOFF already records `Plan-master-ready: <date>` from a prior certify, or user supplies structured YAML with complete `foundation_docs:` paths **and** confirms foundation was completed out-of-band in the same message. |
| **plan-repair brownfield** without plan-master-ready | **Allowed** — synthesize Draft master plan + HANDOFF `Brownfield-aligned:` / `Brownfield master synthesis:` lines; **implementation-ready** remains **no** until formal Approved plan. |
| **plan-verify brownfield** without foundation docs | **Allowed** — score substitutes (README, ROADMAP, code tree); verdict `aligned-best-effort` not formal certify. |
| **plan-master reference edge case** | Do **not** draft a master plan when foundation is not ready - **stop** and list blockers (see `plan-master/skill.md` § Prerequisite gate). |
| **code-implementation** before **implementation-ready** | **Stop** unless HANDOFF explicitly waives a named milestone (e.g. M1 platform skeleton). |
| **plan-master integrity** on foundation only | Does **not** require an existing `*-full-plan.md`; plan-foundation **certify** invokes this. |
| **feature-spec** during plan-foundation P3 | Expected; SPECs need not wait for plan-master. |
| **db-migration** | Does not require plan-master; requires an implementation task or explicit user request. |

---

## Redirect cheat sheet

| User tried | Blocked because | Run next |
|------------|-----------------|----------|
| `@plan-master greenfield` | Not plan-master-ready | `@plan-foundation status` → `@plan-foundation certify` |
| `@plan-foundation certify` | Not foundation-complete | `@plan-foundation continue` |
| `@plan-foundation greenfield` | No HANDOFF / `.cursorrules` | `@project-bootstrap init` |
| `@code-implementation start` | No iteration block | `@code-implementation plan - M{N}`   *(alias: `plan-iteration`)* |
| `@code-implementation plan` (or `plan-iteration`) | No Approved plan | `@plan-master status` → approve or waiver in HANDOFF |
| `@code-implementation start` | Not implementation-ready | `@plan-master status` or document HANDOFF waiver |
| `@code-verify milestone - M{N}` | Milestone M{N} not in plan / NEXT | `@plan-master show M{N}` or `@code-implementation plan - M{N}` |
| `@db-migration create/run` | `db-migration init` never ran | `@db-migration init` |
| `@feature-spec create - <slug>` | Folder already exists | `@feature-spec amend - <slug>` |
| `@project-bootstrap init` | Repo already bootstrapped | `@project-bootstrap status` (or run `init` with overwrite confirmation) |
| "Ready to code?" in plan-foundation | Wrong skill | `@plan-master status` |
| `@code-verify` / sweep **fail** | Findings need remediation | `@code-repair repair - from uncommitted` (or matching source mode) |
| `@db-migration verify` **fail** | Script not idempotent or runner error | `@code-repair repair - from migration` |
| `@plan-verify` **fail** (foundation/master/alignment) | Plan doc gaps or drift | `@plan-repair repair - from <same mode>` |
| `@plan-repair master` | Not plan-master-ready (formal) | `@plan-repair brownfield` **or** `@plan-repair foundation` → `@plan-foundation certify` |
| Legacy repo, no `.work/plans/` | No formal planning | `@plan-verify brownfield` → `@plan-repair brownfield` |
| Plan gaps during code work | Wrong layer | `@plan-repair` / `@plan-master revise` (not `code-repair`) |
| Scope/NFRs/constraints vague; "do you understand the project?" | Understanding gap, not artifact gap | `@plan-foundation probe` (then `certify`) |
| Plan has vague NFRs / unmapped FRs / ownerless risks | Plan-completeness gap | `@plan-master probe` → `@plan-master integrity` |

---

## Canonical command vocabulary

All skills use the same verbs where applicable. This keeps muscle memory portable.

| Canonical verb | Meaning | Skills that implement it |
|----------------|---------|---------------------------|
| `status` | Read-only: report current state | plan-foundation, plan-master, plan-verify, plan-repair, session-control, code-implementation, code-verify, code-repair, feature-spec, db-migration, concept-run, dev-stack, project-bootstrap |
| `repair` | Fix reported issues; re-verify | code-repair, plan-repair |
| `verify` | Audit planning artifacts (foundation / master / alignment) | plan-verify |
| `probe` | Adaptive gap-driven interrogation loop; scores knowledge/plan coverage, asks targeted questions, fills gaps into registries. **New verb** (distinct from `status` read-only, `continue` resume-phase, `integrity` auto-sweep). Engine: [`probe-protocol.md`](probe-protocol.md) | plan-foundation, plan-master |
| `start` | Begin a unit of work | session-control, code-implementation |
| `continue` | Resume in-progress work | plan-foundation, plan-master, code-implementation |
| `continue` + target (`code-implementation` only) | Batch tasks: `- N`, `- until blocked`, `- M{N}-T{a}..T{b}`; stop on gate fail or blocker | code-implementation |
| `close` | Wrap up + handoff | session-control |
| `complete` | Mark a unit as done | code-implementation |
| `plan` | Prepare next unit | code-implementation *(alias: `plan-iteration`)* |
| `init` | One-time setup | project-bootstrap, db-migration, dev-stack |
| `intake` | Classify a free-text feature request → route to the right executor; records to `NEXT.md § Intake queue` (does not auto-execute cross-cutting/brownfield paths) | feature-spec |
| `create` | Make a new artifact | feature-spec, db-migration |
| `amend` | Modify an existing artifact | feature-spec |
| `review` | Read-only audit of an artifact | feature-spec |
| `revise` | Structured edit | plan-master |
| `certify` | Formal sign-off transitioning a readiness state | plan-foundation |
| `greenfield` | First-time creation | plan-foundation, plan-master |
| `verify` / `milestone` / `uncommitted` / `last` | Runtime/output checks | code-verify (scope flag), db-migration; **plan-verify** uses `foundation` / `master` / `alignment` (not bare `verify` alone) |
| `brownfield` | Discover/create missing planning artifacts from existing repo | plan-repair |
| `alignment` / `drift` | NEXT vs master plan consistency | plan-verify (read-only), plan-repair (fix) |
| `run` | Execute (scripts / prompts) | db-migration, concept-run |
| `show` | Read-only inspect of a specific record | plan-master *(alias: `task`)* |
| `list` | Enumerate available items | concept-run |
| `route` / `help` | Read-only Q&A | process-router |

**Alias policy:** When a verb is renamed, the old name is kept as an alias for **at least one minor version**. Aliases are listed inline in each skill's parse-invocation table and in the matrix above.

---

## Blocked report shape (every gate)

When a gate stops execution, the skill emits a uniform block so users always see the same shape:

```markdown
## @<skill> <command> - blocked (prerequisite)

**Required:** <state or upstream step>
**Detected:** <what's actually present>
**Run first:** `<exact command to fix>`
```

Skills must not invent ad-hoc error messages for prerequisite failures.

---

## Self-verify auto-invoke

Some mutating skills must invoke a verifier on the artifact they just produced **before** declaring the mode complete. This is in addition to per-step mechanical gates and prevents "issues surface only after the user prompts again".

| Skill / mode | Auto-invokes | When | Skip allowed? |
|--------------|--------------|------|----------------|
| `code-implementation` `continue` (any `-` target) | `@code-verify uncommitted` over cumulative batch diff (see `code-implementation` § Batch-end sweep) | After per-task loop ends, before Batch summary | Only when zero files changed during the loop |
| `code-implementation` `complete` | `@code-verify milestone` | CO2, before final gates | No |
| `db-migration` `create` / `add` | `@db-migration verify` (or `run` twice in dev DB) on the new script | C6, before declaring create complete | Only when DB not reachable; record reason |
| `feature-spec` `approve` | `@feature-spec review` | Before flipping `Status: Approved` | No |

**Honesty:** Auto-invoked verifiers run with the **same evidence rules** as standalone invocations. A `pass` claim without exit code, file path, or quoted output is treated as `unverified` per `.cursorrules` Core Principle 5.

**Post-fix re-gate** (separate from auto-invoke): when an agent applies a fix in response to **any** reported issue, the affected task's gate **must** be re-run before claiming repair. See `code-implementation` § Post-fix re-gate.

---

## Maintenance

When adding or changing a skill:

1. Update this matrix and (if a new verb is introduced) the canonical vocabulary above.
2. Add or update § **Prerequisite gate** in that skill's `skill.md` using the **blocked report shape**.
3. Add a row to `process-router/reference.md` if operators commonly hit the gate.
4. Do **not** duplicate normative gate text in START_HERE beyond the readiness diagram - link here or to the skill.
5. Prefer **reusing an existing canonical verb** over inventing a new one. If a new verb is unavoidable, document why.
