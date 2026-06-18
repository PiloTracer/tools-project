# plan-repair - reference

Supplement to `skill.md`. Invocation examples and source-mode mapping.

---

## Invocation examples

### After plan-verify failure

```text
@plan-verify foundation
@plan-repair repair - from foundation
```

```text
@plan-verify master
@plan-repair repair - from master
```

```text
@plan-verify alignment
@plan-repair repair - from alignment
@plan-repair repair - from coverage
```

### Explicit goal (open language)

Free-text requests decompose into a **Framework alignment map** (R0-free in `skill.md`) before the F* table. The map identifies which `.ai` standards, concepts, SPECs, and docs each phrase implicates.

```text
@plan-repair foundation - we will require multi-tenant row-level security in v1
@plan-repair master - adjust M2 to split observability from domain API tasks
@plan-repair repair - master - add FR18 for export audit trail
```

**Alignment flow (free requests):**

```text
1. Free request (open language, goal text after -)
2. R0-free: Framework alignment map → standards, concepts, SPECs, foundation/master docs
3. F* table with Framework ref column
4. Repair plan cross-checked against alignment map
5. Delegate commands to upstream skills
6. Mandatory re-verify
```

When the request maps cleanly to framework components, the `Framework ref` column connects each F* row to the target standard, concept id, or plan section.

### Brownfield (no formal plan-foundation / plan-master — framework align)

Synthesizes `.work/plans/` from README, code, ROADMAP, ADRs. Does **not** require prior `@plan-foundation greenfield`.

```text
@plan-verify brownfield
@plan-repair brownfield
@plan-verify brownfield

@plan-repair brownfield - foundation    # foundation slots only
@plan-repair brownfield - master        # master + minimal foundation
```

### Default / status

```text
@plan-repair
@plan-repair repair
@plan-repair status
```

### Custom brief

```text
@plan-repair repair - custom - fix doc 04 bounded context list to match apis/ folders; update DIRECTORY_MAP
```

---

## Source → re-verify map

| Invocation | Run first (if no report) | Re-run after fix |
|------------|--------------------------|------------------|
| `from foundation` / `foundation` | `@plan-verify foundation` | `@plan-verify foundation` |
| `from master` / `master` | `@plan-verify master` | `@plan-verify master` |
| `from alignment` | `@plan-verify alignment` | `@plan-verify alignment` |
| `brownfield` | `@plan-verify status` | `@plan-verify foundation` (+ `master` when ready) |
| `custom` | (brief) | Modes in brief + minimum one verify pass |

---

## Delegate commands (quick reference)

| Need | Command |
|------|---------|
| Resume foundation phase | `@plan-foundation continue` |
| Certify for master plan | `@plan-foundation certify plan-master-ready` |
| New master plan | `@plan-master greenfield` |
| Resume draft master plan | `@plan-master continue` |
| Structured master delta | `@plan-master revise - <reason>` |
| Integrity re-check | `@plan-master integrity` |
| Regenerate NEXT block | `@code-implementation plan - M{N}` |
| Scaffold `.work/` | `@project-bootstrap init` |

---

## plan-repair vs upstream skills

| Situation | Use |
|-----------|-----|
| Single phase gate during greenfield | `@plan-foundation continue` (direct) |
| Multi-gap verify fail report | `@plan-repair repair - from foundation` |
| One clear master plan change | `@plan-master revise - …` or `@plan-repair master - …` (repair coordinates + re-verify) |
| Repo has code, no foundation 01–04 | `@plan-repair brownfield - foundation` |
| Test/lint fail | `@code-repair` (not plan-repair) |

---

## Wrong prompts

| Prompt | Problem | Use instead |
|--------|---------|-------------|
| `@plan-repair` with no findings or goal | No F* table | `@plan-verify` first or paste report |
| **repaired** without verify | Violates skill | R4 mandatory |
| Fix pytest failure | Wrong layer | `@code-repair` |
| Skip certify before master greenfield | PG1 blocked | `@plan-foundation certify` |
| Free request without R0-free alignment map | No framework traceability | Decompose into R0-free before F* table; label Framework ref per finding |
