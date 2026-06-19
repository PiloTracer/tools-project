# Front-end stack — tools-project

> **Bootstrap:** Created by `@ui-bootstrap init` when missing. Customize pins; link from `.cursorrules` as `DOCS_UI_STACK.md`.

**Updated:** 2025-06-11

## Runtime

| Item | Value |
|------|-------|
| Framework | Next.js 16 (App Router) |
| Language | TypeScript 5.x |
| Styling | Vanilla CSS (`web/src/app/globals.css`) |
| Package manager | npm |

## Tooling

| Check | Command |
|-------|---------|
| Unit tests | *not configured* |
| Lint | `cd web && npx eslint .` |
| Typecheck | `cd web && npx tsc --noEmit` |
| Visual regression | *not configured* |
| Accessibility | *not configured* |

## Paths

| Item | Path |
|------|------|
| App root | `web/` |
| Components | `web/src/components/` |
| Screens | `web/src/app/` (App Router routes) |
| Tokens | `web/src/app/globals.css` |
| Framework config | `web/next.config.ts` |

## Docker

| Service | Workdir |
|---------|---------|
| `web` | `/app` |

## Design references

- Inputs: `.ai.ui/inputs/`
- Screen SPECs: `.work.ui/screens/`
