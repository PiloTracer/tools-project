import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import run_bootstrap
from app.db import init_db, session_factory
from app.routers import admin_users, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    fac = session_factory()
    async with fac() as session:
        await run_bootstrap(session)
    yield


app = FastAPI(
    title="tools-project API",
    description="Project management hub — backend",
    version="0.1.0",
    lifespan=lifespan,
)

_origins_raw = os.environ.get("CORS_ALLOWED_ORIGINS", "").strip()
if _origins_raw:
    _origins = [o.strip() for o in _origins_raw.split(",") if o.strip()]
else:
    _origins = ["http://localhost:18513"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin_users.router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/projects")
def list_projects_stub() -> dict[str, object]:
    """Placeholder until persistence + auth are wired."""
    return {
        "items": [],
        "message": "Stub — implement projects CRUD",
    }
