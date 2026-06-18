# concept-run - reference

Supplement to `skill.md`. Invocation examples, concept mapping, trigger quick-reference, and edge cases.

---

## Invocation examples

### Cursor

```
@concept-run list
@concept-run status
@concept-run run - MOD-01
@concept-run - MOD-06
@concept-run run-all - pending
```

### Claude Code / opencode / Codex

```
Follow .ai/skills/concept-run/skill.md - list. Read-only.
```

```
Follow .ai/skills/concept-run/skill.md - run - MOD-06.
Execute the AI-amplification prompt and attach output to the PR or iteration Notes.
```

```
Follow .ai/skills/concept-run/skill.md - run-all - pending.
Run each pending applicable concept in the current iteration registry.
```

---

## Mode comparison

| | list | status | run | run-all |
|---|---|---|---|---|
| Read concept README/prompt.md | no | no | yes | yes |
| Read NEXT.md iteration registry | no | yes | yes | yes |
| Write output to artifact | no | no | yes | yes |
| Update registry Status | no | no | yes | yes |
| Completion checklist | no | no | yes | yes |

---

## Concept mapping (quick)

| Trigger | MOD id | Folder | Required? |
|---------|--------|--------|-----------|
| Splitting packages, changing imports across contexts | MOD-01 | `coupling-audit/` | Recommended |
| Adding sync-call chains, latency-critical paths | MOD-02 | `network-cost/` | Recommended |
| Adding billable deploy units, new services | MOD-03 | `cost-model/` | Recommended |
| Changing ownership, on-call surface, service ratio | MOD-04 | `ops-headcount/` | Recommended |
| Extracting a package, changing modular boundaries | MOD-05 | `modularity-vs-distribution/` | Recommended |
| `@code-implementation` in Cursor/agent session (code touched) | MOD-06 | `ai-amplification/` | **Required** - default **AI-assisted: yes**; **`human-only`** opt-out only |

The authoritative trigger table is in `.ai/concepts/README.md` § Trigger table. The above is a quick reference.

---

## Output attachment by trigger

| Trigger | Output goes to |
|---------|---------------|
| SPEC §15 creation | SPEC §15 Concept / NFR registry |
| `plan` (iteration) block | `NEXT.md` iteration `### Concept / NFR registry` → task Notes column |
| `@code-implementation` session (code touched) | PR description, task `Notes`, or iteration registry |
| `@code-verify milestone` | Verify report § Concept / NFR registry row |

---

## Edge cases

| Situation | Behavior |
|-----------|----------|
| Concept pack missing (no `.ai/concepts/`) | `list` reports `N/A - no pack`; `run` refuses with instructions |
| `prompt.md` not found for MOD id | Report gap; suggest owner create the missing prompt |
| Required input missing (e.g. no diff for MOD-01) | Ask user once for the missing input; do not invent |
| `run-all - pending` finds no pending rows | Report `nothing to run` and suggest `@concept-run list` |
| Quantitative claim without evidence tag | Reject the claim; restate with `estimated` or `assumption` |
| MOD-03 invoked for task that adds no billable units | Mark `N/A` in output with reason; do not fabricate cost lines |
| `Status=gap` rows found | Treat as resolved - do not re-run unless user asks |
| Agent session with code changes but MOD-06 skipped | **fail** in `@code-verify milestone`; re-run before **complete** |

---

## Integration with code-implementation task gate

When the task gate's manual "Also verify" section flags a concept requirement:

1. Stop the task gate.
2. Run `@concept-run run - MOD-{N}` for the relevant concept.
3. Attach output to the task Notes column in `NEXT.md`.
4. Update the iteration registry `Status` row to `done YYYY-MM-DD`.
5. Resume the task gate.

Per `code-implementation` CO1, unresolved `Applies=yes` concept rows block milestone completion.

---

## Integration with feature-spec

When `@feature-spec create` or `review` needs §15 populated:

1. Run `@concept-run list` to see which concepts apply to this feature.
2. Run `@concept-run run - MOD-0N` for each applicable concept.
3. Populate §15 with the output skeleton.

---

## Anti-patterns

- Running `run-all` across all MOD ids when the trigger table says only 2 apply.
- Attaching MOD-06 output without actually following the prompt procedure.
- Using `measured` without a measurement source.
- Editing `prompt.md` files to "fix" a failing concept check.

---

## Wrong prompts

| Prompt | Problem | Use instead |
|--------|---------|-------------|
| `@concept-run run` (no MOD id) | No target | `@concept-run list` first, then pick |
| `@concept-run run - MOD-07` | No such concept | `@concept-run list` for valid ids |
| `@concept-run` with no concept pack | Nothing to run | Report and skip; do not fabricate |
| Skipping MOD-06 on agent/Cursor diffs | Violates Required trigger | Run before `@code-implementation complete`; default AI-assisted |
