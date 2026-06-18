# ADR-0003: Frontend stack

**Status:** Decided
**Date:** 2026-06-18
**Source:** Brownfield reverse-engineering of existing code

## Context

The web client must render a full project management UI: Kanban boards, task detail, activity streams, GitHub commit history, and an upcoming client portal. The stack was chosen before this ADR was written — this document formalizes the existing decision.

## Decision

- **Runtime:** Node.js 22 (`web/Dockerfile.dev:1` — `node:22-bookworm-slim`)
- **Framework:** Next.js 16 App Router (`web/package.json` — `"next": "16.2.4"`) with SSR and API routes (BFF proxy pattern)
- **UI library:** React 19 (`web/package.json` — `"react": "19.2.4"`)
- **Language:** TypeScript ^5 (`web/package.json`)
- **Styling:** Global CSS in `src/app/globals.css` plus component-scoped styles as needed (no Tailwind or CSS-in-JS framework detected)
- **State management:** React state + `fetch`/server data fetching (no SWR, Redux, or Zustand committed)
- **Project structure:** `src/app/` for routes (App Router), `src/components/` for shared UI, `src/shared/` for server utilities

## Consequences

- Next.js App Router requires `'use client'` directives for client-side interactivity — all drag-drop, markdown editor, and kanban components must be client components.
- TypeScript strictness should be enforced per CONVENTIONS standard.
- Node.js 22 provides native `--experimental-require-module` for ESM/CJS interop.
- No global state library means prop drilling or context for data shared across routes — acceptable at current scale.

## Alternatives rejected

- **Vite + React Router:** Rejected — SSR via Next.js provides better SEO and eliminates a separate BFF server for client-side auth token management.
- **Tailwind CSS / CSS-in-JS:** Not used — existing global CSS convention maintained for consistency.
- **Redux / Zustand / SWR:** Not needed — current data-fetching patterns (React state + `fetch`/server fetching + per-page state) are sufficient.
