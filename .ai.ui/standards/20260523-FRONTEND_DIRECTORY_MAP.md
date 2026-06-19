# Frontend Directory Map — template

> Layout and import boundaries for UI code. Link from `.cursorrules` as `REPLACE:UI_DIRECTORY_MAP_FILE`.

---

## 1. Top-level map

```text
REPLACE:UI_APP_ROOT/
├── components/          # primitives + compounds (shared)
├── screens/               # route-level (or pages/)
├── hooks/
├── lib/                   # formatters, non-UI utils used by UI
├── styles/                # global CSS, token entry
└── assets/                # static images (prefer inputs/ for reference-only)

REPLACE:UI_STORYBOOK_DIR/   # optional
```

Customize paths to match the repo; update this file when structure changes.

## 2. Import boundaries (hard)

| From | May import |
|------|------------|
| `components/primitives/*` | tokens, utils — **not** screens, **not** data clients |
| `components/compounds/*` | primitives, tokens |
| `screens/*` | compounds, primitives, hooks, data layer |
| `screens/*` | **not** other `screens/*` internals |

## 3. Agent OS alignment

- Backend / API code: `REPLACE:APP_ROOT` per Agent OS DIRECTORY_MAP — UI does not redefine API boundaries
- Shared types: import from generated or shared package path documented in HANDOFF

## 4. Co-location

- Tests: `*.test.tsx` adjacent or `__tests__/`
- Stories: adjacent or Storybook glob per `REPLACE:UI_STORYBOOK_DIR`
