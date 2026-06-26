from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CommitSubjectRef(Base):
    """Links a commit (by id or by sha+project_id) to a task/ticket subject.

    Two lifecycle states:
      - **Pending** (``github_commit_id IS NULL``): created by post-commit hook
        before the commit has been synced from GitHub.  The link exists solely
        via ``sha`` + ``project_id``.
      - **Resolved** (``github_commit_id IS NOT NULL``): the commit has been
        synced into ``github_commits`` and the FK points to the real row.
    """

    __tablename__ = "commit_subject_refs"
    # NOTE: Partial unique indexes are defined in sql/schema_indexes.sql
    # (uq_commit_subject_refs_commit_subject for resolved,
    #  uq_commit_subject_refs_pending for pending).
    # The model omits __table_args__ because SQLAlchemy can't express
    # partial unique constraints portably with nullable columns here.

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    github_commit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("github_commits.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sha: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
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
