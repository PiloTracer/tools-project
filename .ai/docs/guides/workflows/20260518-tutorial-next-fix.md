# Tutorial - fix `{ITERATION_CARRIER}` (NEXT-style file)

**Doc type:** Corrective tutorial (portable).  
**Skill:** `code-implementation` **plan** (regenerate) or **manual** edit - see valid-block criteria in `{SKILLS_ROOT}/code-implementation/skill.md`. *(Legacy alias of `plan`: `plan-iteration`.)*  
**Related:** [Fix plans + full plan drift](20260518-tutorial-fix-existing-plans.md) (broader), [Generate new NEXT](20260518-tutorial-next-generate-new.md) (structure).

Use this doc when **`{ITERATION_CARRIER}` is wrong or stale** but you already have an Approved `{MASTER_PLAN}`.

---

## 1. Symptoms (you need this tutorial)

- `## Current iteration` is **missing**, duplicated, or under the wrong heading order.  
- Task ids (`M2-T1`) **do not exist** in the master plan section for milestones.  
- **Acceptance** bullets describe the **whole product** instead of **this milestone only**.  
- **Validation** has no runnable command, or commands are for the wrong stack.  
- **`### Concept / NFR registry`** missing while your rules require it.  
- **`## Recommended next`** still says “start M1” while M1 is **done**.

---

## 2. Safe fix order (avoid losing history)

1. **Copy** the entire current `{ITERATION_CARRIER}` file to a scratch note (outside git or in `tmp/` per repo hygiene).  
2. Fix **`{MASTER_PLAN}` first** if task ids or FR links are wrong - [broader tutorial](20260518-tutorial-fix-existing-plans.md).  
3. Either:  
   - **A)** Run `@code-implementation plan - M{N}` with the **correct** milestone (agent regenerates `## Current iteration` per skill), or  
   - **B)** Manually edit only inside `## Current iteration …` through `### Done this iteration` (do not delete `## Done` history rows).

---

## 3. Section-by-section repair checklist

### 3.1 Header (`## Current iteration - M…`)

| Field | Fix if |
|-------|--------|
| Milestone ref | Does not point to `{MASTER_PLAN}` + the section that lists this milestone’s tasks. |
| Status | Stuck on `planning` while tasks are `done` → set to `complete` or start new iteration. |
| Dates | `Started` / `Target` blank → fill honestly. |

### 3.2 In scope / Out of scope

- Must match **this milestone only** (copy from master plan milestone “Scope” if needed).  
- Remove bullets that belong to **other** milestones.

### 3.3 Concept / NFR registry (if required)

- One row per concept id **or** explicit `N/A` with owner.  
- Align with feature SPEC section 15 when a feature drives the iteration.

### 3.4 Task table

| Column | Fix if |
|--------|--------|
| ID | Not exactly `M{N}-T{n}` from master plan → **correct ids** (do not invent). |
| Files | Empty without `TBD` + blocker → add paths or blocker row. |
| FR/NFR | Orphan ids → fix master plan or task row. |
| Status | Multiple `in-progress` → keep one. |

### 3.5 Acceptance criteria

- 3–8 **checkboxes** testable **at end of this milestone**.  
- Remove global GA criteria (those belong in master plan section 20).

### 3.6 Validation steps

- At least **one** command your CI or humans can run (from `.cursorrules` `REPLACE:TEST_COMMAND` and related gates).  
- Replace host-only commands if your project forbids them.

### 3.7 Owner blockers / Cross-LLM / Done this iteration

- **Owner blockers:** each item has an owner name or role.  
- **Cross-LLM:** present; use `skipped` with reason if single model.  
- **Done this iteration:** append rows when tasks finish; **never** delete historical done rows (append-only discipline).

### 3.8 `## Recommended next` (above iteration)

- After milestone complete: first row should be **`@code-implementation plan - M{N+1}`** or explicit human task.  
- Remove stale “start M1” when M1 is complete.

---

## 4. Validate after edits

1. Walk [Valid iteration criteria](20260518-tutorial-next-generate-new.md) (same as `code-implementation` skill).  
2. Run `code-implementation` **status** mode (read-only) if available.  
3. Open a PR; use your PR template’s checklist.

---

## 5. When to nuke vs repair

- **Repair:** one wrong subsection, ids off-by-one, missing registry.  
- **Regenerate:** iteration block is messier than 30 minutes to fix → `@code-implementation plan` for clean structure.  
- **Nuke (rare):** file has conflicting duplicate `## Current iteration` headers → keep file, delete duplicate section bodies after backup, then regenerate one block.
