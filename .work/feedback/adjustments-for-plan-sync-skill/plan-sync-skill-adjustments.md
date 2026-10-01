# Adjustments for the `@plan-sync` skill — instructions for the Agent OS framework

**Audience:** the `pilo.ai.logicbison` (Agent OS) framework maintainer / agent operating that repo.
**Requested by:** tools-project owner · **Date:** 2026-09-30
**Scope:** framework-side only (`skills/plan-sync/skill.md`). Do **not** edit the tools-project repo
from the framework: the skill's only write stays the single `POST …/plan-import` call.
**Status of the tools-project side:** already handled (see §6) — the API, the UI and the SPEC
amendment are not part of this request.

---

## 1. Why — the observed problem

A real production sync of the Mendarion master plan produced **159 tasks in 12 milestones**. It
works, but the tasks are unreadable at a glance. Two samples from production
(`GET /v1/agent/projects/{id}/context`, read-only):

| field | value |
|---|---|
| `ref` | `MDR-159` |
| `title` | `**Enterprise customization cascade (T3, ADR 020)** — the \`location\` scope layer (org default → practice → clinic) resolves in one order` |
| `description` | `## Acceptance\nA lower scope cannot override an org safety floor; a blueprint import carries no PHI and lands disabled\n\n---\n**Provenance:** plan_ref=M12-T15, source=.work/feedback/plans-import/plans/20260925-full-plan.md, plan_version=1.6, files=\`customization/**\`, \`platform/\`, fr_nfr=**FR26**, NFR19, complexity=L` |

Three defects, all skill-side:

1. **The title is a paragraph.** The plan's task cell is a full engineering sentence, so lists,
   boards and search results show walls of text that only the plan's author can skim.
2. **No plain-language summary exists anywhere.** Nothing in the task says *what it delivers* in
   one sentence a non-author can read.
3. **The provenance block is a prose line, not a structure.** `---` + `**Provenance:** k=v, k=v…`
   is hard to render as fields (commas inside backticked values, mixed bold markers) and it does
   not match the SPEC's own wording (`## Source`), i.e. SPEC and implementation have drifted.

The tools-project UI now compensates for all three by parsing the legacy shape (§6), so this is a
*quality* request, not a blocker. Fixing it in the skill is what makes **future** imports clean and
lets the UI drop its compatibility branch.

---

## 2. Required change — one description format, three stable blocks

Compose every imported task's `description` as exactly these three headings, in this order, with
no `---` rule and no inline `**Provenance:**` line:

```markdown
## Intent
<one plain-language sentence: what this task delivers, in the plan's own words where possible>

## Acceptance
- <criterion 1>
- <criterion 2>

## Technical details
- plan_ref: M12-T15
- plan_version: 1.6
- source: .work/feedback/plans-import/plans/20260925-full-plan.md
- files: customization/**, platform/
- traces: FR26, NFR19
- complexity: L
```

Rules:

| # | Rule |
|---|---|
| A1 | Heading names and order are **fixed**: `## Intent`, `## Acceptance`, `## Technical details`. Downstream parsers key on them. |
| A2 | `## Acceptance` items are **one bullet per criterion** — split the plan cell on `;` and on sentence boundaries instead of emitting one run-on line. Never drop a criterion. |
| A3 | `## Technical details` is a **bullet list of `- key: value` pairs**. Keep the exact keys `plan_ref`, `plan_version`, `source`, `files`, `traces`, `complexity` (rename `fr_nfr` → `traces`; keep FR/NFR ids verbatim, comma-separated). |
| A4 | Values stay **verbatim and lossless**: `plan_ref`, `source`, `plan_version`, FR/NFR ids, file globs and complexity must survive exactly as in the plan. No truncation, no re-wording of technical values. |
| A5 | `## Intent` is derived, never invented: take the plan row's own words (its first clause / goal). If the plan offers no separable summary, use the first clause of the cell after the leading bold label. |
| A6 | Omit a block **only** when it has no content (`## Technical details` may be absent for plan rows with no provenance; `## Acceptance` may be absent when the plan records none). Never emit an empty heading. |

### Task title rule

`title` = the **short human label**, ≤ 120 characters, no markdown emphasis markers
(`**`, `__`, backticks), no trailing ellipsis-padding:

