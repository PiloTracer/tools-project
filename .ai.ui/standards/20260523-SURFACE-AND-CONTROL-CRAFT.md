# Surface and control craft — template

> **Positive quality bar** for surfaces, controls, grouping, and clarity. Complements [`20260523-UI-PATTERNS.md`](20260523-UI-PATTERNS.md) (structure) and UIS-06 (anti-slop). **Orthogonal to color scheme** — applies to light, dark, and branded themes.

**Referenced from:** screen SPEC §13, foundation doc 02/03, `@ui-visual-verify`, `@ui-concept-run - UIS-07`

Replace `REPLACE:UI_` tokens after copy.

---

## 1. Craft tier (foundation doc 01)

| Tier | When | Surfaces | Controls |
|------|------|----------|----------|
| **utilitarian** | Internal admin, prototypes | Flat or single elevation; clear borders | Native inputs allowed if SPEC §8 waives catalog |
| **refined** | Customer-facing apps, SaaS | Surface stack + section grouping | Catalog primitives for sliders, selects, toggles on primary flows |
| **premium** | Hardware panels, creative tools, flagship marketing | Card grids, optional glass/blur per SPEC | Custom anatomy; no native range/select on hero/settings flows |

Document chosen tier in foundation **01** and HANDOFF_UI. Do not mix tiers on one screen without SPEC note.

---

## 2. Surface stack (tokens required in foundation doc 02)

Map to semantic CSS variables (names illustrative):

| Layer | Token role | Typical use |
|-------|------------|-------------|
| **base** | `--surface-base` | Page / app background |
| **elevated** | `--surface-elevated` | Cards, panels, modals |
| **inset** | `--surface-inset` | Wells inside cards, input backgrounds |
| **overlay** | `--surface-overlay` | Sheets, popovers, scrims |

**Elevation:** pair surface tokens with `--elevation-*` or `--shadow-*` — never ad-hoc `box-shadow` in screen components.

**Separators:** `--border-subtle` between regions; prefer spacing + separator over nested boxes.

**Optional glass:** only when SPEC §13 cites an example with blur/scrim and craft tier ≥ refined; document `backdrop-filter` fallback.

---

## 3. Control anatomy (catalog primitives)

Every interactive control in **refined** or **premium** tier must use a catalog primitive (see COMPONENT_STANDARD), not browser defaults, unless SPEC §8 lists **native allowed** with waiver.

| Part | Rule |
|------|------|
| **Label** | Visible; associated via `for` / `aria-labelledby` |
| **Value readout** | Numeric or unit beside or below control — not only thumb position |
| **Track / thumb** | Token-backed sizes; focus ring on thumb/handle |
| **States** | default, hover, focus-visible, disabled, loading — distinct visuals |
| **Grouping** | Related controls in `fieldset` or `SectionHeader` + card |

**Primitive names (suggested):** `Card`, `SectionHeader`, `RangeSlider`, `SegmentedControl`, `Toggle`, `Stepper`, `Select` (custom), `IconButton`.

---

## 4. Grouping and clarity

- **Section headers:** title + optional description before control clusters
- **Card grid:** 2–4 columns on desktop; single column on narrow viewports unless SPEC defines otherwise
- **One primary metric per card** on dashboards (see dashboards D1)
- **Legends** for multi-segment status bars — not color-only (UIS-04)
- **Proximity:** label + control + value readout grouped; unrelated fields separated by spacing token step ≥ 2

Run **UIS-01** for scan path; **UIS-07** for craft compliance on diffs.

### Implementation priority (pixels before paperwork)

When craft tier ≥ refined, ship these **before** more docs:

1. **Custom control anatomy** — styled track/thumb + value readout (not `accent-color` on native range)
2. **Surface stack** — at least `--surface-elevated` cards or toolbar wells on primary screens
3. **Section grouping** — `SectionHeader` or fieldset clusters; one primary metric per card on dashboards
4. **S0 primitives** — build cited catalog components ([`resources/control-platforms.md`](../resources/control-platforms.md) for OSS behavior when tier ≥ refined), then compose screens
5. **Screenshot diff** — BEFORE in `inputs/design-references/`; verify against §13 extractedRules

Orchestration steps: [`examples/INDEX.md`](../examples/INDEX.md) § playbook only — do not duplicate here.

---

## 5. Native vs custom policy

| Control | utilitarian | refined | premium |
|---------|-------------|---------|---------|
| `<input type="range">` | allowed | catalog `RangeSlider` | required |
| `<select>` | allowed | catalog `Select` or `SegmentedControl` when ≤5 options | required |
| `<input type="checkbox">` | allowed | catalog `Toggle` for settings | required |
| `<button>` | plain OK | catalog `Button` variants | catalog `Button` |

**Waiver:** SPEC §8 row `native allowed: yes` + reason + HANDOFF_UI note for `@ui-component-build`.

**Binding workflow:** [`examples/INDEX.md`](../examples/INDEX.md) § Example → implementation playbook.

**Invalid SPEC:** cites `mobile-controls/C1` but §8 allows native range inputs without waiver.

---

## 6. Verify

Run `@ui-visual-verify milestone` — craft checklist lives in [`skills/ui-visual-verify/skill.md`](../skills/ui-visual-verify/skill.md). Run `@ui-concept-run - UIS-07` when craft tier ≥ refined.

---

## Related

| Doc | Role |
|-----|------|
| [`20260523-DESIGN_TOKENS_STANDARD.md`](20260523-DESIGN_TOKENS_STANDARD.md) | Token format and forbidden raw values |
| [`20260523-UI-PATTERNS.md`](20260523-UI-PATTERNS.md) | Structural checklists |
| [`20260523-COMPONENT_STANDARD.md`](20260523-COMPONENT_STANDARD.md) | Primitive tiers and Storybook |
| [`examples/INDEX.md`](../examples/INDEX.md) | Visual reference index |
| [`resources/control-platforms.md`](../resources/control-platforms.md) | OSS behavior platforms (MIT/Apache only) |
