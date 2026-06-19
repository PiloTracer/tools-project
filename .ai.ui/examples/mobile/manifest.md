# mobile — manifest

**Archetype:** `mobile-app` · **Patterns doc:** UI-PATTERNS § mobile + navigation

| id | file | patterns (verified) | use when |
|----|------|---------------------|----------|
| M1 | `image.png` | 3-up: home feed + editor canvas + AI bottom sheet; bottom nav + center FAB; horizontal category chips; template carousels | Consumer creative / content apps |
| M2–M9 | `image copy*.png` | Browse vs edit toolbars; prompt UI for generative features (review per file) | Mobile flows |

**Extracted rules:**

- **Mode switch:** browse (tabs + lists) vs edit (canvas + tool tray) — different chrome
- Bottom sheet for AI/secondary tasks; keep canvas visible
- Horizontal scroll for categories/templates with clear affordance
- FAB for primary create — do not stack with 5th tab item without SPEC

**Pair with:** `mobile-controls/manifest.md` for control sizing.
