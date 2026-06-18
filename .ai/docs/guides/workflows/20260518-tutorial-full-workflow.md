# Tutorial - full workflow (example)

**Doc type:** Step-by-step tutorial (portable).  
**Prerequisite:** [Path bootstrap](20260518-tutorial-path-bootstrap.md) completed in your clone (placeholders point at real files).

**What you will produce:** a traceable trail from **idea** → **spec** → **planned iteration** → **implementation** → **verification**, with **concept / NFR** and **observability** hooks.

---

## Roles (who does what)

| Role | Responsibility |
|------|------------------|
| **Product / EM** | Proposal, priority, acceptance in plain language. |
| **Tech lead** | SPEC review, ADRs, boundary map ownership, waivers. |
| **Implementer (human or agent)** | Follows `{SKILLS_ROOT}` implementation skill + task gates. |
| **Reviewer** | Runs concept `prompt.md` outputs for risky diffs; checks verify matrix. |

---

## Phase 0 - One-time setup (per repository)

1. Open [Path bootstrap](20260518-tutorial-path-bootstrap.md).  
2. Copy the placeholder table into `{AGENT_RULES_FILE}` and fill the **right column**.  
3. Add the **invocation contract** sentence (same doc).  
4. Either author `{BOUNDARY_MAP}` using [Boundary map how-to](20260518-guide-boundary-map-howto.md) or record **explicit deferral** with owner + date.  
5. Read [End-to-end workflow](20260518-guide-end-to-end-workflow.md) once as a team.

---

## Phase 1 - Intake (idea → scoped feature)

1. Create a **proposal** (tracker ticket or `{FEATURE_SPEC_ROOT}/../plans/proposals/YYYYMMDD-slug.md` - use your FEATURE_STANDARD).  
2. Name the **bounded contexts** touched (even tentative).  
3. Open `{CONCEPTS_INDEX}` and list which **concept ids** might apply (coupling, network, cost, ops, modularity, AI amplification).  
4. Record a **preliminary** concept table in the ticket: `id` | `likely yes/no` | `reason`.

**Exit criterion:** tech lead acknowledges scope.

---

## Phase 2 - Feature SPEC (behavior + NFR)

1. Create `{FEATURE_SPEC_ROOT}/<slug>/YYYYMMDD-SPEC.md` using your feature template (must include **Observability** and **Concept / NFR registry** sections if your standard requires them).  
2. Write **numbered behavioural rules** (R1, R2, …) so tests and PRs can cite them.  
3. Fill **§Concept / NFR registry**: each concept row = applies, owner, evidence or N/A reason.  
4. Link **ADRs** and **master plan** FR/NFR ids.

**Exit criterion:** SPEC reviewed per your gate (e.g. ≥1 reviewer; ≥2 if high risk).

---

## Phase 3 - Master plan alignment

1. Open `{MASTER_PLAN}`.  
2. Confirm the milestone that will deliver this feature lists the right **FR/NFR** rows (add or fix rows if drift - see [Tutorial - fix existing plans](20260518-tutorial-fix-existing-plans.md)).  
3. If the feature adds a new **deployable** or **sync chain**, run the relevant **concept prompts** (`cost-model`, `network-cost`, `ops-headcount`, …) and **attach** outputs to the ADR or plan appendix with evidence tags.

**Exit criterion:** milestone text matches SPEC scope; no orphan FR ids.

---

## Phase 4 - Iteration block (`{ITERATION_CARRIER}`)

1. Run your implementation skill’s **plan** mode (e.g. `@code-implementation plan - M{N}`; legacy alias `plan-iteration`) **or** manually create the iteration section using the same shape your skill defines.  
2. Ensure the block includes:  
   - Milestone ref → `{MASTER_PLAN}` section for that milestone.  
   - In / out of scope.  
   - Task table with **ids**, **files**, **FR/NFR**.  
   - Acceptance criteria + **validation commands** (runnable).  
   - **`### Concept / NFR registry (this iteration)`** - copy from SPEC or mark N/A per row with reason.  
3. Add **Cross-LLM** or peer review row if your process uses it.

**Exit criterion:** iteration block passes your skill’s **valid iteration** checklist.

---

## Phase 5 - Session open (optional but recommended)

1. Run **session start** skill (if present) or manually read `{HANDOFF}`, `{ITERATION_CARRIER}`, `{CONCEPTS_INDEX}`.  
2. Note dirty git tree, blockers, and which **MOD** prompts you expect to run this week.

---

## Phase 6 - Implement tasks

For **each** task:

1. Read SPEC rules and files **before** edits.  
2. Implement; run **task gate** (tests, lint, type, secrets scan, scope discipline).  
3. If AI-generated: run **AI amplification** concept prompt; paste result into PR or task Notes.  
4. If logging/tracing touched: confirm fields vs [Observability guide](20260518-guide-observability-traceability-in-workflow.md) and SPEC §Observability.  
5. Mark task done **only** after gate passes.

---

## Phase 7 - Verify

1. Run implementation **verify** protocol against `{MASTER_PLAN}` milestone acceptance + **concept registry** rows marked `yes`.  
2. Confirm **observability** row: log/trace fields for touched paths or documented `n/a`.  
3. Record verdict: pass / pass with gaps / fail; gaps need owner or waiver in `{HANDOFF}`.

---

## Phase 8 - Complete iteration + session close

1. Run **complete** protocol: archive tasks, update `{ITERATION_CARRIER}` **Recommended next**, refresh `{HANDOFF}`.  
2. Session **close** with commit message draft.  
3. Update feature **CHANGELOG** if your standard requires it.

---

## Quick reference - artifact chain

```text
Proposal
  → SPEC (domain + MOD registry + observability)
    → MASTER_PLAN milestone (FR/NFR trace)
      → ITERATION_CARRIER block (tasks + same MOD registry)
        → PRs / commits (prompt outputs attached)
          → VERIFY matrix
            → HANDOFF / NEXT recommended next
```

You now have **end-to-end traceability** from business language to validation without being tied to a single vendor tool.

---

## See also (step tutorials)

| Topic | Guide |
|-------|--------|
| Foundation | [plan-foundation](20260518-guide-plan-foundation.md) |
| Master plan | [plan-master](20260518-guide-plan-master-full.md) |
| NEXT sub-plan | [plan / sub-plan](20260518-tutorial-next-generate-new.md) |
| Delivery loop | [Multiple iterations](20260518-tutorial-implement-multiple-iterations.md) |
| Verify & test in dev | [Verify / audit / test](20260518-tutorial-verify-audit-test-development.md) |
| Tests in process | [Testing in workflow](20260518-guide-testing-and-test-suite-in-workflow.md) |
| Fix NEXT | [Fix NEXT](20260518-tutorial-next-fix.md) |
| New NEXT file | [Generate NEXT](20260518-tutorial-next-generate-new.md) |
