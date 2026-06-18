# Minimal adoption (lite path)

Agent OS supports two adoption depths. Use **lite** when you need session memory and agent discipline quickly; use **full** when you are greenfielding a product with foundation docs and a master plan.

---

## Full pipeline (recommended for new products)

```text
@project-bootstrap init
@plan-foundation greenfield
@plan-foundation certify plan-master-ready
@plan-master greenfield
@plan-master status                    # implementation-ready: yes
@session-control start
@code-implementation plan - M1
@code-implementation start → continue
@code-verify milestone
@code-implementation complete
@session-control close
```

Gates, artifacts, and readiness states: [`README.md`](../../README.md) · [`skills/SKILL_DEPENDENCIES.md`](../../skills/SKILL_DEPENDENCIES.md).

---

## Lite path (existing repo, fast start)

**Goal:** `.cursorrules` + `.work/` session files + daily bookends - **without** waiting for foundation 01–04 or an approved master plan.

| Step | Action |
|------|--------|
| 1 | `bash .ai/templates/bootstrap.sh` (or `@project-bootstrap init`) |
| 2 | Fill **`REPLACE:`** tokens in `.cursorrules` and `DOCS_TECH_STACK.md` |
| 3 | Copy/customize standards under `.ai/standards/` |
| 4 | `@session-control start` every session |
| 5 | Maintain `.work/plans/NEXT.md` **Recommended next** manually (or a single milestone you define) |
| 6 | For each coding task: read relevant SPEC if it exists; run test/lint/type from `.cursorrules` before claiming done |
| 7 | `@session-control close` |

**What you skip (and trade off):**

| Skipped | Risk |
|---------|------|
| `@plan-foundation greenfield` | No shared P0 scope doc; agents may invent scope |
| `@plan-foundation certify` | No **plan-master-ready** gate |
| `@plan-master` + **implementation-ready** | `@code-implementation start` may **block** unless you add a HANDOFF waiver or complete the master plan later |
| `@code-verify milestone` | Weaker milestone audit |

**Unblocking coding without a master plan:** Document in `.work/context/HANDOFF.md` which milestone(s) may proceed (e.g. "M1 platform skeleton waived until master plan approved"). `code-implementation` honors explicit HANDOFF waivers per its skill.

---

## When to upgrade lite → full

- Multiple contributors or agents disagree on scope
- You need FR/NFR traceability and milestone **M1…M9** from a single approved plan
- `@code-implementation` blocks repeatedly on **implementation-ready**

Run `@plan-foundation greenfield` then `@plan-master greenfield` when ready; keep existing `.work/` files - skills merge/update rather than replace blindly.

---

## Verification after bootstrap

```bash
bash scripts/smoke-consumer.sh      # local consumer layout check
bash scripts/framework-verify.sh  # full framework checks (also runs in CI)
```

---

## Path convention

| Layout | Agent OS location | Example: START_HERE |
|--------|-------------------|---------------------|
| **Nested** (typical app repo) | `your-app/.ai/` | `.ai/START_HERE.md` |
| **Self-hosted** (this framework repo) | git root *is* the tree | `START_HERE.md` |

Same content; prefix `.ai/` only when Agent OS is a subfolder.
