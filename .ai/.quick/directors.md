# Director quick reference — free-text entry points

**When to open:** You have a goal in mind but don't know which Agent OS skill to invoke. Use a director to route for you.

---

## Which director?

| If your request is about… | Invoke |
|---------------------------|--------|
| Engineering, planning, coding, DB, dev stack | `@ai-director - <describe what you want>` |
| Spans engineering + UI + business | `@x-director - <describe what you want>` |

---

## Common free-text requests

```text
@ai-director - I need to add a users table to the database
  → @db-migration status → @db-migration create - add users table

@ai-director - Start building the authentication feature
  → checks implementation-ready → @code-implementation plan - M{N} → start

@ai-director - Audit the project plan before we start coding
  → @plan-verify foundation → @plan-verify master → @plan-verify alignment

@ai-director - Fix the gaps from the plan audit
  → @plan-repair repair - from <mode>

@ai-director - I'm not sure what to build first
  → @plan-foundation probe

@x-director - Build a signup feature with backend API and UI
  → @ai-director - create backend signup API with database schema
  → @ui-director - design and build signup UI screen

@x-director - Create a landing page for my business
  → @biz-director - strategy and brand for landing page
  → @ui-director - design and build landing page
```

---

## What the director does

1. **Captures** your exact wording.
2. **Loads** `{HANDOFF}` and `{ITERATION_CARRIER}` for context.
3. **Classifies** intent into a bucket (engineering, UI, business, cross-framework).
4. **Checks** prerequisite gates in `SKILL_DEPENDENCIES.md`.
5. **Invokes** the correct skill chain with canonical syntax.
6. **Records** the action in `{HANDOFF}` and updates `{ITERATION_CARRIER}` when the cycle advances.

---

## Syntax reminders

- ASCII hyphen `-` between verb and argument: `@code-implementation plan - M1`
- Free-text mode: `@ai-director - <anything>`
- Status mode: `@ai-director status`
- Help mode: `@ai-director help`

---

**Full protocol:** `skills/ai-director/skill.md` · `skills/x-director/skill.md`
