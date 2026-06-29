from __future__ import annotations

import json
import re
import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# --- Status constants (align with plan §4.1) ---

TASK_STATUSES: frozenset[str] = frozenset({"todo", "in_progress", "blocked", "done", "cancelled"})
TICKET_STATUSES: frozenset[str] = frozenset({"open", "in_progress", "waiting_customer", "resolved", "closed"})
ACTIVITY_KINDS: frozenset[str] = frozenset({
    "comment", "status_change", "assignment", "attachment", "github_commit", "mention", "system",
})


class LocalLoginRequest(BaseModel):
    # Allow development/test domains (e.g. .test) that email-validator rejects.
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1024)

    @field_validator("email")
    @classmethod
    def _validate_login_email(cls, v: str) -> str:
        value = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            raise ValueError("Invalid email address")
        return value


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
    client_contact_id: uuid.UUID | None = None
    client_name: str | None = None

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
    memberships: list["UserMembershipOut"] = Field(default_factory=list)
    client_contacts: list["UserClientContactOut"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    items: list[AdminUserOut]


class UserMembershipOut(BaseModel):
    project_id: uuid.UUID
    project_name: str
    role: str


class UserClientContactOut(BaseModel):
    client_id: uuid.UUID
    client_name: str
    role: str  # contact's descriptive role at the company
    email: str
    name: str


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
    github_task_registry_enabled: bool | None = None
    auto_prefix_enabled: bool | None = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    owner_id: uuid.UUID
    status: str
    project_key: str | None
    github_task_registry_enabled: bool = False
    auto_prefix_enabled: bool = False
    created_at: datetime
    updated_at: datetime
    membership_role: str | None = None
    health: "ProjectHealth | None" = None
    clients_summary: list[ClientSummary] | None = None

    model_config = {"from_attributes": True}


class ProjectHealth(BaseModel):
    open_tasks: int = 0
    open_tickets: int = 0
    oldest_open_ticket_days: int | None = None


class ProjectListResponse(BaseModel):
    items: list[ProjectOut]


class ProjectMemberCreate(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    role: str = Field(min_length=2, max_length=20)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        value = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            raise ValueError("Invalid email address")
        return value


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
    actor_id: uuid.UUID | None = None
    actor_email: str | None = None
    parent_activity_id: uuid.UUID | None = None
    body: str
    meta_json: dict | None = None
    is_internal: bool = False
    created_at: datetime
    subject_ref: str | None = None
    subject_title: str | None = None

    model_config = {"from_attributes": True}


class ActivityListResponse(BaseModel):
    items: list[ActivityOut]


class AttachmentOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    ticket_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
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


class TodayTicketBundle(BaseModel):
    ticket: TicketOut
    project_name: str


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
    watched_tickets: list[TodayTicketBundle] = Field(default_factory=list)


class WatchCreate(BaseModel):
    subject_type: str = Field(pattern=r"^(project|task|ticket)$")
    subject_id: uuid.UUID


class WatchDelete(BaseModel):
    subject_type: str = Field(pattern=r"^(project|task|ticket)$")
    subject_id: uuid.UUID


class WatchOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    subject_type: str
    subject_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchListResponse(BaseModel):
    items: list[WatchOut]


class InboxCreate(BaseModel):
    body_md: str = Field(min_length=1, max_length=8000)


class InboxTriage(BaseModel):
    into: str = Field(pattern=r"^(task|ticket)$")
    project_id: uuid.UUID
    component_id: uuid.UUID | None = None
    priority: str = Field(default="normal", max_length=20)
    assignee_id: uuid.UUID | None = None


class InboxOut(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    body_md: str
    meta_json: dict | None = None
    triaged_to_type: str | None = None
    triaged_to_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InboxListResponse(BaseModel):
    items: list[InboxOut]


class UserSearchResult(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None = None


class UnifiedSearchHit(BaseModel):
    id: str
    label: str
    subtitle: str
    href: str
    kind: str  # "project", "task", "ticket", "client", "prospect"


class TaskBatchUpdate(BaseModel):
    ids: list[uuid.UUID] = Field(min_length=1, max_length=100)
    status: str | None = Field(default=None, max_length=40)
    priority: str | None = Field(default=None, max_length=20)
    assignee_id: uuid.UUID | None = None
    due_at: datetime | None = None


class TicketBatchUpdate(BaseModel):
    ids: list[uuid.UUID] = Field(min_length=1, max_length=100)
    status: str | None = Field(default=None, max_length=40)
    priority: str | None = Field(default=None, max_length=20)
    assignee_id: uuid.UUID | None = None
    queue_slug: str | None = Field(default=None, max_length=80)


class RefSearchResult(BaseModel):
    id: str
    ref: str | None = None
    title: str
    project_id: str
    project_name: str
    kind: str  # "task" or "ticket"


_GITHUB_REPO_URL = re.compile(
    r"^https?://github\.com/([^/]+)/([^/.]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


class GithubLinkCreate(BaseModel):
    """Create a repo link. Supply owner+repo or a github.com URL plus a PAT."""

    owner: str | None = Field(default=None, max_length=200)
    repo: str | None = Field(default=None, max_length=200)
    github_repo_url: str | None = Field(default=None, max_length=500)
    github_token: str = Field(min_length=8, max_length=4000)
    component_id: uuid.UUID | None = None
    poll_interval_seconds: int = Field(default=300, ge=60, le=86400)

    @model_validator(mode="after")
    def _normalize_owner_repo(self) -> GithubLinkCreate:
        owner = self.owner
        repo = self.repo
        if self.github_repo_url:
            m = _GITHUB_REPO_URL.match(self.github_repo_url.strip())
            if not m:
                raise ValueError(
                    "github_repo_url must look like https://github.com/org/repo (GitHub.com only for MVP)"
                )
            owner, repo = m.group(1), m.group(2)
        if not owner or not repo:
            raise ValueError("owner and repo are required unless github_repo_url is set")
        return self.model_copy(
            update={
                "owner": owner.strip().lower(),
                "repo": repo.strip().lower(),
            }
        )


class GithubLinkOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    component_id: uuid.UUID | None = None
    owner: str
    repo: str
    poll_interval_seconds: int
    last_synced_at: datetime | None = None
    last_seen_sha: str | None = None
    sync_status: str = "idle"
    last_error: str | None = None
    last_error_at: datetime | None = None
    error_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GithubSyncResult(BaseModel):
    upserted: int
    owner: str
    repo: str
    linked_refs: int = 0


class GithubSyncStatusItem(BaseModel):
    """Per-link sync health — returned by the sync-status endpoint."""

    link_id: uuid.UUID
    owner: str
    repo: str
    sync_status: str = "idle"
    last_synced_at: datetime | None = None
    last_error: str | None = None
    last_error_at: datetime | None = None
    error_count: int = 0


class GithubSyncStatusResponse(BaseModel):
    items: list[GithubSyncStatusItem]


class CommitSummary(BaseModel):
    """Read model for any UI widget — html_url is always present (see Batch I §I4.1)."""

    id: uuid.UUID
    project_id: uuid.UUID
    project_name: str
    github_link_id: uuid.UUID
    owner: str
    repo: str
    sha: str = Field(..., min_length=7, max_length=40)
    short_sha: str = Field(..., min_length=7, max_length=7)
    message: str
    message_preview: str = Field(..., min_length=1, max_length=400)
    html_url: str = Field(
        ...,
        min_length=8,
        description="Browser URL for this commit (GitHub REST html_url or derived https://github.com/{owner}/{repo}/commit/{sha}).",
    )
    committed_at: datetime
    author_name: str | None = None
    author_email: str | None = None


class GithubCommitListResponse(BaseModel):
    items: list[CommitSummary]


class CommitSubjectRefCreate(BaseModel):
    """Create a ref for a commit that has already been synced (github_commit_id known)."""

    github_commit_id: uuid.UUID
    subject_type: str = Field(pattern=r"^(task|ticket)$")
    subject_id: uuid.UUID


class CommitSubjectRefPendingCreate(BaseModel):
    """Create a ref for a commit that has NOT been synced yet (local SHA only).

    ``project_id`` is inferred from the URL path. ``sha`` is the full 40-char hex SHA.
    ``ref`` is the task/ticket ref string (e.g. ``PROJ-456`` / ``PROJ-T-23``).
    """

    sha: str = Field(
        ..., min_length=40, max_length=40, pattern=r"^[0-9a-f]{40}$"
    )
    ref: str = Field(..., min_length=1, max_length=40)


class CommitBrief(BaseModel):
    """Lightweight commit info embedded in ref responses."""

    sha: str
    short_sha: str
    message_preview: str
    html_url: str
    author_name: str | None = None
    committed_at: datetime
    owner: str
    repo: str


class CommitSubjectRefOut(BaseModel):
    id: uuid.UUID
    github_commit_id: uuid.UUID | None = None
    sha: str | None = None
    project_id: uuid.UUID | None = None
    subject_type: str
    subject_id: uuid.UUID
    subject_ref: str | None = None
    subject_title: str | None = None
    subject_status: str | None = None
    subject_priority: str | None = None
    subject_description: str | None = None
    created_by: uuid.UUID
    created_at: datetime
    commit: CommitBrief | None = None

    model_config = {"from_attributes": True}


class CommitSubjectRefListResponse(BaseModel):
    items: list[CommitSubjectRefOut]


class GithubRefMeta(BaseModel):
    """Use inside activity / task `meta_json` under key `github_ref` (optional future validation)."""

    commit_id: uuid.UUID
    sha: str = Field(min_length=7, max_length=40)
    owner: str = Field(min_length=1, max_length=200)
    repo: str = Field(min_length=1, max_length=200)
    html_url: str = Field(min_length=8, max_length=2000)


# --- CRM: Prospects ---

VALID_PIPELINE_STAGES = frozenset({
    "target", "connected", "engaged", "call_scheduled", "call_done",
    "proposal_sent", "negotiating", "won", "lost",
})
TERMINAL_PIPELINE_STAGES = frozenset({"won", "lost"})


class ProspectCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    pipeline_stage: str = Field(default="target", max_length=20)
    pipeline_value: float | None = Field(default=None, ge=0)
    source: str | None = Field(default=None, max_length=30)
    first_contact_date: date | None = None
    notes: str | None = Field(default=None, max_length=16000)

    @field_validator("pipeline_stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        if v not in VALID_PIPELINE_STAGES:
            raise ValueError(f"Invalid stage: {v}. Must be one of {sorted(VALID_PIPELINE_STAGES)}")
        return v


class ProspectUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=200)
    pipeline_stage: str | None = Field(default=None, max_length=20)
    pipeline_value: float | None = Field(default=None, ge=0)
    source: str | None = Field(default=None, max_length=30)
    first_contact_date: date | None = None
    notes: str | None = Field(default=None, max_length=16000)

    @field_validator("pipeline_stage")
    @classmethod
    def validate_stage(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_PIPELINE_STAGES:
            raise ValueError(f"Invalid stage: {v}. Must be one of {sorted(VALID_PIPELINE_STAGES)}")
        return v


class ProspectStageChange(BaseModel):
    stage: str = Field(..., max_length=20)

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        if v not in VALID_PIPELINE_STAGES:
            raise ValueError(f"Invalid stage: {v}. Must be one of {sorted(VALID_PIPELINE_STAGES)}")
        return v


class ProspectOut(BaseModel):
    id: uuid.UUID
    company_name: str
    pipeline_stage: str
    pipeline_value: float | None = None
    source: str | None = None
    first_contact_date: date | None = None
    last_interaction: datetime | None = None
    next_action: str | None = None
    next_action_date: date | None = None
    notes: str | None = None
    client_id: uuid.UUID | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProspectStageChangeResponse(ProspectOut):
    promoted_client: ClientOut | None = None


class ProspectListResponse(BaseModel):
    items: list[ProspectOut]


# --- M2: Clients + Contacts ---

def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")[:80]
    return s or "client"


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    industry: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=16000)


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    industry: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=16000)


class ClientOut(BaseModel):
    id: uuid.UUID
    prospect_id: uuid.UUID | None = None
    name: str
    slug: str
    industry: str | None = None
    notes: str | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClientListResponse(BaseModel):
    items: list[ClientOut]


class ClientContactCreate(BaseModel):
    prospect_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(max_length=320)
    phone: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, max_length=200)
    role: str = Field(default="contact", max_length=30)
    is_primary: bool = False
    notes: str | None = Field(default=None, max_length=16000)


class ClientContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, max_length=200)
    role: str | None = Field(default=None, max_length=30)
    is_primary: bool | None = None
    notes: str | None = Field(default=None, max_length=16000)
    user_id: uuid.UUID | None = None


class ClientContactOut(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    prospect_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    user_email: str | None = None
    user_name: str | None = None
    name: str
    email: str
    phone: str | None = None
    title: str | None = None
    role: str
    is_primary: bool
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClientContactListResponse(BaseModel):
    items: list[ClientContactOut]


# --- M3: Project-client linking & access ---


class ProjectClientLinkRequest(BaseModel):
    client_id: uuid.UUID


class ProjectClientOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    client_id: uuid.UUID
    client_name: str
    client_slug: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectClientListResponse(BaseModel):
    items: list[ProjectClientOut]


class ProjectClientSearchHit(BaseModel):
    client_id: uuid.UUID
    client_name: str
    client_slug: str
    contact_name: str | None = None
    contact_email: str | None = None


class ProjectClientSearchResponse(BaseModel):
    items: list[ProjectClientSearchHit]


class ClientSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str


class ClientAccessCreate(BaseModel):
    client_contact_id: uuid.UUID
    role: str = "view"
    can_create_tasks: bool = False


class ClientAccessUpdate(BaseModel):
    role: str | None = None
    can_view_tasks: bool | None = None
    can_view_tickets: bool | None = None
    can_create_tasks: bool | None = None


class ClientAccessOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    client_contact_id: uuid.UUID
    contact_name: str | None = None
    contact_email: str | None = None
    client_id: uuid.UUID | None = None
    client_name: str | None = None
    role: str
    can_view_tasks: bool
    can_view_tickets: bool
    can_create_tasks: bool
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ClientAccessListResponse(BaseModel):
    items: list[ClientAccessOut]


class ProjectClientContactOut(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    client_name: str | None = None
    name: str
    email: str
    phone: str | None = None
    title: str | None = None
    role: str
    is_primary: bool

    model_config = {"from_attributes": True}


class ProjectClientContactListResponse(BaseModel):
    items: list[ProjectClientContactOut]


class MyStatsOut(BaseModel):
    open_tasks: int
    overdue_tasks: int
    done_this_week: int
    inbox_count: int
    mention_count: int
    open_tickets: int


class PipelineStageStats(BaseModel):
    stage: str
    label: str
    count: int
    value: float


class PipelineStatsOut(BaseModel):
    by_stage: list[PipelineStageStats]
    total_value: float
    won_value: float
    lost_value: float
    conversion_rate: float | None
    needs_attention_count: int = 0


class GlobalStatsOut(BaseModel):
    total_projects: int
    active_projects: int
    open_tasks: int
    open_tickets: int
    total_prospects: int
    total_clients: int
