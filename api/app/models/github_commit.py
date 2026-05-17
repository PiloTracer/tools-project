from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class GithubCommit(Base):
    __tablename__ = "github_commits"
    __table_args__ = (
        UniqueConstraint("github_link_id", "sha", name="uq_github_commits_link_sha"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    github_link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("github_links.id", ondelete="CASCADE"),
        index=True,
    )
    sha: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text)
    author_name: Mapped[str | None] = mapped_column(String(400), nullable=True)
    author_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    committed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    html_url: Mapped[str] = mapped_column(Text, nullable=False)
    raw_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    link = relationship("GithubLink", back_populates="commits", lazy="joined")
