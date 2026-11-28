"""User UI preferences — durable across sessions (stored on users.ui_preferences)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Lean defaults: org name is always shown in the form (not listed here).
# Giro / Zona / Fuente and primary contact are on; heavy intake fields stay off.
DEFAULT_CRM_FORM_FIELDS: dict[str, bool] = {
    "pipeline_stage": True,
    "pipeline_value": False,
    "source": True,  # Fuente
    "industry": True,  # Giro de negocio
    "zone": True,  # Zona
    "contact_name": True,
    "contact_email": True,
    "contact_phone": True,
    "org_email": False,
    "org_phone": False,
    "working_schedule": False,
    "message": False,
    "service": False,
    "address": False,
    "coordinates": False,
    "notes": False,
}

CRM_FORM_FIELD_KEYS = frozenset(DEFAULT_CRM_FORM_FIELDS.keys())


def merge_ui_preferences(existing: dict | None, patch: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge a preferences patch onto existing prefs; unknown keys ignored."""
    out: dict[str, Any] = deepcopy(existing) if isinstance(existing, dict) else {}
    if "crm_form_fields" in patch and isinstance(patch["crm_form_fields"], dict):
        current = out.get("crm_form_fields")
        merged = dict(DEFAULT_CRM_FORM_FIELDS)
        if isinstance(current, dict):
            for key, val in current.items():
                if key in CRM_FORM_FIELD_KEYS and isinstance(val, bool):
                    merged[key] = val
        for key, val in patch["crm_form_fields"].items():
            if key in CRM_FORM_FIELD_KEYS and isinstance(val, bool):
                merged[key] = val
        out["crm_form_fields"] = merged
    if "saved_views" in patch and isinstance(patch["saved_views"], dict):
        current = out.get("saved_views")
        views = dict(current) if isinstance(current, dict) else {}
        for key, val in list(patch["saved_views"].items())[:20]:
            if not isinstance(key, str) or not isinstance(val, dict):
                continue
            name = key.strip()[:40]
            if not name:
                continue
            if val.get("remove") is True:
                views.pop(name, None)
                continue
            views[name] = {
                "label": str(val.get("label") or name)[:80],
                "query": str(val.get("query") or "")[:200],
            }
        out["saved_views"] = views
    return out


def resolved_crm_form_fields(prefs: dict | None) -> dict[str, bool]:
    merged = dict(DEFAULT_CRM_FORM_FIELDS)
    if isinstance(prefs, dict):
        raw = prefs.get("crm_form_fields")
        if isinstance(raw, dict):
            for key, val in raw.items():
                if key in CRM_FORM_FIELD_KEYS and isinstance(val, bool):
                    merged[key] = val
    return merged


def public_ui_preferences(prefs: dict | None) -> dict[str, Any]:
    views = {}
    if isinstance(prefs, dict) and isinstance(prefs.get("saved_views"), dict):
        views = prefs["saved_views"]
    return {
        "crm_form_fields": resolved_crm_form_fields(prefs),
        "saved_views": views,
    }
