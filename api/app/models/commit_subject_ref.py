from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CommitSubjectRef(Base):
    __tablename__ = "commit_subject_refs"
    __table_args__ = (
        UniqueConstraint(
            "github_commit_id", "subject_type", "subject_id",
            name="uq_commit_subject_refs_commit_subject",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    github_commit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("github_commits.id", ondelete="CASCADE"),
        index=True,
    )
    subject_type: Mapped[str] = mapped_column(String(40))
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    commit = relationship("GithubCommit", lazy="joined")
