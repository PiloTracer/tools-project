# Concepts pack — design & UX signals for AI-assisted UI

**Location:** `.ai.ui/concepts/`  
**Scope:** Markdown only. Does **not** modify `.ai/skills/` or `.ai/concepts/` (Agent OS).

**Purpose:** Repeatable **UIS-*** checks and copy-paste prompts for visual quality, layout, motion, contrast, interaction, craft, and AI-generated UI. Wire outputs into screen SPECs, `NEXT_UI.md`, or PR descriptions.

**Operator workflow:** `.ai.ui/docs/guides/workflows/README.md` · triggers below.

---

## How this relates to Agent OS MOD pack

| Agent OS (`.ai/concepts/`) | UI Design OS (this pack) |
|----------------------------|---------------------------|
| MOD-01…06 architecture, cost, coupling | **UIS-01…09** visual / UX / intuitive / data-viz |
| `@concept-run - MOD-06` for app code | `@ui-concept-run - UIS-06` for UI diffs |
| Both may apply on one PR | Run **both** when diff spans API + UI |

**Do not** rename or merge MOD folders into `.ai.ui/`. **Do not** add UIS ids under `.ai/concepts/`.

---

## Concept index

| Id | Directory | Use when… |
|----|-----------|-----------|
| UIS-01 | [`visual-hierarchy/`](visual-hierarchy/README.md) | New screen, marketing block, dense dashboard |
| UIS-02 | [`responsive-layout/`](responsive-layout/README.md) | Breakpoints, grid, overflow, mobile-first |
| UIS-03 | [`motion-design/`](motion-design/README.md) | Animation, transitions, loading skeletons |
| UIS-04 | [`color-contrast/`](color-contrast/README.md) | New colors, themes, overlays on imagery |
| UIS-05 | [`interaction-patterns/`](interaction-patterns/README.md) | Forms, modals, menus, multi-step flows |
| UIS-06 | [`ai-visual-quality/`](ai-visual-quality/README.md) | **AI-generated UI** — spacing drift, generic chrome |
| UIS-07 | [`surface-control-craft/`](surface-control-craft/README.md) | **Craft tier ≥ refined** — surfaces, controls, §13 compliance |
| UIS-08 | [`intuitive-ux/`](intuitive-ux/README.md) | **All screens** — discoverability, feedback, error forgiveness, cognitive load |
| UIS-09 | [`data-visualization-quality/`](data-visualization-quality/README.md) | **Analytical dashboards & charts** — truthful encoding, colorblind safety, responsive, chart junk |

---

## Trigger table

| If you are about to… | Run prompt | Output goes to | Required? |
|---|---|---|---|---|
| Open a screen SPEC | List UIS-01…08 in SPEC §12 | screen SPEC | **Required** |
| `@ui-component-build plan` | Copy SPEC §12 → `### UIS registry` in NEXT_UI | `NEXT_UI.md` | **Required** |
| Agent/Cursor UI session (default **AI-assisted: yes**) | [`ai-visual-quality/prompt.md`](ai-visual-quality/prompt.md) | PR, task Notes, NEXT_UI | **Required** unless **`human-only`** in same message |
| Craft tier ≥ refined; forms/settings/dashboards | [`surface-control-craft/prompt.md`](surface-control-craft/prompt.md) | PR, verify report | **Required** at milestone |
| New theme or semantic color token | UIS-04 | ADR or token PR | **Required** |
| New animation beyond micro-feedback | UIS-03 | screen SPEC or PR | Recommended |
| Multi-step flow or modal | UIS-05 | screen SPEC §6 | Recommended |
| Any screen before ship | UIS-08 | PR, verify report, NEXT_UI | **Required** |
| Analytical dashboard or report screen | UIS-09 | PR, verify report, NEXT_UI | **Required** (analytical dashboards) |
| If unsure | UIS-01 | PR / Notes | Default lightest prompt |

**Evidence tags:** `measured` | `estimated` | `assumption` | `unknown`

---

## Reliability rules

1. Do not treat inspiration screenshots as spec — cite screen SPEC or token file.
2. Prefer design-token file over memory for spacing and color.
3. Quantitative claims (contrast ratio, bundle size) need evidence or `unknown`.
4. Example ids from manifests inform SPEC §13 — implementation follows SPEC, not PNG filenames.
