import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import run_bootstrap
from app.db import get_engine, init_db, session_factory
from app.schema_sql import run_post_bootstrap
from app.routers import activities, admin_users, attachments, auth, components, inbox, me_focus, projects, tasks, tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    fac = session_factory()
    async with fac() as session:
        await run_bootstrap(session)
    async with get_engine().begin() as conn:
        await run_post_bootstrap(conn)
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
app.include_router(projects.router)
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


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
