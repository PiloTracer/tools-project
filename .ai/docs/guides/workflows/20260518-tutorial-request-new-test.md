# Tutorial - request a **new** test (no code yet)

**Doc type:** Change-request tutorial (portable).  
**Goal:** Get a **test artifact** scheduled (file + task + owner) without mixing “random test idea” into production code unplanned.

---

## 1. Pick the intake channel

| Channel | Best for |
|---------|----------|
| **Tracker ticket** (GitHub Issue / Jira / Linear) | Visibility, prioritization, SLA |
| **`UNKNOWNS.md` or `RISK_REGISTRY.md`** | Blocks release until answered |
| **Amendment to feature SPEC §12 Test plan** | Behaviour already Approved; test gap found late |

---

## 2. Minimum ticket content (copy template)

```markdown
## Test request

**Type:** unit | contract | integration | e2e | performance | security
**Feature / bounded context:** <name>
**SPEC rules covered:** R…
**Why now:** <regression risk / new path / bug escape>
**Acceptance:** <given/when/then or assertion list>
**Data:** synthetic fixtures only - describe
**Owner:** <role>
**Suggested path:** <e.g. tests/unit/foo/test_bar.py>
**Non-goals:** …
```

---

## 3. Planning linkage

1. If the test belongs to **current milestone** - add a **task row** to `{ITERATION_CARRIER}` (or split existing task) with file path to new test.  
2. If it belongs to **later** work - add to `{MASTER_PLAN}` validation section or next milestone notes via **plan-master revise** (human-gated).  
3. If it **blocks** correctness - mark **Owner blockers** in iteration until task exists.

---

## 4. Agent / human assignment

Paste into agent chat:

```text
Implement test only: <path>. Cover SPEC R… . Do not change production code unless the test exposes a real bug - then stop and report.
```

Attach **feature SPEC** path and **CONVENTIONS** test layout section.

---

## 5. Definition of done for the request

- [ ] Test file merged.  
- [ ] Task gate / CI green.  
- [ ] SPEC test plan row references new test name or file (amendment if SPEC was Approved).

---

## 6. Anti-patterns

- “Add tests someday” with no owner.  
- Integration test that needs **production** credentials - use sandbox per runbook.
