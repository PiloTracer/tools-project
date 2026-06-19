# CSS Modules

**Tokens →** CSS variables on `:root` / `[data-theme]`; import `tokens.css` once in app entry.

**Do**

- One `.module.css` per component; compose class names in TS/JS
- Use `composes:` sparingly; prefer design-system primitives
- Logical properties (`margin-inline`) for RTL-ready layouts

**Don't**

- Global element selectors in module files (breaks isolation)
- Duplicate token values — reference `var(--token-name)`

**Verify:** typecheck + stylelint if configured.
