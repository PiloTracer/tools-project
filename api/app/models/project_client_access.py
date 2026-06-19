from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


CLIENT_ROLES = frozenset({"view", "contribute", "decision_maker", "billing"})


class ProjectClientAccess(Base):
    __tablename__ = "project_client_access"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    client_contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("client_contacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(30), default="view")
    can_view_tasks: Mapped[bool] = mapped_column(Boolean, default=True)
    can_view_tickets: Mapped[bool] = mapped_column(Boolean, default=False)
    can_create_tasks: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project = relationship("Project", lazy="joined")
    client_contact = relationship("ClientContact", lazy="joined")
    creator = relationship("User", lazy="joined")
