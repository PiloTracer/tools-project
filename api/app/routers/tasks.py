from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.component import Component
from app.models.task import Task
from app.models.user import User
from app.schemas import (
    TASK_STATUSES,
    TaskBatchUpdate,
    TaskCreate,
    TaskListResponse,
    TaskOut,
    TaskPatch,
    TaskTransition,
)
from app.services.activity_writer import write_activity
from app.services.github_task_registry import (
    spawn_push_task_ref,
)
from app.services.github_task_registry import (
    spawn_remove_ref as spawn_remove_task_ref,
)
from app.services.project_access import (
    can_create_tasks,
    can_edit_tasks,
    can_view_tasks,
    client_company_user_ids,
    is_client_participant,
    require_project_access,
)
from app.services.ref_alloc import allocate_ref
from app.services.webhook_dispatcher import dispatch_event

project_router = APIRouter(
    prefix="/v1/projects/{project_id}/tasks",
    tags=["tasks"],
)
detail_router = APIRouter(prefix="/v1/tasks", tags=["tasks"])

_TERMINAL_TASK_STATUSES: frozenset[str] = frozenset({"done", "cancelled"})


async def _require_task_project(task: Task, user: User, db: AsyncSession):
    acc = await require_project_access(db, user, task.project_id)
    return acc


@project_router.get("", response_model=TaskListResponse)
async def list_tasks(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    task_status: str | None = Query(default=None, alias="status"),
    assignee_id: uuid.UUID | None = None,
    component_id: uuid.UUID | None = None,
    is_todo: bool | None = Query(default=None),
    q: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    acc = await require_project_access(db, user, project_id)
    if not can_view_tasks(acc):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view tasks in this project",
        )

    base = select(Task).where(Task.project_id == project_id)
    if q:
        like = f"%{q.strip()}%"
        base = base.where(or_(Task.title.ilike(like), Task.ref.ilike(like)))
    if task_status:
        base = base.where(Task.status == task_status.strip())
    if assignee_id is not None:
        base = base.where(Task.assignee_id == assignee_id)
    if component_id is not None:
        base = base.where(Task.component_id == component_id)
    if is_todo is not None:
        base = base.where(Task.is_todo == is_todo)
    if is_client_participant(acc):
        peer_ids = await client_company_user_ids(db, acc)
        base = base.where(Task.assignee_id.in_(peer_ids))

    total = (await db.scalar(base.with_only_columns(func.count()).order_by(None))) or 0

    stmt = base.order_by(Task.updated_at.desc()).offset(offset).limit(limit)
    result = await db.scalars(stmt)
    rows = list(result.all())
    return TaskListResponse(
        items=[TaskOut.model_validate(r) for r in rows],
        total=total,
        has_more=(offset + len(rows)) < total,
    )


@project_router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: uuid.UUID,
    body: TaskCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acc = await require_project_access(db, user, project_id)
    if not can_create_tasks(acc):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create tasks in this project",
        )
    if body.component_id is not None:
        comp = await db.get(Component, body.component_id)
        if comp is None or comp.project_id != project_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="component_id must belong to this project",
            )
    if body.parent_task_id is not None:
        parent = await db.get(Task, body.parent_task_id)
        if parent is None or parent.project_id != project_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="parent_task_id must belong to this project",
            )
    status_val = body.status.strip()
    if status_val not in TASK_STATUSES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_val}. Use one of {sorted(TASK_STATUSES)}",
        )
    ref = await allocate_ref(db, project_id, "task")
    closed_at = datetime.now(UTC) if status_val in _TERMINAL_TASK_STATUSES else None
    row = Task(
        project_id=project_id,
        component_id=body.component_id,
        ref=ref,
        title=body.title.strip(),
        description=body.description.strip() if body.description else None,
        status=status_val,
        priority=body.priority.strip(),
        assignee_id=body.assignee_id,
        reporter_id=user.id,
        due_at=body.due_at,
        parent_task_id=body.parent_task_id,
        is_todo=body.is_todo,
        closed_at=closed_at,
    )
    db.add(row)
    await db.flush()
    await write_activity(
        db=db,
        project_id=project_id,
        subject_type="task",
        subject_id=row.id,
        kind="system",
        actor_id=user.id,
        body=f"Task created: {row.title}",
    )
    await db.commit()
    await db.refresh(row)
    if row.ref:
        spawn_push_task_ref(project_id, row.ref, row.title, row.status, row.description)
    return TaskOut.model_validate(row)


@detail_router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Task, task_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    await _require_task_project(row, user, db)
    return TaskOut.model_validate(row)


