from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

PIPELINE_STAGES = frozenset({
    "target", "connected", "engaged", "call_scheduled", "call_done",
    "proposal_sent", "negotiating", "won", "lost",
})

PIPELINE_STAGE_ORDER = (
    "target",
    "connected",
    "engaged",
    "call_scheduled",
    "call_done",
    "proposal_sent",
    "negotiating",
    "won",
    "lost",
)

TERMINAL_STAGES = frozenset({"won", "lost"})


class Prospect(Base):
    __tablename__ = "prospects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_name: Mapped[str] = mapped_column(String(200))
    pipeline_stage: Mapped[str] = mapped_column(String(20), default="target")
    pipeline_value: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    source: Mapped[str | None] = mapped_column(String(30), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    zone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_contact_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_interaction: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_action_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    org_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    org_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    working_schedule: Mapped[str | None] = mapped_column(Text, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    service: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    creator = relationship("User", lazy="joined")
    tenant = relationship("Tenant", lazy="joined")
