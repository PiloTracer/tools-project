# Boundary map how-to + template

**Doc type:** Guide + template.  
**Why:** Coupling audits and AI blast-radius checks need a **shared definition** of “module” or “hard boundary.” Without it, reviewers output `unknown` for boundary counts.

---

## 1. What a boundary map is

A **boundary map** is a human- and machine-readable table that answers:

- What are the **top-level deployable or importable units**?  
- Who **owns** each unit?  
- Which **imports or calls are allowed** vs **forbidden** across units?

It is **not** a copy of your entire directory tree - only **edges** that must not be crossed without review.

---

## 2. Authoring steps (any project)

1. List **candidate boundaries** (packages, apps, services, or layers your team treats as separate ownership).  
2. For each pair `(A → B)`, mark **allowed**, **forbidden**, or **allowed with adapter** (port/hexagon).  
3. Add an **owner** (team or role) per boundary.  
4. Link to **enforcement**: CI import rules, ArchUnit, `ruff`/`eslint` boundaries, or `skip - manual review only` if not automated yet.  
5. Version the map (`**Updated:**` date); append rows instead of silent deletes.

---

## 3. Template (copy into `{BOUNDARY_MAP}`)

```markdown
# Module boundary map - <Project>

**Updated:** <YYYY-MM-DD>  
**Status:** Draft | Active  
**Source of truth for:** coupling audits, AI change blast radius, import lint config.

## Top-level boundaries

| Unit id | Path / package pattern | Owner team / role |
|---------|-------------------------|-------------------|
| U1 | `<example: apps/api/src/orders>` | Orders squad |
| U2 | `<example: apps/api/src/billing>` | Billing squad |

## Allowed imports (summary)

| From → To | Rule | Enforced by |
|-------------|------|-------------|
| U1 → U2 | **Forbidden** direct domain import; use `U2` public port only | import lint / review |
| U2 → U1 | Same | … |

## Notes

- **Unknown** couplings: any path not listed here defaults to **requires human review** until classified.
```

---

## 4. Relationship to other artifacts

- **Feature specs:** reference unit ids when describing which contexts a feature touches.  
- **Iteration carrier:** MOD-01 / MOD-06 rows point at this file for “which boundaries were crossed.”  
- **CI:** when ready, generate lint config **from** this table (single source of truth).

---

## 5. Starter content (non-normative example)

Until a dedicated `{BOUNDARY_MAP}` file exists, use **`.ai/standards/*-DIRECTORY_MAP.md`** as the **interim** boundary list (`REPLACE:PLATFORM_PACKAGE/`, `<context-a>/`, `<context-b>/`, …). Promote a trimmed **edge-only** table here or into a dedicated boundary file when M1 lands and import lint exists.
