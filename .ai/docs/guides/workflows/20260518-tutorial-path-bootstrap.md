# Path bootstrap - fill placeholders once per clone

**Doc type:** Operational checklist.  
**Portability:** The **left column** is generic. The **right column** is an **example fill-in** for one sample layout (multi-service backend + `.ai/` governance). Replace the right column in **your** canonical map (often `{AGENT_RULES_FILE}`).

---

## 1. Copy this table to your canonical rules file

After filling, every human and agent reads **one** table instead of hunting paths.

| Placeholder | Meaning | Example fill-in (replace in your clone) |
|-------------|---------|----------------------------------------|
| `{CONCEPTS_ROOT}` | Concept pack root (`README` + per-concept `prompt.md`) | `.ai/concepts/` |
| `{CONCEPTS_INDEX}` | Pack index | `{CONCEPTS_ROOT}/README.md` |
| `{SKILLS_ROOT}` | Skills registry | `.ai/skills/` |
| `{WORK_ROOT}` | Project working tree | `.work/` |
| `{PLANS_ROOT}` | Plans directory | `.work/plans/` |
| `{FEATURE_SPEC_ROOT}` | Feature specs | `.work/features/` |
| `{PROMPTS_ROOT}` | Project prompts | `.work/prompts/` |
| `{DECISIONS_ROOT}` | ADRs | `.work/decisions/` |
| `{ITERATION_CARRIER}` | Active iteration / backlog file | `.work/plans/NEXT.md` |
| `{MASTER_PLAN}` | Approved roadmap (milestones, FR/NFR) | `.work/plans/full/*-full-plan.md` (pick latest Approved) |
| `{HANDOFF}` | Session / pick-up file | `.work/context/HANDOFF.md` |
| `{BOUNDARY_MAP}` | Module / package boundary contract | *(author per* [Boundary map how-to](20260518-guide-boundary-map-howto.md)*)* - e.g. extend your directory map |
| `{OBSERVABILITY_SPEC}` | Logging, metrics, trace fields | e.g. `.ai/standards/*observability*.md` if present |
| `{AGENT_RULES_FILE}` | Global agent rules | `.cursorrules` (do not add `AGENTS.md` without owner approval) |

---

## 2. Invocation contract (single sentence)

Paste under the table in `{AGENT_RULES_FILE}`:

> **Concept workflow:** For each change or milestone slice, list applicable architecture concept ids (from `{CONCEPTS_INDEX}`), run the matching `prompt.md` procedures, attach outputs to the PR or `{ITERATION_CARRIER}`, and tag quantitative claims with `{EVIDENCE_TAGS}`.

Default evidence tags: `measured` | `estimated` | `assumption` | `unknown`.

---

## 3. Verify the map

- [ ] Every path in the table opens in the repo.  
- [ ] `{MASTER_PLAN}` points at a document whose **status** is Approved (or your waiver process is documented in `{HANDOFF}`).  
- [ ] `{ITERATION_CARRIER}` contains or will contain a **Concept / NFR registry** subsection for the active iteration (see [End-to-end workflow](20260518-guide-end-to-end-workflow.md) section 8).  
- [ ] `{BOUNDARY_MAP}` either exists or is explicitly **deferred** with owner and date (coupling prompts will return `unknown` until it exists).

---

## 4. Optional: second clone / fork

When you fork the repo, **re-validate** the right column. Do not assume paths from upstream match your org’s layout.
