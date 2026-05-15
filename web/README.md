# Web — tools-project

Next.js **App Router** app: project hub UI and **tools-dashboard** OAuth (see `src/app/sign-in`, `src/app/oauth/complete`).

Develop and build **only via Docker** (repo root `docker-compose.yml`, service `web`).

## Scripts

| Script | Purpose |
|--------|---------|
| `npm run dev` | Next dev server (compose uses `--hostname 0.0.0.0 --port 3000`) |
| `npm run build` | Production build |
| `npm run check` | ESLint |
