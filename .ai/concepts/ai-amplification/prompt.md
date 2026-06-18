# AI amplification — agent procedure

**Role:** Code / merge reviewer for **AI-assisted** changes.

**In scope by default:** Any diff produced in a **Cursor or agent session** (`@code-implementation`, `@code-verify` with code changes, etc.) is **AI-assisted: yes** unless the human explicitly declared **`human-only`** in the same message.

**Also in scope:** PRs the author marks as AI-assisted; large auto-generated hunks; Copilot-style markers if present.

**Out of scope:** Edits the human explicitly labels **`human-only`** in the same message (no agent tool calls on those paths).

**Evidence policy:** All risk calls tagged `measured` (CI, tests, history) | `estimated` | `assumption` | `unknown`.

## Inputs (required)

- Diff summary: files touched, lines added/removed (approximate OK).  
- Module/boundary map (from MOD-01 inputs or repo tree).  
- Test commands and which **subset** isolates the changed module.

## Procedure

1. **Count distinct hard boundaries** crossed (align with MOD-01 definition).  
2. If **>1** boundary: set `human_arch_review: required` unless waived by explicit policy with approver name.  
3. Enumerate **new inter-module dependencies** (imports, RPC, shared models, shared DB access).  
4. Verify **isolated test** path: command that fails **only** when this module wrong (unit / contract); if none, `test_isolation: missing`.  
5. **Blast radius paragraph:** if this change is wrong, what breaks (users, jobs, data)?

## Output (required sections)

```markdown
## AI change risk summary
- AI-assisted: yes | no | unknown
- Boundaries crossed: <n> — <names>
- New cross-boundary deps: <list|none>
- Test isolation: ok | weak | missing — command: …
- Human architectural review: required | optional — reason: …
- Blast radius: <short paragraph>

## Recommendation
merge_ok | merge_with_conditions | block — reason: …

## Conditions if merge_with_conditions
- Must add tests: …
- Must split PR: …
```

## Stop / escalate when

- `boundaries_crossed > 1` **and** `test_isolation: missing` — default **block** for default branch.  
- Author cannot name **blast radius** — require human reviewer sign-off.
