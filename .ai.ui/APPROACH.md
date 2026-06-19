# Project approach — archetypes & skill chains

**Purpose:** One file agents read to pick the right `ui-*` path. **Not** a folder tree — extend by adding rows here and pattern notes in [`standards/20260523-UI-PATTERNS.md`](standards/20260523-UI-PATTERNS.md).

**Invoke:** `@ui-project-approach - <describe project>` · `@ui-project-approach status`

---

## 1. Pick archetype (required in foundation doc 01)

| Archetype | Signals | Primary surfaces |
|-----------|---------|------------------|
| **marketing-site** | Hero, storytelling, few forms, CMS | Landing, about, contact |
| **saas-product** | Auth, app shell, settings, billing | Dashboard, lists, detail |
| **admin-dashboard** | Dense tables, filters, KPIs, roles | Data-heavy back-office |
| **mobile-app** | Bottom nav, sheets, touch, narrow width | Native-like or PWA |
| **design-system** | Primitives, docs, Storybook first | Buttons, forms, tokens |
| **hybrid** | Marketing + logged-in app | Split foundation; two screen maps |

If hybrid → document **marketing** vs **app** shells separately in screen map (foundation 04).

---

## 2. Skill chain (default)

| Archetype | Chain (after `@ui-bootstrap init`) |
|-----------|----------------------------------|
| marketing-site | `ui-style-stack set` → `ui-design-foundation greenfield` → `ui-screen-spec create` per route → `ui-component-build` → verify |
| saas-product | `ui-style-stack set` → `ui-design-foundation` → `ui-screen-spec` (shell + key flows) → `ui-design-system init` → `ui-component-build` → verify + a11y |
| admin-dashboard | Same as saas; **require** UIS-01 + pattern § data-density in SPECs |
| mobile-app | `ui-style-stack set` → foundation → specs per screen → build; **UIS-02 required** every screen |
| design-system | foundation → `ui-design-system init` → primitives before screens |
| hybrid | foundation once → separate SPEC groups per shell |

**Always:** `@session-control` (Agent OS) for session bookends when `.ai/` present.

**Never duplicate:** `plan-master`, `code-implementation`, `feature-spec` — link domain SPECs from screen SPECs.

---

## 3. Style stack (see `style-stacks/`)

Set once in foundation + `{HANDOFF_UI}` via `@ui-style-stack set - <stack>`.

| Stack | When |
|-------|------|
| `tailwind` | Utility-first, rapid UI, design tokens → `tailwind.config` |
| `css-modules` | Component-scoped CSS, React/Vue SFC |
| `vanilla-css` | Tokens as CSS variables, no runtime CSS-in-JS |
| `styled-components` | Theme object + styled primitives |

Implementation rules live in `style-stacks/<stack>.md` — skills emit code for the **active** stack only.

---

## 4. Complexity (scope, not more skills)

| Level | Scope | Extra discipline |
|-------|-------|------------------|
| **S** | 1–3 screens, one archetype | UIS-01 + UIS-06 on agent diffs; UIS-07 if tier ≥ refined |
| **M** | App shell + 5–15 screens | Full foundation 01–04; design-system catalog |
| **L** | Multi-role, i18n, white-label | ADRs for theme; stricter verify cadence |

---

## 5. Inspiration (do not treat as spec)

| Source | Path |
|--------|------|
| Annotated screenshots | [`examples/INDEX.md`](examples/INDEX.md) |
| External galleries | [`resources/README.md`](resources/README.md) |
| Project brand | `.ai.ui/inputs/brand/` or adopter `inputs/` |

**Rule:** Patterns from examples → SPEC §13 (`exampleIds`, `extractedRules`). See [`examples/INDEX.md`](examples/INDEX.md) playbook.

---

## 6. Skills we explicitly did **not** add

Feedback proposed 12 niche skills (`ui-landing-page`, `ui-data-display`, …). **Rejected** to avoid overlap and bloat. Use instead:

| Need | Use |
|------|-----|
| Landing / hero | Archetype `marketing-site` + [`UI-PATTERNS`](standards/20260523-UI-PATTERNS.md) § marketing |
| Tables / dashboards | Archetype `admin-dashboard` + UI-PATTERNS § data |
| Forms | UI-PATTERNS § forms + UIS-05 |
| Mobile controls | UI-PATTERNS § mobile + UIS-02 |
| Motion | UIS-03 |
| Responsive QA | UIS-02 + `@ui-visual-verify` |
| Token codegen | foundation doc 02 + `@ui-style-stack` |
| i18n / RTL | UI-CONVENTIONS § i18n (defer dedicated skill) |

**Add a new skill only when** a workflow needs gates, file writes, and a protocol that UI-PATTERNS + existing skills cannot cover. Register in `skills/README.md` + one row in §2 above.

---

## 7. Extending this framework

1. **Archetype:** Add row §1 + §2; optional `examples/<folder>/manifest.md` entry.
2. **Pattern:** Edit `standards/20260523-UI-PATTERNS.md` (one section).
3. **Style stack:** Add `style-stacks/<name>.md` + row in `style-stacks/README.md`.
4. **Concept:** New `concepts/<name>/` with **UIS-NN** + trigger row in `concepts/README.md`.
5. **Skill:** `skills/ui-<name>/skill.md` + `SKILL_DEPENDENCIES.md` — must not duplicate Agent OS.
