from __future__ import annotations

import json
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Status constants (align with plan §4.1) ---

TASK_STATUSES: frozenset[str] = frozenset({"todo", "in_progress", "blocked", "done", "cancelled"})
TICKET_STATUSES: frozenset[str] = frozenset({"open", "in_progress", "waiting_customer", "resolved", "closed"})
ACTIVITY_KINDS: frozenset[str] = frozenset({
    "comment", "status_change", "assignment", "attachment", "github_commit", "mention", "system",
})


class LocalLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    avatar_url: str | None = None
    is_superuser: bool
    auth: str = "local"

    model_config = {"from_attributes": True}


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=1024)
    display_name: str | None = None
    is_superuser: bool = False


class AdminUserUpdate(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=1024)
    display_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class AdminUserOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    avatar_url: str | None = None
    auth_source: str = "local"
    is_active: bool
    is_superuser: bool

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    items: list[AdminUserOut]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=8000)
    slug: str | None = Field(
        default=None,
        max_length=80,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=8000)
    status: str | None = Field(
        default=None,
        pattern=r"^(active|archived)$",
    )
    project_key: str | None = Field(
        default=None,
        max_length=32,
        pattern=r"^[A-Za-z0-9_-]+$",
    )


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    owner_id: uuid.UUID
    status: str
    project_key: str | None
    created_at: datetime
    updated_at: datetime
    membership_role: str | None = None

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    items: list[ProjectOut]


class ProjectMemberCreate(BaseModel):
    email: EmailStr
    role: str = Field(min_length=2, max_length=20)


class ProjectMemberPatch(BaseModel):
    role: str = Field(min_length=2, max_length=20)


class ProjectMemberOut(BaseModel):
    user_id: uuid.UUID
    email: str
    display_name: str | None
    role: str
    created_at: datetime


class ProjectMemberListResponse(BaseModel):
    items: list[ProjectMemberOut]


class ComponentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    key: str | None = Field(default=None, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")
    description: str | None = Field(default=None, max_length=8000)
    lead_user_id: uuid.UUID | None = None


class ComponentPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    key: str | None = Field(default=None, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")
    description: str | None = Field(default=None, max_length=8000)
    lead_user_id: uuid.UUID | None = None


class ComponentOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    key: str | None = None
    name: str
    description: str | None
    lead_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComponentListResponse(BaseModel):
    items: list[ComponentOut]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=32000)
    status: str = Field(default="todo", max_length=40)
    priority: str = Field(default="normal", max_length=20)
    component_id: uuid.UUID | None = None
    assignee_id: uuid.UUID | None = None
    due_at: datetime | None = None
    parent_task_id: uuid.UUID | None = None
    is_todo: bool = False


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=32000)
    status: str | None = Field(default=None, max_length=40)
    priority: str | None = Field(default=None, max_length=20)
    component_id: uuid.UUID | None = None
    assignee_id: uuid.UUID | None = None
    due_at: datetime | None = None
    parent_task_id: uuid.UUID | None = None
    is_todo: bool | None = None


class TaskTransition(BaseModel):
    status: str = Field(min_length=1, max_length=40)


class TaskOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    component_id: uuid.UUID | None
    ref: str | None = None
    title: str
    description: str | None
    status: str
    priority: str
    assignee_id: uuid.UUID | None
    reporter_id: uuid.UUID
    due_at: datetime | None
    parent_task_id: uuid.UUID | None
    is_todo: bool
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    items: list[TaskOut]


# --- Batch F: activity, tickets, /me today & mentions ---


class ActivityCreate(BaseModel):
    subject_type: str = Field(pattern=r"^(project|task|ticket)$")
    subject_id: uuid.UUID
    kind: str = Field(default="comment", max_length=40)
    parent_activity_id: uuid.UUID | None = None
    body: str = Field(default="", max_length=8000)
    meta_json: dict | None = None
    is_internal: bool = False

    @field_validator("meta_json")
    @classmethod
    def _meta_json_size(cls, v: dict | None) -> dict | None:
        if v is None:
            return v
        raw = json.dumps(v, separators=(",", ":"))
        if len(raw) > 8192:
            raise ValueError("meta_json exceeds max serialized size (8192 bytes)")
        return v


class ActivityOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    subject_type: str
    subject_id: uuid.UUID
    kind: str = "comment"
    actor_id: uuid.UUID
    actor_email: str | None = None
    parent_activity_id: uuid.UUID | None = None
    body: str
    meta_json: dict | None = None
    is_internal: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityListResponse(BaseModel):
    items: list[ActivityOut]


class AttachmentOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    ticket_id: uuid.UUID
    activity_id: uuid.UUID | None = None
    filename: str
    mime: str
    size_bytes: int
    storage_key: str
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=32000)
    status: str = Field(default="open", max_length=40)
    priority: str = Field(default="normal", max_length=20)
    queue_slug: str = Field(default="default", max_length=80)
    requester_email: str | None = None
    assignee_id: uuid.UUID | None = None


class TicketPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=32000)
    status: str | None = Field(default=None, max_length=40)
    priority: str | None = Field(default=None, max_length=20)
    queue_slug: str | None = Field(default=None, max_length=80)
    requester_email: str | None = None
    assignee_id: uuid.UUID | None = None


class TicketTransition(BaseModel):
    status: str = Field(min_length=1, max_length=40)


class TicketOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    ref: str | None = None
    title: str
    description: str | None
    status: str
    priority: str
    queue_slug: str
    requester_email: str | None = None
    reporter_id: uuid.UUID
    assignee_id: uuid.UUID | None
    first_response_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    items: list[TicketOut]


class MentionWithContext(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    project_name: str
    activity_id: uuid.UUID
    excerpt: str
    created_at: datetime


class MentionListResponse(BaseModel):
    items: list[MentionWithContext]


class TodayTaskBundle(BaseModel):
    task: TaskOut
    project_name: str


class TodayResponse(BaseModel):
    items: list[TodayTaskBundle]
