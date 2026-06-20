# Prospects list — Screen SPEC amendment 01

**Amends:** `.work.ui/screens/prospects-list/20260618-SCREEN-SPEC.md` (Approved)
**Date:** 2026-06-19
**Reason:** §8 Tokens & components listed `Button` and `Input` with catalog status `done`, but per `CATALOG.md` § Missing there are **no** `Button` or `Input` React primitives — they are CSS utility classes (`.btn`, `.btn-primary`, `.input`). Status should be `native allowed` with a waiver note, matching the convention used for `Select` in the same table.

---

## §8 Tokens & components — corrected rows

Replace these two rows in the Approved SPEC's §8 table:

| Component | Catalog status (was) | Catalog status (now) | Native waiver |
|-----------|----------------------|----------------------|---------------|
| Button | `done` | `native allowed` | Utility classes `.btn`, `.btn-primary` (no React primitive — CATALOG.md § Missing) |
| Input | `done` | `native allowed` | Utility class `.input` (no React primitive — CATALOG.md § Missing) |

All other §8 rows (DataTable, Badge, Chip, Select, Dialog, DropdownMenu, Skeleton) are unchanged and remain `done`.

## Rationale

`CATALOG.md` § Missing explicitly states: "no `Button` or `Input` React primitives — use utility classes (`.btn`, `.btn-primary`, `.input` in `globals.css`)". The original SPEC marked them `done` (catalog primitive present), which is inconsistent with the catalog. This amendment corrects the status to `native allowed` with the waiver reason, aligning the Approved SPEC with the three sibling SPECs (prospects-detail, clients-list, clients-detail) that were fixed to `native allowed` on 2026-06-19.

## Impact

None on implementation — the prospects list page already uses `.btn` / `.input` utility classes (not React primitives). This is a documentation/catalog-consistency correction only.
