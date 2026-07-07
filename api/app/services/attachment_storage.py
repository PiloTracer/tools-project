from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)


def attachments_dir() -> Path:
    raw = os.environ.get("ATTACHMENTS_DIR", "/data/attachments").strip()
    return Path(raw).expanduser()


def ensure_dir() -> Path:
    d = attachments_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def path_for_key(storage_key: str) -> Path:
    """Resolve on-disk path; rejects path traversal."""
    key = storage_key.strip()
    if not key or "/" in key or "\\" in key or key.startswith("."):
        raise ValueError("invalid storage_key")
    return ensure_dir() / key


def retention_cutoff(days: int | None = None) -> datetime | None:
    """Return the earliest ``created_at`` that should be retained.

    Attachments older than this date are candidates for cleanup by a
    scheduled maintenance job.  ``days`` comes from the deployment setting
    ``ATTACHMENT_RETENTION_DAYS``; set to 0 to never expire (returns None).
    """
    import os as _os

    if days is None:
        days = int(_os.environ.get("ATTACHMENT_RETENTION_DAYS", "0") or "0")
    if days <= 0:
        return None
    return datetime.now(UTC) - timedelta(days=days)


async def purge_expired_attachments(db: AsyncSession) -> int:
    """Delete attachments older than the retention cutoff from disk and DB."""
    from sqlalchemy import select

    from app.models.attachment import Attachment

    cutoff = retention_cutoff()
    if cutoff is None:
        return 0
    stmt = select(Attachment).where(Attachment.created_at < cutoff)
    rows = list((await db.scalars(stmt)).all())
    purged = 0
    for att in rows:
        try:
            p = path_for_key(att.storage_key)
            if p.exists():
                p.unlink()
        except OSError as exc:
            log.warning("Failed to delete attachment file %s: %s", att.storage_key, exc)
        await db.delete(att)
        purged += 1
    await db.flush()
    return purged
