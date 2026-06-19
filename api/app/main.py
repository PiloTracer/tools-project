import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import run_bootstrap
from app.config import get_settings
from app.db import get_engine, init_db, session_factory
from app.github_background import github_poll_loop
from app.schema_sql import run_post_bootstrap
from app.routers import (
    activities,
    admin_users,
    attachments,
    auth,
    client_contacts,
    client_portal,
    clients,
    components,
    github,
    inbox,
    me_focus,
    projects,
    prospects,
    tasks,
    tickets,
)


_github_poll_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _github_poll_task
    await init_db()
    fac = session_factory()
    async with fac() as session:
        await run_bootstrap(session)
    async with get_engine().begin() as conn:
        await run_post_bootstrap(conn)
    if get_settings().github_sync_enabled:
        _github_poll_task = asyncio.create_task(github_poll_loop(), name="github_poll_loop")
    yield
    if _github_poll_task is not None:
        _github_poll_task.cancel()
        try:
            await _github_poll_task
        except asyncio.CancelledError:
            pass
        _github_poll_task = None


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
app.include_router(inbox.router)
app.include_router(prospects.router)
app.include_router(clients.router)
app.include_router(client_contacts.router)
app.include_router(client_portal.router)
app.include_router(github.router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
