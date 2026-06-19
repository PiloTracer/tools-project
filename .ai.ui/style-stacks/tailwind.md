# Tailwind CSS

**Tokens →** `tailwind.config.ts` theme.extend (colors, spacing, radius, fontSize). Source of truth remains `REPLACE:UI_TOKENS_FILE` — sync, do not fork.

**Do**

- Semantic tokens mapped to theme keys (`primary`, `surface`, `muted`)
- `@layer components` for repeated compounds (button, input)
- Mobile-first breakpoints aligned with foundation doc 02

**Don't**

- Arbitrary values (`w-[437px]`) except one-off with SPEC note
- `!important` in components
- Mix raw hex in JSX class strings

**Verify:** `REPLACE:UI_LINT` + visual tests on changed routes.
