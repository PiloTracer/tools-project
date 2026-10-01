# tools-project

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A **project management hub with integrated CRM** — manage projects, tasks, tickets, track GitHub commits, and run a sales-to-delivery pipeline. All in one self-hosted app. **Free and open source under the MIT License.**

**Repository:** <https://github.com/PiloTracer/tools-project>

## Features

- **Project Management** — Kanban boards, task tracking, support tickets, activity feeds
- **GitHub Integration** — Link repos, sync commits automatically, link commits to tasks/tickets
- **CRM Pipeline** — Track prospects through sales stages, manage clients and contacts, client portal
- **Collaboration** — Threaded comments, @mentions, markdown editor, inbox, watches
- **Dual Auth** — Standalone (local) or OAuth 2.0 SSO, configurable per deployment
- **Client Portal** — Limited project view for external stakeholders

## License

MIT — free for personal and commercial use. See [LICENSE](LICENSE) for the full text.

## Quick start.

```bash
cp .env.example .env.dev
./bin/start.sh dev          # interactive dev menu (also: ./bin/start.sh dev start)
```

Verify a configuration before starting (never reads `.env`; mode files only):

```bash
./bin/env-check.sh          # every mode file present here — dev and prd
./bin/env-check.sh prd      # one mode, with the full list of missing keys
./bin/env-check.sh --diff   # side-by-side: .env.example | .env.dev | .env.prd, line by line
```

The three env files are kept on the same line layout, so a key that is on line *x* of
`.env.example` is on line *x* of `.env.dev` and `.env.prd`. Production's file lives in the
repo root or in `$TOOLS_PROJECT_SECRET_DIR` (default: sibling `tools-project-secret/`).

- **Web:** http://localhost:18513
- **API:** http://localhost:8300/docs
- **Login:** `admin@example.com` / `dev-bootstrap-change-me`

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2 async |
| Database | PostgreSQL 16 |
| Auth | Local JWT (bcrypt) + OAuth 2.0 (PKCE) |
| Schema | Declarative SQL scripts (no Alembic) |
| Container | Docker Compose (dev + production) |

## Documentation

| Guide | Description |
|-------|-------------|
| [Quick Start](.work/docs/QUICK_START.md) | Get running in 5 minutes |
| [Feature Overview](.work/docs/FEATURES.md) | All features explained |
| [Architecture](.work/docs/ARCHITECTURE.md) | System design and decisions |
| [Auth Guide](.work/docs/guides/AUTH.md) | Authentication modes |
| [GitHub Guide](.work/docs/guides/GITHUB.md) | GitHub integration setup |
| [CRM Guide](.work/docs/guides/CRM.md) | Sales pipeline and client management |
| [Admin Guide](.work/docs/guides/ADMIN.md) | User management and configuration |
| [First Project Tutorial](.work/docs/tutorials/FIRST_PROJECT.md) | Walk through creating your first project |
| [GitHub Setup Tutorial](.work/docs/tutorials/GITHUB_SETUP.md) | Connect a GitHub repository |
| [Configuration Reference](.work/docs/reference/CONFIGURATION.md) | All environment variables |
| [Docker Reference](.work/docs/reference/DOCKER.md) | Docker commands and maintenance |
| [API Reference](.work/docs/reference/API.md) | All REST API endpoints |
| [Plan Sync Reference](.work/docs/reference/PLAN_SYNC.md) | Sync a plan file into a project (milestones + tasks) |
| [Release Notes](CHANGELOG.md) | What's new |

## Deployment

### Development

```bash
docker compose --profile dev up --build
```

### Production

```bash
cp .env.example .env.prd
# Edit .env.prd with production secrets
docker compose -f docker-compose.prd.yml --env-file .env.prd up -d --build
```

Or use the interactive menu:

```bash
./bin/start.sh dev          # dev menu  (env .env.dev)
./bin/start.sh prd          # prod menu (env .env.prd)
./bin/start.sh dev status   # single command, non-interactive
```

The mode (`dev`/`prd`) is mandatory; the script refuses to run without it and never reads a bare `.env`.

## Project Health

| Badge | Description |
|-------|-------------|
| CI | Automated lint + type-check + build on every push |
| Health | `/healthz` endpoint checks DB liveness, returns version + uptime |
| Tracing | Every response includes `X-Request-Id` for debugging |

## License

MIT — see [LICENSE](LICENSE). Free for personal and commercial use.
