"""CLI to backfill the GitHub task registry for existing tasks/tickets.

Usage:
    python -m app.cli_registry_backfill <project_id>

Scans all tasks and tickets with refs for the given project and pushes
them to the GitHub task registry file. Safe to re-run (idempotent).
"""

from __future__ import annotations

import asyncio
import sys
import uuid

from sqlalchemy import select

from app.db import session_factory
from app.models.project import Project
from app.models.task import Task
from app.models.ticket import Ticket
from app.services.github_task_registry import (
    push_task_ref,
    push_ticket_ref,
)


async def backfill_project(project_id: uuid.UUID) -> int:
    """Push all existing task/ticket refs to the GitHub registry.

    Returns the total number of refs pushed.
    """
    async with session_factory()() as db:
        proj = await db.get(Project, project_id)
        if proj is None:
            print(f"Project {project_id} not found.")
            return 0

        print(f"Project: {proj.name} (key={proj.project_key})")
        print(f"  github_task_registry_enabled={proj.github_task_registry_enabled}")
        if not proj.github_task_registry_enabled:
            print("  WARNING: registry is disabled — pushes will be skipped.")

        tasks = (
            await db.scalars(
                select(Task).where(
                    Task.project_id == project_id,
                    Task.ref.isnot(None),
                )
            )
        ).all()
        tickets = (
            await db.scalars(
                select(Ticket).where(
                    Ticket.project_id == project_id,
                    Ticket.ref.isnot(None),
                )
            )
        ).all()

        pushed = 0
        for t in tasks:
            ok = await push_task_ref(db, project_id, t.ref, t.title, t.status)
            if ok is not None:
                print(f"  task {t.ref}: {'pushed' if ok else 'skipped (no registry access)'}")
                if ok:
                    pushed += 1
            else:
                pushed += 1

        for t in tickets:
            ok = await push_ticket_ref(db, project_id, t.ref, t.title, t.status)
            if ok is not None:
                print(f"  ticket {t.ref}: {'pushed' if ok else 'skipped (no registry access)'}")
                if ok:
                    pushed += 1
            else:
                pushed += 1

        print(f"\nDone. {pushed} ref(s) pushed.")
        return pushed


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        sys.stderr.write(
            "usage: python -m app.cli_registry_backfill <project_uuid>\n"
            "  Scans all tasks/tickets with refs and pushes them to GitHub registry.\n"
        )
        return 2

    try:
        project_id = uuid.UUID(argv[0])
    except ValueError:
        sys.stderr.write(f"Invalid project UUID: {argv[0]}\n")
        return 2

    asyncio.run(backfill_project(project_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
