# End-to-end workflow - concepts, feature-centric delivery, skills, and agents

**Doc type:** Workflow guide (portable template).  
**Use:** Define how **feature work**, **architecture/NFR concepts**, **orchestration skills**, and **tooling agents** fit together in a repository. Copy to another project and fill the placeholders below first.

**Sibling guides:** [Workflow guides - artifact matrix](README.md) · [Workflows index - curriculum + principles](20260518-guide-workflows-index.md) (path bootstrap, tutorials, reference guides).

---

## Parameterize these placeholders (read before the rest)

Replace every token with your project’s real paths, filenames, and conventions. Until you do, treat paths in examples as **illustrative only**.

For a **copy-paste table** plus invocation sentence, use [Path bootstrap](20260518-tutorial-path-bootstrap.md) and paste the result into `{AGENT_RULES_FILE}`.

| Placeholder | Meaning | You must define |
|-------------|---------|-----------------|
| `{CONCEPTS_ROOT}` | Root directory of the **concept pack** (each concept: context `README` + executable `prompt.md`, optional ids like `MOD-xx`). | Yes |
| `{CONCEPTS_INDEX}` | Entry file listing concepts and how to consume them (often `{CONCEPTS_ROOT}/README.md`). | Recommended |
| `{SKILLS_ROOT}` | Root directory of **agent skills** (`skill.md` per skill, optional `reference.md`). | If you use skills |
| `{FEATURE_SPEC_ROOT}` | Where **feature specs** (or equivalent) live: scope, acceptance, domain invariants. | Yes |
| `{ITERATION_CARRIER}` | Where **implementation iterations** are tracked (`NEXT.md`, board, tracker export, etc.). | If you use iteration blocks |
| `{MASTER_PLAN}` | Approved roadmap (milestones, FR/NFR, acceptance). | Recommended |
| `{AGENT_RULES_FILE}` | Where **global agent/human rules** live (typically `.cursorrules` at repo root). | Recommended |
| `{BOUNDARY_MAP}` | Document that defines **hard module / package / service boundaries** for coupling reviews. | Strongly recommended |
| `{SESSION_HANDOFF_FILE}` | Optional file for **session open/close** and pick-up notes (if you use session bookends). | Optional |
| `{OBSERVABILITY_SPEC}` | Logging, metrics, traces, SLO conventions. | Recommended once code ships |
| `{EVIDENCE_TAGS}` | Allowed labels for uncertain numbers in plans (default: `measured` \| `estimated` \| `assumption` \| `unknown`). | Optional |

**Convention:** Any path in this guide written as `{…}` is a **placeholder**. Concrete paths appearing outside the placeholder table in your checkout are **examples** for that checkout only; other clones may differ.

---

## 1. Purpose

This guide describes a **project-agnostic** way to combine:

- **Feature-centric delivery** - what the product/domain requires.  
- **Concept packs** - reusable NFR/architecture procedures (coupling, latency, cost, ops load, modularity, AI blast radius, etc.).  
- **Skills** - repeatable orchestration (who reads/writes which canonical files, completion gates).  
- **Agents** - executors that follow a **single primary contract** (one skill or one prompt + links).

It deliberately does **not** require a specific stack, monorepo layout, or vendor tool.

---

## 2. What each layer owns (so nothing fights)

| Layer | Owns | Must not own |
|--------|------|----------------|
| **Feature-centric work** | *What* you build: problems, invariants, acceptance, boundaries of **product/domain** behavior. | Repo-wide orchestration mechanics (that belongs in **skills** and governance docs). |
| **Concepts** | *Cross-cutting NFR/architecture* rules and **prompt-sized procedures** with **fixed output shapes**. | Owning iteration file formats, milestone parsers, or “advance the sprint” unless promoted into a skill. |
| **Skills** | *Orchestration*: ordered steps, which **canonical** files to read/write, completion gates, invocation modes (`start` / `continue` / `close`, etc.). | Long philosophy; link to `{CONCEPTS_INDEX}` instead. |
| **Agents** | *Execution*: search, edits, commands, until a **stop condition** from the attached skill or prompt. | Implicit policy; always attach **one** primary contract. |

**Invariant:** Features answer **what is true in the domain?** Concepts answer **what must stay true in the system while we build?** Skills answer **how do we run the process?** Agents answer **who runs the tools?**

---

## 3. End-to-end workflow (agnostic shape)

**A. Intake (idea → scoped work)**  
- Feature track: proposal or issue → **feature spec** under `{FEATURE_SPEC_ROOT}` (or your equivalent).  
- In parallel, attach a **concept registry** for that work item: for each concept id you use, record **applies (yes/no)**, **owner**, **not applicable reason** when `no`.  
- Same work item carries **domain** responsibility and **NFR/architecture** responsibility.

**B. Planning (milestones)**  
- Milestones in `{MASTER_PLAN}` reference the feature spec **and** the concept registry row for that slice.  
- Architectural forks (new deployable, mesh, region, synchronous multi-hop chain) trigger the **relevant** `{CONCEPTS_ROOT}/*/prompt.md` runs; outputs attach to the planning artifact (ADR, design doc, ticket) with `{EVIDENCE_TAGS}` on every quantitative claim.

