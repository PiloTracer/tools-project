"""Prospect-to-client promotion and pipeline helpers."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.project import Project
from app.models.project_client import ProjectClient
from app.models.project_client_access import ProjectClientAccess
from app.models.project_member import ProjectMember
from app.models.prospect import Prospect
from app.models.task import Task
from app.models.user import User
from app.schemas import slugify
from app.services.project_access import MemberRole

ONBOARDING_TASKS: list[str] = [
    "Welcome and introduction call",
    "Contract and paperwork",
    "Deposit or initial payment",
    "Repository and tooling setup",
    "Communication channel setup",
    "First milestone planning",
    "Stakeholder introductions",
]


async def ensure_unique_client_slug(db: AsyncSession, company_name: str) -> str:
    """Generate a unique slug for a client based on the company name."""
    client_slug = slugify(company_name)
    existing = await db.scalar(select(Client).where(Client.slug == client_slug))
    if not existing:
        return client_slug
    for i in range(1, 100):
        candidate = f"{client_slug}-{i}"
        dup = await db.scalar(select(Client).where(Client.slug == candidate))
        if not dup:
            return candidate
    raise ValueError("Could not allocate a unique client slug")


async def _unique_onboarding_slug(db: AsyncSession, base: str) -> str:
    """Generate a unique project slug for an onboarding project."""
    candidate = base[:80]
    for _ in range(24):
        existing = await db.scalar(select(Project).where(Project.slug == candidate))
        if existing is None:
            return candidate
        suffix = uuid.uuid4().hex[:6]
        trimmed = base[: max(1, 80 - 7 - len(suffix))]
        candidate = f"{trimmed}-{suffix}"
    raise ValueError("Could not allocate a unique onboarding project slug")


async def auto_scaffold_onboarding_project(
    db: AsyncSession,
    client: Client,
    prospect: Prospect,
    promoting_user_id: uuid.UUID,
) -> Project:
    """Auto-create an onboarding project when a prospect is promoted to client.

    Creates:
      - Project named "{company_name} Onboarding"
      - Owner membership for the promoting user
      - Project-client link
      - Onboarding tasks
      - Client access grants for contacts with user accounts
      - Activity entry recording the conversion
    """
    base_slug = slugify(f"{prospect.company_name}-onboarding")
    slug = await _unique_onboarding_slug(db, base_slug)

    project = Project(
        name=f"{prospect.company_name} Onboarding",
        slug=slug,
        description=f"Onboarding project for {prospect.company_name} — auto-created from prospect promotion.",
        owner_id=promoting_user_id,
        status="active",
        project_key=None,
    )
    db.add(project)
    await db.flush()

    db.add(
        ProjectMember(
            project_id=project.id,
            user_id=promoting_user_id,
            role=MemberRole.owner.value,
        )
    )

    db.add(
        ProjectClient(
            project_id=project.id,
            client_id=client.id,
            created_by=promoting_user_id,
        )
    )

    for title in ONBOARDING_TASKS:
        db.add(
            Task(
                project_id=project.id,
                title=title,
                status="todo",
                priority="normal",
                reporter_id=promoting_user_id,
            )
        )

    contacts = (
        await db.execute(
            select(ClientContact).where(
                ClientContact.client_id == client.id,
                ClientContact.user_id.isnot(None),
            )
        )
    ).scalars().all()

    for contact in contacts:
        db.add(
            ProjectClientAccess(
                project_id=project.id,
                client_contact_id=contact.id,
                role="contribute",
                can_view_tasks=True,
                can_view_tickets=True,
                can_create_tasks=True,
                created_by=promoting_user_id,
            )
        )

    promoter = await db.get(User, promoting_user_id)
    promoter_name = promoter.display_name or promoter.email if promoter else "System"

    db.add(
        Activity(
            project_id=project.id,
            subject_type="project",
            subject_id=project.id,
            kind="system",
            actor_id=promoting_user_id,
            body=f"{promoter_name} converted {prospect.company_name} to a client and created this onboarding project",
            is_internal=True,
        )
    )

    return project


async def promote_prospect_to_client(
    db: AsyncSession,
    prospect: Prospect,
    *,
    created_by: uuid.UUID | None = None,
) -> Client:
    """Transactional promotion: when a prospect reaches `won`, create the client record.

    Args:
        db: active async SQLAlchemy session.
        prospect: the prospect being promoted (must already be in `won` stage).
        created_by: user ID to record as creator. Defaults to the prospect's creator.

    Returns:
        The newly created Client instance (already added to the session, not committed).
    """
    if prospect.pipeline_stage != "won":
        raise ValueError("Prospect must be in 'won' stage to promote to client")

    client_slug = await ensure_unique_client_slug(db, prospect.company_name)
    client = Client(
        name=prospect.company_name,
        slug=client_slug,
        prospect_id=prospect.id,
        created_by=created_by or prospect.created_by,
    )
    db.add(client)
    return client
