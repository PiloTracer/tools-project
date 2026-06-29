# Quick Start

Get tools-project running on your machine in 5 minutes.

## Prerequisites

- Docker & Docker Compose
- Git

## 1. Clone and configure

```bash
git clone <repo-url> tools-project
cd tools-project
cp .env.example .env
```

## 2. Start the stack

```bash
docker compose --profile dev up --build
```

This starts:
- **PostgreSQL 16** on port `55433`
- **FastAPI backend** on port `8300`
- **Next.js frontend** on port `18513`

## 3. Open the app

- **Web:** http://localhost:18513
- **API docs:** http://localhost:8300/docs
- **Health check:** http://localhost:8300/healthz

## 4. Sign in

Default bootstrap credentials (from `.env`):
- Email: `admin@example.com`
- Password: `dev-bootstrap-change-me`

## What's next

- [Feature overview](FEATURES.md)
- [Authentication guide](guides/AUTH.md)
- [GitHub integration guide](guides/GITHUB.md)
- [Reference: all env vars](reference/CONFIGURATION.md)