**C. Implementation iteration**  
- A **skill** (under `{SKILLS_ROOT}`) defines the iteration: load spec → tasks → per-task gates (tests/lint/type as **your** repo defines).  
- For AI-heavy or high-blast-radius tasks, run the **AI/coupling** concept prompts from the pack and attach results to the PR or `{ITERATION_CARRIER}` - keep procedures in **concepts** until you **promote** stable checks into the skill body.

**D. Verification / merge**  
- Skill **`@code-verify milestone`** (or equivalent): implementation vs feature spec **plus** rerun applicable concept procedures from the registry.  
- Include **observability / traceability** when code paths emit logs or spans ([Observability in workflow](20260518-guide-observability-traceability-in-workflow.md)).  
- Include **test suite gates** per [Testing in workflow](20260518-guide-testing-and-test-suite-in-workflow.md) (task gate + milestone verify matrix + complete protocol).  
- **CI automation** only for **objective** checks (forbidden imports, package fan-in limits). Subjective architecture review stays **prompt + human** until `{BOUNDARY_MAP}` exists.

**E. Session hygiene (optional)**  
- Session skill or habit: **open** = load what applies this cycle; **close** = which gates were satisfied, what debt remains (`{SESSION_HANDOFF_FILE}` if used).

---

## 4. Where to use skills vs prompts vs agents

| Mechanism | When to use |
|-----------|-------------|
| **Skill** | Repeated flow that must produce the **same artifact shape** every time (updated `{ITERATION_CARRIER}`, handoff file, completion checklist). |
| **Prompt** (from concepts) | One bounded review with a **fixed output skeleton**; paste into chat, PR template, or CI bot body. |
| **Agent** | Needs **many tool steps**; must run under **one** skill (“implement iteration X”) **or** **one** primary prompt (“audit this change for MOD-01 and MOD-06 only”) plus links to `{CONCEPTS_INDEX}`. |

**Rule of thumb:** Updates **official repo/process files** → skill. **One structured answer** → prompt. **Tool loop** → agent + single contract.

---

## 5. Making a checkout self-describing

Do **not** leave placeholders only inside this guide. After you decide paths:

1. Complete [Path bootstrap](20260518-tutorial-path-bootstrap.md).  
2. Paste the filled table + invocation contract into `{AGENT_RULES_FILE}` (and optionally one line in `{SESSION_HANDOFF_FILE}` Fresh start).  
3. Follow [Tutorial - full workflow](20260518-tutorial-full-workflow.md) once as a dry run.

The **workflow** in sections 2–4 stays stable; only the **registry** changes per project.

---

## 6. Implementation order (minimize thrash)

1. Stabilize **concept pack** under `{CONCEPTS_ROOT}`: each concept = `README` + `prompt.md`; index at `{CONCEPTS_INDEX}`.  
2. Extend the **feature spec template** with **§Concept / NFR registry** (applies, evidence, owner).  
3. Add an **invocation contract** in `{AGENT_RULES_FILE}` (see path bootstrap).  
4. Author `{BOUNDARY_MAP}` ([how-to](20260518-guide-boundary-map-howto.md)) so coupling and AI-blast-radius prompts can name boundaries instead of defaulting everything to `unknown`.  
5. Author or link `{OBSERVABILITY_SPEC}` before GA traffic.  
6. **Promote** only proven checks into **skills** (verify matrix, per-task gate).  
7. Add **CI** last, for machine-checkable rules only.

---

## 7. Staying feature-centric

You do **not** replace features with “architecture-only” work. You **bind** each feature (or milestone slice) to:

- Domain acceptance (unchanged), **and**  
- A **small explicit** set of concept obligations (which ids matter for *this* feature).

That preserves **stream-aligned ownership**, improves **maintainability** (fewer accidental cross-boundary edits), and improves **reliability under AI** (smaller blast radius, isolated tests) without mandating a particular deployment style (monolith vs services).

---

## 8. Optional: MOD registry snippet (for `{ITERATION_CARRIER}`)

If your iteration file is Markdown, you can add a subsection like:

```markdown
### Concept / NFR registry (this iteration)

| Concept id | Applies | Owner | Evidence / N/A reason | Status |
|------------|---------|-------|------------------------|--------|
| MOD-01 | yes/no | … | … | pending/done |
| … | … | … | … | … |
```

Concept ids and columns are **your** convention; rename if you do not use `MOD-xx`.

---

## 9. Observability and traceability (summary)

Treat observability as **first-class** in verify, not an afterthought: correlation IDs, stable log `event` names, trace parent/child relationships, and “no PII in logs” must align with `{OBSERVABILITY_SPEC}` and your security standard. Full checklist: [Observability in workflow](20260518-guide-observability-traceability-in-workflow.md).

---

## 10. Related locations (non-normative)

When bootstrapping a new adoption, typical paths are:

- Workflow index: `.ai/docs/guides/workflows/README.md` (**artifact matrix**) and `.ai/docs/guides/workflows/20260518-guide-workflows-index.md` (**curriculum**)  
- Concept pack: `.ai/concepts/README.md`  
- Skills: `.ai/skills/README.md`  
- Iteration carrier: `.work/plans/NEXT.md`  
- Master plan: `.work/plans/full/*-full-plan.md`  
- Handoff: `.work/context/HANDOFF.md`

When you copy this guide to another repository, **rewrite** section 10 with your own paths or delete it.
