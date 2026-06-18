# Guide - foundation plan (`plan-foundation` skill)

**Doc type:** Planning reference guide (portable).  
**Skill:** `plan-foundation` - canonical file: `{SKILLS_ROOT}/plan-foundation/skill.md`.  
**Output home (typical):** `.work/plans/foundation/` docs **01–04**, ADRs, SPECs, registries - **not** the master execution plan.

---

## 1. What foundation planning is

**Foundation** answers: *What product, what constraints, what verified external facts, what architecture proposal, what risks?*

It **stops** at **plan-master-ready** certification. It does **not** replace:

- `{MASTER_PLAN}` (`*-full-plan.md`) - owned by **plan-master**.  
- `{ITERATION_CARRIER}` tactical tasks - owned by **code-implementation** after the master plan is Approved.

---

## 2. When to run it

| Situation | Mode (typical) |
|-----------|----------------|
| New greenfield product | `greenfield` then `continue` through P0–P6 |
| Resume stalled foundation | `continue` |
| Check if you can start plan-master | `status` |
| Formal gate before master plan | `@plan-foundation certify plan-master-ready` (exact phrase per `plan-foundation/skill.md` parse table) |

Parse table lives in **`plan-foundation/skill.md`** - read it before invoking.

---

## 3. Phase mental model (P0–P6)

Your skill file is authoritative; typically:

- **P0** - registry bootstrap (`ASSUMPTIONS`, `RISK_REGISTRY`, `UNKNOWNS`), HANDOFF shape.  
- **P1** - foundation docs folder + doc **01** scope.  
- **P2** - integration / evidence (doc **02**).  
- **P3** - adjacency / ERP lanes (doc **03**, optional).  
- **P4** - architecture foundation (doc **04**) - **not** “full plan” wording.  
- **P5–P6** - integrity, SPECs, ADRs, directory map, **certify plan-master-ready**.

---

## 4. Anti-confusion (required vocabulary)

| Wrong | Right |
|-------|-------|
| Calling doc 04 “the full plan” | **Architecture foundation**; master plan = `*-full-plan.md` only |
| Asking plan-foundation for M1 task lists | Use **plan-master** after certify |

---

## 5. Human checklist before leaving foundation

- [ ] Doc 01–04 exist and cross-link; no duplicate “mega plan” inside them.  
- [ ] ADRs exist for Decided architecture; open ones in `UNKNOWNS`.  
- [ ] `{HANDOFF}` states foundation-complete and points to next skill (**plan-master**).  
- [ ] `@plan-foundation certify plan-master-ready` (or equivalent per skill) recorded **pass** with evidence.

---

## 6. Next step

Run **`@plan-master status`** then **`@plan-master greenfield`** (or `continue`) per `plan-master` skill - see [Guide - master / full plan](20260518-guide-plan-master-full.md).
