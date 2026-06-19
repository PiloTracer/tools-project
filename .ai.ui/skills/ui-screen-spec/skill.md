---
name: ui-screen-spec
description: >-
  Author, review, amend screen SPECs per SCREEN_SPEC_STANDARD under .work.ui/screens/,
  or triage a free-text UI request (intake). Use intake - <sentence>, create - <slug>,
  review - <path>, amend - <slug>, status.
---

# ui-screen-spec

**Path (mandatory):** `<repo-root>/.work.ui/screens/<slug>/YYYYMMDD-SCREEN-SPEC.md`  
Placeholder: `{SCREEN_SPEC_ROOT}/<slug>/YYYYMMDD-SCREEN-SPEC.md`

**Template source (copy only):** `.ai.ui/templates/work.ui/screens/example-slug/YYYYMMDD-SCREEN-SPEC.md.template`

**Standards:** `SCREEN_SPEC_STANDARD` · `SURFACE-AND-CONTROL-CRAFT` · `examples/<folder>/manifest.md`

## Modes

| Mode | Action |
|------|--------|
| `intake - <free sentence>` | Classify a free-text UI request → route to the right executor |
| `create - <slug \| free-text>` | New SPEC from template; derives slug if given a sentence; pattern extraction below |
| `review - <path>` | Checklist against SCREEN_SPEC_STANDARD + craft gates |
| `amend - <slug>` | Amendment file; do not edit Approved SPEC in place |
| `status` | List SPECs by status |

## Prerequisites

- **screen-spec-ready: yes** from `@ui-design-foundation certify` (or HANDOFF_UI waiver)

## intake — free-text front door

Classify one unstructured UI request, route it, and record it so nothing is lost. **Never auto-executes** the gated paths.

1. **CLASSIFY** by blast radius (first match wins):

| Signal | Class | Route to |
|--------|-------|----------|
| No UI foundation yet (`screen-spec-ready: no`) | **brownfield** | `@ui-design-foundation greenfield` (or `probe`), then re-run intake |
| Vague look/scope, no measurable outcome | **underspecified** | `@ui-design-foundation probe`, then re-classify |
| Cross-cutting: new tokens, primitives, or affects many screens | **cross-cutting** | `@ui-design-system init` / `@ui-design-foundation` (tokens), then `plan` |
| One screen/flow, uses existing tokens & primitives | **local** | continue into `create` (derive slug) |

Override: `@ui-screen-spec intake - <sentence> ; force=<class>`.

2. **ROUTE** — state the class + the single next command; only `local` proceeds into `create`.
3. **RECORD** — append to `{UI_ITERATION_CARRIER}` under `## Intake queue` (seeded in the NEXT_UI template): `- <YYYY-MM-DD> · <class> · "<sentence>" → <next command>`. Underspecified + owner away → also `{UI_PLANS_ROOT}/UNKNOWNS.md`.

## create — pattern extraction

**Free-text slug:** if the arg after `-` is a sentence (not kebab-case), propose a derived slug (e.g. *"a page to manage team members"* → `team-members`), state it, and carry the sentence into SPEC §1 Summary. Explicit kebab-case slug → skip.

Follow [`examples/INDEX.md`](../../examples/INDEX.md) § playbook (Phases A–C). On `create`: copy manifest **extractedRules** → §11 + §13; **primitives** → §8; add UIS-07 when craft tier ≥ refined.

## Hard rules

- No API schema duplication — link `.work/features/` SPECs
- §12 UIS registry mandatory before `Approved`
- §13 **exampleIds** + **extractedRules** mandatory when craft tier ≥ refined (or N/A waiver in HANDOFF_UI)
- §8 must not allow native range/select/checkbox on primary flows if §13 cites examples requiring catalog primitives — unless `native allowed` waiver per row

## review checklist (additions)

- [ ] §13 shape matches SCREEN_SPEC_STANDARD §5
- [ ] §11 includes manifest extractedRules
- [ ] §8 catalog status consistent with CATALOG.md
- [ ] Invalid: cites `mobile-controls/C1` but native `<input type="range">` without waiver

## Approval

Only human or explicit user message may set `Status: Approved`.

**Do not** `@ui-component-build plan` screen tasks until **Approved** and P0 primitives **done** (or documented waiver).
