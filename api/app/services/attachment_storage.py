from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path


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
    return datetime.now(timezone.utc) - timedelta(days=days)