@detail_router.patch("/{task_id}", response_model=TaskOut)
async def patch_task(
    task_id: uuid.UUID,
    body: TaskPatch,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Task, task_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    acc = await _require_task_project(row, user, db)
    if not can_edit_tasks(acc):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit tasks in this project",
        )
    if body.component_id is not None:
        comp = await db.get(Component, body.component_id)
        if comp is None or comp.project_id != row.project_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="component_id must belong to this project",
            )
    if body.parent_task_id is not None:
        parent = await db.get(Task, body.parent_task_id)
        if parent is None or parent.project_id != row.project_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="parent_task_id must belong to this project",
            )
    if body.title is not None:
        row.title = body.title.strip()
    if body.description is not None:
        v = body.description.strip()
        row.description = v if v else None
    _prev_status = row.status
    _prev_assignee = row.assignee_id
    if body.status is not None:
        status_val = body.status.strip()
        if status_val not in TASK_STATUSES:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_val}. Use one of {sorted(TASK_STATUSES)}",
            )
        row.status = status_val
        if status_val in _TERMINAL_TASK_STATUSES:
            row.closed_at = datetime.now(UTC)
        else:
            row.closed_at = None
    if body.priority is not None:
        row.priority = body.priority.strip()
    if body.component_id is not None:
        row.component_id = body.component_id
    if body.assignee_id is not None:
        row.assignee_id = body.assignee_id
    if body.due_at is not None:
        row.due_at = body.due_at
    if body.parent_task_id is not None:
        row.parent_task_id = body.parent_task_id
    if body.is_todo is not None:
        row.is_todo = body.is_todo
    await db.flush()
    if body.status is not None and _prev_status != row.status:
        await write_activity(
            db=db,
            project_id=row.project_id,
            subject_type="task",
            subject_id=row.id,
            kind="status_change",
            actor_id=user.id,
            body=f"Status changed from {_prev_status} to {row.status}",
        )
    if body.assignee_id is not None and _prev_assignee != row.assignee_id:
        await write_activity(
            db=db,
            project_id=row.project_id,
            subject_type="task",
            subject_id=row.id,
            kind="assignment",
            actor_id=user.id,
            body="Assignee changed",
        )
    await db.commit()
    await db.refresh(row)
    if row.ref:
        spawn_push_task_ref(row.project_id, row.ref, row.title, row.status, row.description)
    return TaskOut.model_validate(row)


@detail_router.post("/{task_id}/transition", response_model=TaskOut)
async def transition_task(
    task_id: uuid.UUID,
    body: TaskTransition,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Task, task_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    acc = await _require_task_project(row, user, db)
    if not can_edit_tasks(acc):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to change task status",
        )
    status_val = body.status.strip()
    if status_val not in TASK_STATUSES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_val}. Use one of {sorted(TASK_STATUSES)}",
        )
    prev = row.status
    row.status = status_val
    if status_val in _TERMINAL_TASK_STATUSES:
        row.closed_at = datetime.now(UTC)
    else:
        row.closed_at = None
    await db.flush()
    if prev != status_val:
        await write_activity(
            db=db,
            project_id=row.project_id,
            subject_type="task",
            subject_id=row.id,
            kind="status_change",
            actor_id=user.id,
            body=f"Status changed from {prev} to {status_val}",
        )
    await db.commit()
    await db.refresh(row)
    if row.ref:
        spawn_push_task_ref(row.project_id, row.ref, row.title, row.status, row.description)
    if status_val == "done" and prev != "done":
        dispatch_event("task.done", {
            "task_id": str(row.id),
            "project_id": str(row.project_id),
            "title": row.title,
            "ref": row.ref,
        })
    return TaskOut.model_validate(row)


@detail_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Task, task_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    acc = await _require_task_project(row, user, db)
    if not can_edit_tasks(acc):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete tasks",
        )
    ref = row.ref
    await db.delete(row)
    await db.commit()
    if ref:
        spawn_remove_task_ref(row.project_id, ref)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@detail_router.post("/batch", response_model=list[TaskOut])
async def batch_update_tasks(
    body: TaskBatchUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Batch update multiple tasks — status, priority, assignee, or due_at."""
    rows = list((await db.scalars(
        select(Task).where(Task.id.in_(body.ids))
    )).all())

    if not rows:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No tasks found")

    # Verify access to all tasks
    project_ids = {r.project_id for r in rows}
    for pid in project_ids:
        acc = await require_project_access(db, user, pid)
        if not can_edit_tasks(acc):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to edit tasks in project {pid}",
            )

    updated: list[Task] = []
    now = datetime.now(UTC)
    for row in rows:
        changed = False
        if body.status is not None:
            status_val = body.status.strip()
            if status_val not in TASK_STATUSES:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_val}. Use one of {sorted(TASK_STATUSES)}",
                )
            row.status = status_val
            if status_val in {"done", "cancelled"}:
                row.closed_at = now
            else:
                row.closed_at = None
            changed = True
        if body.priority is not None:
            row.priority = body.priority.strip()
            changed = True
        if body.assignee_id is not None:
            row.assignee_id = body.assignee_id
            changed = True
        if body.due_at is not None:
            row.due_at = body.due_at
            changed = True
        if changed:
            updated.append(row)

    await db.commit()
    for row in updated:
        await db.refresh(row)
        if row.ref:
            spawn_push_task_ref(row.project_id, row.ref, row.title, row.status, row.description)
    return [TaskOut.model_validate(r) for r in updated]
