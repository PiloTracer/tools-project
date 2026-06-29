# Docker Reference

## Quick Commands

```bash
# Start the full development stack
docker compose --profile dev up --build

# Start in background
docker compose --profile dev up --build -d

# Stop the stack
docker compose --profile dev down

# Stop and remove volumes (fresh start)
docker compose --profile dev down -v

# View logs
docker compose logs -f api
docker compose logs -f web

# Run a command in the API container
docker compose exec api bash

# Run a command in the web container
docker compose exec web sh

# One-off Python script
docker compose exec api python -c "print('hello')"

# Run tests (when available)
docker compose exec api pytest
```

## Development Stack

The dev stack (`docker-compose.dev.yml`) mounts source directories for live reload:

| Service | Image | Host mount | Container path |
|---------|-------|-----------|----------------|
| `api` | Python 3.11 (dev) | `./api` | `/app` |
| `web` | Node 20 (dev) | `./web` | `/app` |
| `postgresql` | PostgreSQL 16 | — | — |

## Production Stack

The prod stack (`docker-compose.prd.yml`) uses pre-built images:

```bash
# Build production images
docker compose -f docker-compose.prd.yml build

# Start production stack
docker compose -f docker-compose.prd.yml --env-file .env.prd up -d
```

## Interactive Menu

The `bin/start.sh` script provides an interactive menu:

```bash
./bin/start.sh
```

Options:
- **Dev mode** — Start development stack with live reload
- **Production mode** — Start production stack
- **Clean up** — Stop and remove containers/volumes
- **Backup** — Backup attachments volume
- **Restore** — Restore attachments volume from backup
- **Nuke** — Full reset (containers, volumes, images)

## Maintenance

```bash
# Run DDL scripts manually
docker compose exec api python -m app.cli_schema apply-ddl

# Check API health
curl http://localhost:8300/healthz

# Check web server
curl -s -o /dev/null -w "%{http_code}" http://localhost:18513

# Verify web build
docker compose exec web sh -lc "npm run build"
```
