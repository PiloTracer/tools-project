"""Append-only CRM field history and a small custom-field object."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planning import CrmFieldChange

_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,40}$")


def clean_custom_fields(raw: dict | None) -> dict[str, str]:
    """Keep a flat string map. Unknown shapes become an empty object."""
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in list(raw.items())[:40]:
        if not isinstance(key, str) or not _KEY_RE.match(key):
            continue
        if value is None:
            continue
        if isinstance(value, dict | list):
            continue
        text = str(value).strip()
        if text:
            out[key] = text[:500]
    return out


def as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = json.dumps(value, sort_keys=True, default=str) if isinstance(value, dict) else str(value)
    text = text.strip()
    return text[:500] if text else None


def record_changes(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    before: dict[str, str | None],
    after: dict[str, str | None],
) -> None:
    for field, old in before.items():
        new = after.get(field)
        if old == new:
            continue
        db.add(
            CrmFieldChange(
                tenant_id=tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                actor_id=actor_id,
                field_name=field,
                old_value=old,
                new_value=new,
            )
        )
