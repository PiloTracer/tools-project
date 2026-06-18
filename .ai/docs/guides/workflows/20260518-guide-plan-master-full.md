# Guide - master / full plan (`plan-master` skill)

**Doc type:** Planning reference guide (portable).  
**Skill:** `plan-master` - output: `{MASTER_PLAN}` path (often `.work/plans/full/YYYYMMDD-full-plan.md`).  
**Prerequisite:** `plan-master-ready` from `plan-foundation` (or explicit waiver in `{HANDOFF}` per skill).

---

## 1. What the master plan is

A **single** implementation roadmap that links:

**Business goal → FR/NFR → architecture → milestone → task id → validation → acceptance**

It is the **only** home for **M1…Mn** milestone tables and **global** acceptance (section numbers vary - record yours in `{HANDOFF}`).

---

## 2. Invocation verbs (read skill first)

| User intent | Typical verb |
|-------------|--------------|
| Read-only health check | `status` |
| Resume authoring | `continue` |
| New plan from inputs | `greenfield` |
| Contradiction sweep | `integrity` |
| Change after approval | `revise` - with reason |
| Look up one task | `task` M3-T5 |

Exact parse table: **`plan-master/skill.md`**.

---

## 3. Greenfield flow (happy path)

1. Gather YAML or pointers to `README`, `{HANDOFF}`, foundation docs, SPECs.  
2. `plan-master greenfield` - produces draft `*-full-plan.md`.  
3. Human review: FR/NFR realism, milestone sizing, validation gates.  
4. `plan-master integrity` - fix contradictions; update `UNKNOWNS` for open items.  
5. Obtain **Approved** status in plan header (human process).  
6. `plan-master status` - confirm **implementation-ready** per skill criteria.

---

## 4. Traceability you should see inside the plan

- Every major FR has **tasks** and **tests** called out somewhere in milestone or validation sections.  
- NFRs (security, observability, deployability) map to **tasks** or explicit waivers (append-only).  
- No silent **Unverified** compliance claims - label or cite.

---

## 5. After the plan is Approved

1. Update `{HANDOFF}` **Repository state** with plan path + version.  
2. Run **`@code-implementation plan - M1`** (or next incomplete milestone) to build `{ITERATION_CARRIER}` - see [NEXT iteration block](20260518-tutorial-next-generate-new.md).

---

## 6. Common mistakes

- Editing merged SPECs instead of **amendment** files when the plan exposes a SPEC gap.  
- Putting **execution task tables** inside foundation doc 04 (belongs in master plan section 19).  
- Marking **implementation-ready** inside `plan-foundation` (wrong skill).
