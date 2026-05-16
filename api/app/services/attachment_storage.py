from __future__ import annotations

import os
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
