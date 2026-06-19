# websites — manifest

**Archetype:** `marketing-site` · **Patterns doc:** UI-PATTERNS § marketing · **Craft:** [`standards/20260523-SURFACE-AND-CONTROL-CRAFT.md`](../../standards/20260523-SURFACE-AND-CONTROL-CRAFT.md)

| id | file | surfaces | controls | typography | spacing | extractedRules | primitives |
|----|------|----------|----------|------------|---------|----------------|------------|
| W1 | `image.png` | Full-bleed immersive hero (photo/video); minimal chrome; dark overlay | Central circular MENU hub; icon-only header (search, grid, bag); underline text CTA | Display serif headline + caps sans subcopy; logo centered | Edge-to-edge hero; bottom-center MENU affordance | Full-bleed hero imagery; serif headline + utility sans for tags/CTA; navigation can be non-standard (central MENU) — document in SPEC §6; dark immersive hero: contrast check on all overlay text (UIS-04); avoid generic AI gradient hero unless brand SPEC allows | `Hero`, `TextLink`, `IconButton`, `MenuHub` (pattern) |
| W2 | `image copy.png` | Split hero; light/dark sections; editorial whitespace | Standard top nav + hamburger; primary filled CTA | Large display + body copy pairing | Generous vertical sections | Alternate landing: split layout hero; clear H1 + single CTA; section rhythm with whitespace | `Hero`, `Button`, `NavBar` |
| W3 | `image copy 2.png` | Card grid for features; soft background | Multiple CTAs tiered (primary/secondary) | Feature titles bold; body regular | Feature grid 2–3 col desktop | Feature grid blocks below hero; secondary CTA ghost/outline | `Card`, `Button` |
| W4–W9 | `image copy*.png` | Varies — review before cite | Varies | Varies | Varies | Open PNG before SPEC cite; extract rules per screen | Per extraction |

**Extracted rules (W1):**

- Typography pairing: display serif + utility sans for tags/CTA
- Navigation can be non-standard (central MENU) — document in SPEC §6
- Dark immersive hero: contrast check on all overlay text (UIS-04)
- Avoid generic AI gradient hero unless brand SPEC allows

**External refs:** `resources/webdesign/concept.design.txt`
