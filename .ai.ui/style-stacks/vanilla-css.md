# Vanilla CSS

**Tokens →** single `tokens.css` + optional `themes/dark.css`.

**Do**

- BEM or project prefix (`ds-`, `c-`) documented in DIRECTORY_MAP
- Layer order: tokens → reset → primitives → layouts → utilities
- Container queries where supported for component responsiveness

**Don't**

- Deep selector chains (`div div div .title`)
- ID selectors for styling

**Verify:** visual regression on key templates.
