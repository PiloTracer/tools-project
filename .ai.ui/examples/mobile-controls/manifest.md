# mobile-controls — manifest

**Archetype:** `mobile-app` · **Patterns doc:** UI-PATTERNS § forms + mobile-native · **Craft:** [`standards/20260523-SURFACE-AND-CONTROL-CRAFT.md`](../../standards/20260523-SURFACE-AND-CONTROL-CRAFT.md)

| id | file | surfaces | controls | typography | spacing | extractedRules | primitives |
|----|------|----------|----------|------------|---------|----------------|------------|
| C1 | `image.png` | Dark base; elevated card grid; optional glass on cards; sidebar icon rail | Vertical % sliders with readout; mode pills; segmented Open/Pause/Close; toggle switch; circular power buttons | Bold metric (80%, -16°C); muted labels; status icons in header | Card padding ~16–24px; grid gaps; pill clusters | Card grid for control clusters; one primary metric per card; vertical slider shows numeric % beside track; segmented actions for multi-state (not dropdown); mode pills in vertical stack; min 44px touch on all controls | `Card`, `RangeSlider`, `SegmentedControl`, `Toggle`, `IconButton`, `SectionHeader` |
| C2 | `image copy.png` | Dark panels; hero chart card; thumbnail cards with status dots | Bottom tab bar; full-width primary CTA; stepper (+/−); green toggle; icon grid selector | Large kW hero metric; small labels on cards; tab labels under icons | Hero block + 2-col card grid; bottom nav safe area | Hero metric + sparkline/chart in elevated card; panel cards with thumbnail + status dot + sub-metrics; steppers for numeric fields; icon grid for category pick (active = border accent); bottom nav ≤5 items | `Card`, `Stepper`, `Toggle`, `BottomNav`, `Button`, `LineChart` (optional) |
| C3 | `image copy 2.png` | Dark navy cards; gradient chart bars; list rows with icons | Pill category filters; circular play FAB-style; segmented Week/Month/Year; progress rings on list items | Greeting headline; price tags right-aligned; badge for delta (+32%) | Search bar full width; featured card large; filter pills horizontal scroll | Pill filters for categories (active = filled); featured content card with illustration + floating action; segmented time range for charts; list rows with trailing status (check vs progress ring); audio/player controls as icon cluster + large primary | `Card`, `SegmentedControl`, `Chip`, `SearchBar`, `ProgressRing`, `Button` |
| C4 | `image copy 3.png` | Glass cards on purple gradient; bottom sheet overlay; nested cards in sheet | Room pill selector (horizontal scroll); ghost + gradient primary buttons; status pill (Online) | Monospace micro-metadata blocks; brand wordmark; small spec labels | Bottom sheet inset; pill row above fold | Glass/blur cards only when SPEC allows; status pill with glow dot; horizontal scroll pills for context switch; bottom sheet for secondary flow; pair ghost + solid CTAs; optional technical micro-copy in corners (premium tier) | `Card`, `BottomSheet`, `Chip`, `Button`, `Badge` |
| C5 | `image copy 4.png` | Light/dark mixed settings panels; grouped field cards | Custom sliders with value; dropdowns styled; toggle rows; checkbox lists | Label above control; value below or inline with slider | Section spacing between groups; consistent field vertical rhythm | Settings: label + custom slider + unit readout (never bare range); group related fields under section title; toggles as row (label left, control right); avoid native select styling on primary settings | `SectionHeader`, `RangeSlider`, `Toggle`, `Select`, `Card` |
| C6 | `image copy 5.png` | Compact control density; inset wells for inputs | Steppers; radio clusters; mini sliders; button groups | Smaller type scale; tight label-control pairing | Reduced padding tier for dense forms | Dense form variant: still ≥44px touch; use inset `--surface-inset` for inputs; radio/checkbox clusters in fieldset; mini sliders only for secondary prefs | `Stepper`, `RangeSlider`, `RadioGroup`, `Fieldset`, `Toggle` |

## Global extracted rules

- Minimum 44×44px touch targets (UIS-02)
- Group related controls with legends or `SectionHeader`
- Prefer catalog primitives over browser defaults when craft tier ≥ refined
- Cite **id** (e.g. `C1`) in SPEC §13 — not filename

## Pair with

- `examples/mobile/manifest.md` — nav, sheets, browse vs edit
- `examples/dashboards/manifest.md` — KPI cards when mixing admin + controls
