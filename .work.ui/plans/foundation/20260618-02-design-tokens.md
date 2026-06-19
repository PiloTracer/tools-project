# Design Tokens

**Token file:** `web/src/app/globals.css` (CSS custom properties on `:root`).

**Craft tier:** refined — requires surface stack tokens, semantic color tokens, spacing scale, and elevation/shadow tokens.

---

## 1. Surface stack (new — add to globals.css)

| Token | Current value | Role |
|-------|--------------|------|
| `--surface-base` | `#0c1222` | Page / app background (same as current `--bg`) |
| `--surface-elevated` | `#121a2e` | Cards, panels, modals (same as current `--bg-elevated`) |
| `--surface-inset` | `#0a0f1c` | Wells inside cards, input backgrounds (darker than base) |
| `--surface-overlay` | `#1a2540` | Sheets, popovers, dropdowns, scrims (same as current `--surface`) |

## 2. Color tokens (existing - semantic naming)

| Token | Current var | Current value |
|-------|-------------|---------------|
| `--color-text-primary` | `--text` | `#e8eef9` |
| `--color-text-muted` | `--muted` | `#94a3c8` |
| `--color-accent` | `--accent` | `#38bdf8` |
| `--color-accent-dim` | `--accent-dim` | `#0ea5e9` |
| `--color-success` | `--success` | `#4ade80` |
| `--color-danger` | `--danger` | `#fb7185` |
| `--color-border` | `--border` | `#2a3f66` |

## 3. Spacing scale (new — add to globals.css)

```
--space-xs: 0.25rem;    /* 4px */
--space-sm: 0.5rem;     /* 8px */
--space-md: 0.75rem;    /* 12px */
--space-lg: 1rem;       /* 16px */
--space-xl: 1.5rem;     /* 24px */
--space-2xl: 2rem;      /* 32px */
```

## 4. Elevation / shadow

| Token | Value | Use |
|-------|-------|-----|
| `--shadow-sm` | `0 1px 3px rgb(0 0 0 / 30%)` | Subtle card |
| `--shadow-md` | `0 4px 20px rgb(0 0 0 / 20%)` | Elevated card, dropdown |
| `--shadow-lg` | `0 18px 50px rgb(0 0 0 / 35%)` | Modal, overlay (existing `.card` shadow) |

## 5. Radius

| Token | Value |
|-------|-------|
| `--radius-sm` | `6px` |
| `--radius-md` | `8px` |
| `--radius-lg` | `10px` (current `--radius`) |

## 6. Typography

| Token | Value |
|-------|-------|
| `--font-family` | `"DM Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` |
| `--text-xs` | `0.72rem` |
| `--text-sm` | `0.85rem` |
| `--text-base` | `0.95rem` |
| `--text-lg` | `1.05rem` |
| `--text-xl` | `1.15rem` |
| `--text-2xl` | `1.65rem` |

## 7. Z-index layers

| Token | Value | Use |
|-------|-------|-----|
| `--z-dropdown` | `30` | Dropdown menus, selects |
| `--z-modal` | `50` | Modals, dialogs |
| `--z-toast` | `60` | Toast notifications |

---

## Tokens to add to `web/src/app/globals.css`

Surface tokens, spacing scale, elevation/shadows, radius variants, named type scale, and z-index layers are new. The existing color tokens map as-is to the new semantic names.
