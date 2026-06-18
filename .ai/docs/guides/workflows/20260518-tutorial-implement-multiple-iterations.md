# Tutorial - multiple iterations to finish the current sub-plan

**Doc type:** Delivery loop tutorial (portable).  
**Skills:** `code-implementation` - `start`, `continue`, `task`, `complete`, `status` · `code-verify` - `milestone`, `uncommitted`, `last`.

---

## 1. Loop diagram

```text
plan - M{N}
       │
       ▼
    start ──► continue ──► … ──► @code-verify milestone ──► complete
       │           ▲                      │
       │           └──── task gate fail ─┘
       └────── status (any time)
```

---

## 2. First entry (`start`)

1. Valid `## Current iteration` exists ([checklist](20260518-tutorial-next-generate-new.md)).  
2. `@code-implementation start` - mandatory reads (NEXT, SPECs, CONVENTIONS, FEATURE_STANDARD, HANDOFF).  
3. First task → `in-progress`; implement; run **task gate** (tests + lint + type + secrets + protected files + scope).

---

## 3. Stepping tasks (`continue`)

| Invoke | Behavior |
|--------|----------|
| `@code-implementation continue` | Next **1** task (default) |
| `@code-implementation continue - 5` | Up to **5** tasks, or **stop early** on gate fail / blocker (same as "next 5 or until failed") |
| `@code-implementation continue - until blocked` | No task cap; stop on gate fail, blocker, or queue exhausted |
| `@code-implementation continue - M4-T2..T6` | Inclusive range in iteration order |

Per task in the batch:

1. Find `in-progress` or next `pending` in the queue.  
2. Implement **only** files listed on the task row.  
3. **Task gate** must pass before `done YYYY-MM-DD`.  
4. On pass, agent reports e.g. **`Batch 3/5: M4-T4 done`**.  
5. On gate **fail** or **blocked** → **stop the batch** (do not skip to the next queued task).  
6. Schema change? → `@db-migration`; batch stops unless user continues in the same message.  
7. End of batch: read **batch summary** in the skill report; optional `@code-implementation status`.

**Parallelism:** one active `in-progress` task at a time unless your team process explicitly allows parallel agents on disjoint file lists.

---

## 4. Mid-milestone verify (`@code-verify milestone`)

Run when:

- User asks; or  
- ≥80% tasks done; or  
- Contradiction suspected.

Produces **check matrix** (FR, SPEC rules, ADR, scope, schema, security, **tests**, observability, concepts, docs). Verdict **pass** | **pass with gaps** | **fail**. **Fail** → return to `continue` until fixed.

Optional: `@code-verify uncommitted` before commit · `@code-verify last` after commit/push.

---

## 5. Finish milestone (`complete`)

1. Run **CO2** `@code-verify milestone` if not run since last task - **pass** or **waived** in `{HANDOFF}`.  
2. **CO1** final gates: manual validation steps + concept registry; skip duplicate pytest/lint/type if CO2 shared gates already passed on current tree.  
3. `complete` updates: iteration status, **Done this iteration** table, **Recommended next**, `{HANDOFF}` produced artifacts.  
4. Draft **commit message** for human (per `.cursorrules` if present).

---

## 6. Next milestone (second “iteration” of the process)

`@code-implementation plan - M{N+1}` - new sub-plan. Repeat loop.

---

## 7. When the sub-plan is “too big”

If **L** tasks linger:

- Split milestone in **plan-master revise** (preferred), **or**  
- Add explicit **Owner blockers** and pause - do not invent scope cuts.

---

## 8. Session hygiene

`@session-control start` before a long coding day; `close` after - keeps `{HANDOFF}` honest about blockers and waivers.
