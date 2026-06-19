# styled-components (or CSS-in-JS with theme)

**Tokens →** `theme` object exported from `REPLACE:UI_TOKENS_FILE` or `theme.ts` generated from tokens.

**Do**

- `ThemeProvider` at app root; typed theme for TS
- Primitive styled components in design-system folder
- Transient props (`$variant`) to avoid DOM leakage

**Don't**

- Inline `style={{}}` for layout that should be tokens
- New theme keys without updating token standard

**Verify:** unit tests for variants; Storybook theme switcher.
