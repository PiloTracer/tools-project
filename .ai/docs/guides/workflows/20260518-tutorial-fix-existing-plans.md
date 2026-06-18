# Tutorial - fix existing plans (`NEXT` + full plan)

**Doc type:** Corrective maintenance tutorial (portable).  
**NEXT-only repair:** [Fix NEXT tutorial](20260518-tutorial-next-fix.md).  
**Use when:** `{ITERATION_CARRIER}` and `{MASTER_PLAN}` predate the workflow guides; milestones, FR links, or iteration blocks are **out of sync**.

**Worked example (replace dates/slugs in your clone):** `{ITERATION_CARRIER}` = `.work/plans/NEXT.md`, `{MASTER_PLAN}` = `.work/plans/full/YYYYMMDD-full-plan.md` (record your plan’s milestone/acceptance section ids in `{HANDOFF}`).

---

## 1. Know the three layers (do not conflate them)

| Layer | Typical file (example) | What it must contain |
|-------|--------------------------|----------------------|
| **Strategic roadmap** | `{MASTER_PLAN}` | Goals, FR/NFR tables, **milestone** deliverables, global acceptance, validation gates. |
| **Tactical queue** | `{ITERATION_CARRIER}` | **Current** milestone slice: tasks, acceptance for **this** slice only, validation commands, blockers. |
| **Behaviour contract** | `{FEATURE_SPEC_ROOT}/.../*SPEC.md` | Rules R1…, data model, observability, **concept registry** per feature. |

**Rule:** Numbers and ids in the iteration block should **cite** the master plan, not invent new requirements.

---

## 2. Audit `{MASTER_PLAN}` (30-minute pass)

Open your full plan and check:

1. **Header metadata** - Status (Approved / Draft), version, last revised date.  
2. **Section numbers** - Example layout: **§19** = incremental roadmap, **§20** = global acceptance, **§21** = validation gates. Your plan may differ; **record the section ids** in `{HANDOFF}` so agents stop guessing.  
3. **Milestone table** - Every milestone has: objective, dependencies, size (or equivalent).  
4. **Per-milestone tasks** - Each row: stable **task id** (e.g. `M1-T3`), description, FR/NFR trace, file paths, validation.  
5. **FR/NFR drift** - Each milestone task references FR/NFR ids that **exist** in sections 3–4 (or your plan’s equivalent). Fix broken references.  
6. **NFR observability** - If NFR9 (or equivalent) names logging/tracing, milestone **M1**-class tasks should mention it where platform logging is built.

**Fix pattern:** append a dated revision note at top; **do not** silently rewrite historical text - add “**Correction YYYY-MM-DD:** …” if your governance requires audit trail.

### Optional improvement (example project)

Add a short subsection under **19** pointing operators to `.ai/docs/guides/workflows/README.md` so humans know where process lives (see what you merge from this tutorial’s companion PR).

---

## 3. Audit `{ITERATION_CARRIER}` (20-minute pass)

For the **active** `## Current iteration` block:

| Check | Pass if |
|-------|---------|
| **Milestone ref** | Points to `{MASTER_PLAN}` + correct section (here: §19 `M{N}`). |
| **Task ids** | Match master plan ids **exactly** (`M1-T1`, not renumbered `T1` only, unless your skill explicitly allows shorthand **inside** the block only). |
| **Files** | Every task lists at least one path or `TBD` + owner blocker. |
| **FR/NFR** | Each task row has trace or honest `-` with reason. |
| **Acceptance** | Checklist is **for this milestone only**; not a dump of entire plan section 20. |
| **Validation** | At least one command block is **copy-paste runnable** in your environment (here: Docker-based). |
| **Concept / NFR registry** | Subsection exists; rows for each concept id your repo uses, or `N/A` with reason. |
| **Cross-LLM** | Row exists (even if `skipped`). |

**Fix pattern:** insert missing subsections; align task text with master plan **verbatim** where the plan is source of truth.

---

## 4. Reconcile SPEC ↔ plan ↔ iteration (when drift is found)

1. Pick the **SPEC** that owns the behaviour (e.g. `.work/features/<slug>/…-SPEC.md`).  
2. If the master plan claims a rule the SPEC does not have → **SPEC amendment** (new dated file), not silent SPEC edit if already merged.  
3. If the iteration block claims files the master plan does not → **trim iteration** to match plan, or run `@plan-master revise` (or your equivalent) to update the plan first.  
4. Update **Concept / NFR registry** in the iteration block to match the **SPEC’s** registry for this feature slice.

---

## 5. Observability and traceability catch-up

1. Open [Observability in workflow](20260518-guide-observability-traceability-in-workflow.md).  
2. For each milestone that touches HTTP, jobs, or logging: ensure **M1-style** platform tasks exist **before** domain milestones emit user traffic (e.g. health, observability, tenant middleware in M1).  
3. In `{ITERATION_CARRIER}` acceptance bullets, add one line: “Structured log line includes …” only if SPEC/plan already define fields (avoid inventing names here - pull from `{OBSERVABILITY_SPEC}`).

---

## 6. Order of edits (minimize thrash)

1. Fix `{MASTER_PLAN}` FR/NFR and milestone tables (source of truth).  
2. Regenerate or hand-fix `{ITERATION_CARRIER}` **Current iteration** from plan **§19** only.  
3. Patch SPECs / ADRs if gaps were found.  
4. Run **`@code-verify milestone`** on the iteration before declaring the docs pass complete.

---

## 7. Done checklist

- [ ] Every iteration task id exists in `{MASTER_PLAN}` section 19 (or your mapped section).  
- [ ] No orphan FR/NFR ids in the iteration table.  
- [ ] Concept / NFR registry present (N/A rows have reasons).  
- [ ] Validation commands match current repo layout (Docker vs bare metal).  
- [ ] `{HANDOFF}` **Repository state** paragraph mentions the milestone you are on.

You have now **re-based** tactical files on the strategic plan without losing history.
