"""Shared helpers for CRM org/contact profile fields on prospects and clients."""

from __future__ import annotations

from typing import Any


def blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def email_or_none(value: str | None) -> str | None:
    trimmed = blank_to_none(value)
    return trimmed.lower() if trimmed else None


PROSPECT_PROFILE_KEYS = (
    "industry",
    "zone",
    "contact_name",
    "contact_email",
    "contact_phone",
    "org_email",
    "org_phone",
    "working_schedule",
    "message",
    "service",
    "address",
    "latitude",
    "longitude",
)

CLIENT_PROFILE_KEYS = (
    "zone",
    "source",
    "email",
    "phone",
    "working_schedule",
    "message",
    "service",
    "address",
    "latitude",
    "longitude",
)

_EMAIL_KEYS = frozenset({"contact_email", "org_email", "email"})
_TEXT_KEYS = frozenset(
    {
        "industry",
        "zone",
        "source",
        "contact_name",
        "contact_phone",
        "org_phone",
        "phone",
        "working_schedule",
        "message",
        "service",
        "address",
    }
)


def profile_kwargs(body: Any, keys: tuple[str, ...]) -> dict[str, Any]:
    """Extract create-time profile fields from a Pydantic body."""
    out: dict[str, Any] = {}
    for key in keys:
        raw = getattr(body, key, None)
        if key in _EMAIL_KEYS:
            out[key] = email_or_none(raw)
        elif key in _TEXT_KEYS:
            out[key] = blank_to_none(raw)
        else:
            out[key] = raw
    return out


def apply_profile_update(row: Any, body: Any, keys: tuple[str, ...]) -> None:
    """Apply PATCH fields; omitted keys stay unchanged; empty strings clear to NULL."""
    for key in keys:
        if not hasattr(body, key):
            continue
        raw = getattr(body, key)
        # Pydantic optional: None means "omit" for create defaults, but for update
        # we only touch fields that were explicitly provided.
        fields_set = getattr(body, "model_fields_set", None)
        if fields_set is not None and key not in fields_set:
            continue
        if key in _EMAIL_KEYS:
            setattr(row, key, email_or_none(raw) if isinstance(raw, str) or raw is None else raw)
        elif key in _TEXT_KEYS:
            setattr(row, key, blank_to_none(raw) if isinstance(raw, str) or raw is None else raw)
        else:
            setattr(row, key, raw)
