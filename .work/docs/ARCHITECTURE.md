# Architecture

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript | Web UI |
| **Backend** | FastAPI, Python 3.11, Uvicorn | REST API |
| **Database** | PostgreSQL 16, SQLAlchemy 2.0 (async) | Persistence |
| **Auth** | Local JWT (bcrypt) + OAuth 2.0 (PKCE) | Identity |
| **Schema** | Declarative SQL scripts (no Alembic) | Migrations |
| **Container** | Docker Compose (dev + production profiles) | Deployment |

## Repository Layout

```
tools-project/
├── api/                    # FastAPI backend
│   └── app/
│       ├── main.py         # App entry, lifespan, middleware
│       ├── config.py       # Pydantic settings (env-driven)
│       ├── db.py           # Async engine + session factory
│       ├── deps.py         # FastAPI dependencies (auth, permissions)
│       ├── models/         # SQLAlchemy ORM models
│       ├── routers/        # API route handlers
│       ├── services/       # Business logic services
│       └── schema_sql.py   # SQL script runner
├── web/                    # Next.js frontend
│   └── src/
│       ├── app/            # App Router pages + API routes
│       ├── components/     # Shared React components
│       └── shared/         # Server/client utilities
├── sql/                    # Database schema scripts
│   ├── schema_changes.sql  # Table DDL (idempotent)
│   ├── schema_indexes.sql  # Indexes + constraints
│   ├── schema_backfill.sql # Data backfills
│   └── schema_inserts.sql  # Seed data
├── .work/                  # Project working directory
│   ├── context/            # Session context, HANDOFF
│   ├── docs/               # Documentation (you are here)
│   ├── plans/              # Implementation plans
│   ├── features/           # Feature SPECs
│   └── decisions/          # Architecture Decision Records
├── docker-compose.dev.yml  # Development stack
├── docker-compose.prd.yml  # Production stack
└── CHANGELOG.md            # Release notes
```

## Architecture Decisions

Key ADRs (see `.work/decisions/`):

| ADR | Decision |
|-----|----------|
| 0001 | Client contact model: separate `client_contacts` with optional `user_id` FK |
| 0002 | Backend: Python 3.11, FastAPI, SQLAlchemy async, PostgreSQL 16 |
| 0003 | Frontend: Next.js 16, React 19, TypeScript |
| 0004 | Hosting: Docker Compose, dual auth, Fernet PAT encryption |

## Data Flow

```
Browser ──HTTP──► Next.js ──BFF proxy──► FastAPI ──SQLAlchemy──► PostgreSQL
                    │                        │
                    │ Server Components       │ Background tasks
                    │ (SSR)                   │ (GitHub poll, retention purge)
                    ▼                        ▼
              Static HTML              asyncio tasks
```

## Key Design Decisions

- **No Alembic:** Schema changes are idempotent SQL scripts in `sql/`, run on every API startup.
- **No Redis:** OAuth PKCE state is embedded in signed cookies.
- **Encrypted Secrets:** GitHub PATs are encrypted at rest with Fernet.
- **Dual Auth:** Both local JWT and OAuth 2.0 can operate simultaneously.
- **Company-Scoped Visibility:** Client participants see content from all contacts in their company.