| before | after |
|---|---|
| `**Enterprise customization cascade (T3, ADR 020)** — the \`location\` scope layer …` | `Enterprise customization cascade (T3, ADR 020)` |
| `Provision repo layout exactly as \`DIRECTORY_MAP\` §2 (contexts named, staged packages empty)` | unchanged (already a single clause) |

The remainder of the cell (the technical sentence, the `(T3, ADR 020)`-style references, the
`DIRECTORY_MAP §2` detail) moves into `## Intent` / `## Technical details`, so nothing is lost.
Keep the plan's `plan_ref` and the migrated identifiers exactly as today.

### Milestone rule

Populate the milestone's `summary` with **one plain sentence** (the plan's milestone heading or
its goal line) — tools-project already renders `summary` under the milestone name, and today most
imported milestones have `summary = NULL`.

### Manifest envelope — unchanged

`manifest_version: 1` stays as-is, including `project`, `milestones[]`, `tasks[]`, `components[]`
and the existing per-item fields. This request changes only **how the text fields are composed**;
no new keys, no version bump (the endpoint validates the same schema).

---

## 3. Back-compat and migration

- **Existing rows fix themselves**: tools-project imports match on `(plan_id, plan_ref)` and
  *refresh* `title`, `description`, `summary` and content fields on match
  (`api/app/services/plan_import.py`, SPEC R13 — local `status` is preserved, nothing else is
  frozen). So after this skill change, the next `sync` of the same plan rewrites the 159 existing
  tasks into the new format. **No manual migration, no re-import from scratch, no data loss.**
- Until that sync happens, both shapes coexist. tools-project's UI already parses the legacy shape
  (§6), so mixed states render correctly.
- The skill must keep working against a tools-project that predates the friendly UI — it does:
  the API stores whatever text the manifest carries.

---

## 4. Files to change (framework repo)

| File | Change |
|---|---|
| `skills/plan-sync/skill.md` | Compose `description` per §2; add the title rule; add the milestone `summary` rule; update the embedded manifest example and the "what the operator sees" preview text so the preview shows the friendly title + acceptance list |
| `skills/SKILL_DEPENDENCIES.md` (row `plan-sync`) | No gate change expected — mention the title/description rules only if the row describes outputs |
| `skills/README.md` (row `plan-sync`) | Optionally note "composes an Intent / Acceptance / Technical-details description" |

No other framework file is touched. Do not add write tools to the read-only MCP
(`.opencode/mcp/project-mcp`), do not add endpoints, do not read the tools-project database.

---

## 5. Acceptance test for the framework team (no tools-project access needed)

1. Take any plan file with the documented columns and an "Acceptance"/verification cell.
2. Run the skill's `dry-run` path against a **test** tools-project project (or inspect the manifest
   it would send) and check the payload:
   - every task `description` starts with `## Intent` and contains `## Acceptance` bullets;
   - no `**Provenance:**` and no `---` line anywhere;
   - `## Technical details` is a `- key: value` list with the six keys where applicable;
   - every task `title` is ≤ 120 chars, single clause, no `**`;
   - milestone `summary` is non-empty.
3. Diff one task before/after: no technical value (`plan_ref`, `source`, `plan_version`, FR/NFR,
   files, complexity) may be lost — only re-segmented.

---

## 6. Tools-project side — already done (do not re-implement)

Shipped 2026-09-30 (`web/`), and it accepts **all three** shapes: the legacy inline provenance,
a `## Source` heading, and the new `## Technical details` list.

| Piece | Where |
|---|---|
| Tolerant parser (label from the title's first clause; acceptance → checklist; provenance → structured fields; raw text fallback) | `web/src/shared/plan-text.ts` |
| Friendly renderer ("What this delivers" + "Done when:" + collapsed *Technical details (plan source)* + *Original stored description*) | `web/src/components/PlanTaskBody.tsx` |
| Tasks grouped by milestone, milestone/plan-state filters, deep links (`?milestone=<id>`, `?plan_state=`) | `web/src/app/projects/[id]/tasks/…` |
| Milestone list with progress bars on the project page | `web/src/app/projects/[id]/page.tsx` |

The SPEC amendment that makes this format official (tools-project-owned, SPEC R21) is handled on
the tools-project side; this file is the framework-side work order only.
