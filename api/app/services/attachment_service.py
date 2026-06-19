"""Attachment lifecycle operations (retention purge, quota helpers)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.attachment_storage import purge_expired_attachments


__all__ = ["purge_expired_attachments"]


async def run_attachment_retention_purge(db: AsyncSession) -> int:
    """Delete attachments older than the retention cutoff.

    Safe to call repeatedly; returns the number of attachments purged.
    """
    return await purge_expired_attachments(db)
