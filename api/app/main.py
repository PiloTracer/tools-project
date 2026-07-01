import asyncio
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import select

from app.bootstrap import run_bootstrap
from app.config import get_settings
from app.db import get_engine, init_db, session_factory
from app.github_background import attachment_retention_purge_loop, github_poll_loop
from app.schema_sql import run_post_bootstrap
from app.routers import (
    activities,
    admin_users,
    agent_query,
    attachments,
    auth,
    client_contacts,
    client_health,
    client_portal,
    clients,
    commit_refs,
    components,
    github,
    inbox,
    me_api_keys,
    me_focus,
    project_client_access,
    project_clients,
    projects,
    prospects,
    reports,
    stats,
    tasks,
    tickets,
)


_github_poll_task: asyncio.Task | None = None
_retention_purge_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _github_poll_task, _retention_purge_task
    await init_db()
    fac = session_factory()
    async with fac() as session:
        await run_bootstrap(session)
    async with get_engine().begin() as conn:
        await run_post_bootstrap(conn)
    if get_settings().github_sync_enabled:
        _github_poll_task = asyncio.create_task(github_poll_loop(), name="github_poll_loop")
    _retention_purge_task = asyncio.create_task(
        attachment_retention_purge_loop(), name="retention_purge_loop"
    )
    yield
    if _github_poll_task is not None:
        _github_poll_task.cancel()
        try:
            await _github_poll_task
        except asyncio.CancelledError:
            pass
        _github_poll_task = None
    if _retention_purge_task is not None:
        _retention_purge_task.cancel()
        try:
            await _retention_purge_task
        except asyncio.CancelledError:
            pass
        _retention_purge_task = None


_start_time: float = time.time()

app = FastAPI(
    title="tools-project API",
    description="Project management hub — backend",
    version="0.1.3",
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


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    start = time.time()
    response = await call_next(request)
    response.headers["X-Request-Id"] = rid
    elapsed = time.time() - start
    log.info("%s %s %s %.0fms", request.method, request.url.path, response.status_code, elapsed * 1000)
    return response

app.include_router(auth.router)
app.include_router(admin_users.router)
app.include_router(projects.router)
app.include_router(project_clients.router)
app.include_router(project_client_access.router)
app.include_router(components.router)
app.include_router(components.detail_router)
app.include_router(tasks.project_router)
app.include_router(tasks.detail_router)
app.include_router(activities.router)
app.include_router(tickets.router)
app.include_router(tickets.detail_router)
app.include_router(attachments.router)
app.include_router(attachments.ticket_router)
app.include_router(attachments.task_router)
app.include_router(attachments.file_router)
app.include_router(me_focus.router)
app.include_router(me_api_keys.router)
app.include_router(inbox.router)
app.include_router(prospects.router)
app.include_router(client_health.router)
app.include_router(clients.router)
app.include_router(client_contacts.router)
app.include_router(client_portal.router)
app.include_router(github.router)
app.include_router(commit_refs.router)
app.include_router(stats.router)
app.include_router(reports.router)
app.include_router(agent_query.router)


@app.get("/healthz")
async def healthz() -> dict[str, object]:
    db_ok = False
    try:
        from app.db import session_factory

        fac = session_factory()
        async with fac() as session:
            await session.execute(select(1))
            db_ok = True
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "ok" if db_ok else "unreachable",
        "version": "0.1.3",
        "uptime_seconds": int(time.time() - _start_time),
    }
