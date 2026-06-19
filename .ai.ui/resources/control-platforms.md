# Control platforms — behavior sources (commercial-safe)

**Purpose:** Pick **one** OSS platform for interaction/a11y; **you** own surfaces via tokens + `ds-*` CSS (or active style stack).

**Visual target:** [`examples/INDEX.md`](../examples/INDEX.md) + SPEC §13 — not these libraries’ default skins.

**License policy:** Only sources verified **MIT**, **Apache-2.0**, **BSD**, or **CC0/public domain**. No GPL dependencies as platform baseline. No paid kits (Tailwind UI, etc.). Verify `LICENSE` in each package before ship.

**Record choice in:** foundation doc 03 row, `CATALOG.md` **Behavior source** column, HANDOFF_UI one line.

---

## Pick one behavior platform per repo

| Platform | License | Stack | Role |
|----------|---------|-------|------|
| [Radix UI Primitives](https://www.radix-ui.com/primitives) | MIT | React | Slider, Select, Switch, Dialog, Tabs — unstyled |
| [React Aria Components](https://react-spectrum.adobe.com/react-aria/) | Apache-2.0 | React | Same; strong mobile/gesture |
| [Ark UI](https://ark-ui.com) | MIT | React, Vue, Solid, Svelte | Primitives on Zag.js |
| [Headless UI](https://headlessui.com) | MIT | React, Vue | Lists, menus, dialogs |
| [Base UI](https://base-ui.com) | MIT | React | MUI headless primitives |
| [Shoelace](https://shoelace.style) | MIT | Web Components | Framework-agnostic; style via CSS parts / tokens |

**Do not** mix Radix + React Aria heavily in one app (bundle + API drift).

---

## Optional accelerators (copy into your repo)

| Platform | License | Notes |
|----------|---------|-------|
| [shadcn/ui](https://ui.shadcn.com) | MIT | Copy-paste components; often Radix + Tailwind — **re-skin** to your stack |
| [Park UI](https://park-ui.com) | MIT | Styled recipes on Ark + Panda CSS |
| [Jolly UI](https://jollyui.dev) | MIT | Styled recipes on React Aria |

Use for **starting code**, not as npm theme. Strip foreign styling; keep behavior wiring.

---

## Reference only (full styled systems)

MIT/Apache kits — adopt whole UI or mine patterns; harder to match custom craft tier:

[Mantine](https://mantine.dev) (MIT) · [Chakra UI](https://chakra-ui.com) (MIT) · [Carbon](https://carbondesignsystem.com) (Apache-2.0) · [USWDS](https://designsystem.digital.gov) (CC0 components)

---

## Pattern catalog (no code)

| Resource | Use |
|----------|-----|
| [Open UI](https://open-ui.org) | Control research + API vocabulary for SPECs |
| [WAI-ARIA APG](https://www.w3.org/WAI/ARIA/apg/) | Authoritative interaction patterns |

---

## Adoption (S0 primitive)

```text
1. examples/mobile-controls/C5 → SPEC §13 extractedRules
2. Pick platform row above → HANDOFF_UI
3. @ui-design-system add - RangeSlider
   CATALOG: Behavior source = @radix-ui/react-slider (MIT)
   Path = frontend/.../ds-range + your tokens
4. Style with SURFACE-AND-CONTROL-CRAFT §3 — no platform default chrome
```

**Native HTML** remains OK when craft tier = utilitarian and SPEC §8 waives catalog.
