---
name: ui-design-foundation
description: >-
  Establish UI foundation: design tokens doc, pattern inventory, screen map,
  a11y baseline. Certifies screen-spec-ready. Use greenfield, probe, status, certify.
---

# ui-design-foundation

**Output root (mandatory):** `{WORK_UI_ROOT}` = **`<repo-root>/.work.ui/`** (sibling to `.ai.ui/`). Never write foundation docs under `.ai.ui/`.

Produces under `{UI_PLANS_ROOT}/foundation/` (= `.work.ui/plans/foundation/`):

| Doc | Purpose |
|-----|---------|
| `YYYYMMDD-01-ui-vision-and-principles.md` | Vision, **archetype**, complexity, style stack, **craft tier** |
| `YYYYMMDD-02-design-tokens.md` | Maps to `REPLACE:UI_TOKENS_FILE`; **surface/elevation** tokens when tier ≥ refined |
| `YYYYMMDD-03-pattern-inventory.md` | Existing vs needed components; **example id** + catalog primitive per row |
| `YYYYMMDD-04-screen-map.md` | Slugs, routes, priority, dependencies |

Updates `{HANDOFF_UI}` (`.work.ui/context/HANDOFF_UI.md`) with **UI foundation state**.

Also update when changed: `.work.ui/plans/ASSUMPTIONS.md`, `RISK_REGISTRY.md`, `UNKNOWNS.md`.

## Before greenfield

Recommend: `@ui-project-approach - <description>` · `@ui-style-stack set - <stack>` · pick **2–4 example ids** from `examples/INDEX.md`.

## greenfield (craft)

Set **craft tier** in doc 01; `--surface-*` in doc 02 when tier ≥ refined; doc 03 rows cite **example id** + primitive. Record ids in HANDOFF_UI. See [`SURFACE-AND-CONTROL-CRAFT`](../../standards/20260523-SURFACE-AND-CONTROL-CRAFT.md) §1–2 and [`examples/INDEX.md`](../../examples/INDEX.md) playbook.

## Modes

| Mode | Action |
|------|--------|
| `greenfield` | Create docs 01–04 (see greenfield protocol above) |
| `probe` | Interrogate until UI foundation is understood (see Probe protocol) |
| `probe - status` | Read the ledger read-only; ask nothing |
| `probe - until ready` | Loop passes without re-confirming between them |
| `status` | Read-only readiness |
| `certify screen-spec-ready` | Gate: all foundation docs present + token file exists |

## Probe protocol

Adaptive, gap-driven interrogation that **guarantees foundation understanding** before certification. Engine: [`probe-protocol.md`](../probe-protocol.md) (loop, scoring, ledger — not restated here). This section supplies the foundation **coverage profile**.

| Parameter | Value |
|-----------|-------|
| Exit gate | [certify gate](#certify-gate) (screen-spec-ready) |
| Ledger | `{UI_PLANS_ROOT}/foundation/PROBE_LEDGER.md` |
| Target | Coverage ≥ 85%; no ★ dimension below `partial` |

**Coverage map** (★ = gate-blocking, weight 2):

| Dim | Topic | What good looks like | Records into |
|-----|-------|----------------------|--------------|
| D1 ★ | Product UI intent & users | Who/what/primary jobs + archetype named | doc 01 |
| D2 ★ | Success / craft tier | Measurable craft bar + tier (basic/standard/refined) | doc 01 |
| D3 | Brand & visual language | Voice, references, do/don't | doc 01 |
| D4 ★ | Design tokens | Color/type/space/surface tokens mapped to `REPLACE:UI_TOKENS_FILE` | doc 02 |
| D5 | Pattern inventory | Existing vs needed components + example ids | doc 03 |
| D6 ★ | Screen map & IA | Slugs, routes, priority, dependencies | doc 04 |
| D7 | Accessibility targets | WCAG level + key constraints | doc 01 / ASSUMPTIONS |
| D8 | Platform / responsive | Breakpoints, devices, performance budget | doc 01 |

`probe` records answers into the docs above + `HANDOFF_UI`; owner-blocked items → `UNKNOWNS.md`.

## certify gate

**Required:** ui-foundation-complete (all four docs, tokens linked in HANDOFF_UI).

**Unlocks:** `@ui-screen-spec create`

## Pairs with

- `@ui-design-system init` after tokens doc
- Agent OS `@plan-foundation` — parallel; cross-link FRs in screen map, do not duplicate
