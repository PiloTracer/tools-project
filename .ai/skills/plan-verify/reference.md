# plan-verify - reference

Supplement to `skill.md`. Invocation examples and mode picker.

---

## Invocation examples

```text
@plan-verify brownfield               # full framework alignment (no prior formal plan-foundation/master)
@plan-verify foundation
@plan-verify master
@plan-verify alignment
@plan-verify coverage                 # app surfaces vs SPECs / DIRECTORY_MAP
@plan-verify registry                 # alias: coverage
@plan-verify drift                    # alias: alignment
@plan-verify status
@plan-verify                          # default: brownfield if code-first repo; else alignment / master / foundation
```

Open language (agent maps to mode; emits **Request interpretation** block before running):

```text
@plan-verify - audit foundation docs for plan-master-ready
@plan-verify - is our master plan ready for implementation?
@plan-verify - check NEXT against the full plan for M2
@plan-verify - align existing repo to Agent OS without plan-foundation greenfield
@plan-verify - find unmapped dashboard pages and API routes
@plan-verify coverage - audit code-to-feature registry before M2
```

**Interpretation flow (free requests):**

When the user does not provide an explicit mode keyword, the agent:
1. Detects keywords or intent from the free text
2. Maps to the closest framework mode (foundation, master, alignment, brownfield, status)
3. Emits a **Request interpretation** block showing the mapping before running the protocol
4. Labels the mapping **Confirmed** (unambiguous) or **Inference** (needs user confirmation)

The interpretation block appears in the verification report header. For explicit-mode invocations (e.g. `@plan-verify foundation`), the block records `explicit mode — no interpretation needed`.

---

## Brownfield (no formal plan-foundation / plan-master)

Use when the repo has **code or legacy docs** but never ran `@plan-foundation greenfield` or `@plan-master greenfield`.

```text
@plan-verify brownfield
@plan-repair brownfield
@plan-verify brownfield          # re-verify after repair
```

**Readiness labels (brownfield — not formal certify):**

| Label | Meaning |
|-------|---------|
| **brownfield-aligned** | ≥70% framework slots covered (canonical or substitute) |
| **brownfield-partial** | 40–69%; repair can continue |
| **formal-plan-master-ready** | Requires `@plan-foundation certify` — separate from brownfield-aligned |

---

## Mode picker

| Situation | Mode |
|-----------|------|
| Before `@plan-foundation certify` | **foundation** |
| Before `@plan-master greenfield` / after foundation change | **foundation** |
| Before approving master plan / broad coding | **master** |
| Before `@code-implementation complete` (plan slice) | **alignment** + **code-verify milestone** |
| NEXT tasks do not match plan §19 | **alignment** |
| Brownfield / legacy repo, no formal planning run | **brownfield** first |
| Brownfield repo, unknown planning state | **brownfield** → **foundation** → **master** → **alignment** |
| Quick "what should I verify?" | **status** |

---

## Typical flows

**Foundation not ready for master plan:**

```text
@plan-verify foundation
@plan-repair repair - from foundation
@plan-verify foundation
@plan-foundation certify plan-master-ready
```

**Master plan wrong or stale:**

```text
@plan-verify master
@plan-repair master - adjust checkout flow for guest users
@plan-verify master
```

**NEXT and full plan out of sync:**

```text
@plan-verify alignment
@plan-repair master - reconcile M2 task ids with FR12
@code-implementation plan - M2
@plan-verify alignment
```

**Brownfield adopt (code-first repo):**

```text
@plan-verify brownfield
@plan-repair brownfield
@plan-verify brownfield
# optional formal path later:
@plan-foundation certify plan-master-ready
@plan-master continue
```

**Verify then repair (symmetric to code layer):**

```text
@plan-verify foundation
# … fail …
@plan-repair repair - from foundation
```

---

## Mapping to legacy skill verbs

| plan-verify | Closest legacy |
|-------------|----------------|
| foundation | `@plan-foundation status` + `@plan-master integrity` (foundation scope) |
| master | `@plan-master status` + `@plan-master integrity` |
| alignment | Tutorial `20260518-tutorial-fix-existing-plans.md` |

plan-verify **does not replace** `certify`, `continue`, `greenfield`, or `revise` — it **audits** and routes to **plan-repair** or upstream skills.

---

## Wrong prompts

| Prompt | Problem | Use instead |
|--------|---------|-------------|
| `@plan-verify` then edit SPECs inline | Verify is read-only | `@plan-repair foundation - …` |
| Expect implementation-ready from foundation mode | Wrong layer | `@plan-verify master` |
| Fix code test failures | Wrong layer | `@code-verify` / `@code-repair` |
| Open-language verify without interpretation block | No framework traceability | Emit **Request interpretation** before protocol; label mapping Confirmed / Inference |
