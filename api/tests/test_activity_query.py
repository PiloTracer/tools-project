"""Unit tests for the shared activity query builder (web + agent feeds)."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.services.activity_query import (
    activity_order,
    assert_visibility_allowed,
    normalize_visibility,
)
from app.services.project_access import MemberRole, ProjectAccess


def _access(*, client: bool) -> ProjectAccess:
    # Only `client_access is None` matters to is_client_participant; the project
    # instance is irrelevant for these helpers.
    return ProjectAccess(
        project=object(),  # type: ignore[arg-type]
        role=MemberRole.viewer,
        client_access=object() if client else None,  # type: ignore[arg-type]
    )


def test_normalize_visibility_accepts_known_values() -> None:
    assert normalize_visibility(None) is None
    assert normalize_visibility("all") is None
    assert normalize_visibility(" INTERNAL ") == "internal"
    assert normalize_visibility("external") == "external"


def test_normalize_visibility_rejects_unknown_values() -> None:
    with pytest.raises(HTTPException) as exc:
        normalize_visibility("secret")

    assert exc.value.status_code == 400


def test_client_participant_cannot_request_internal() -> None:
    with pytest.raises(HTTPException) as exc:
        assert_visibility_allowed(_access(client=True), "internal")

    assert exc.value.status_code == 403


def test_staff_may_request_internal() -> None:
    assert_visibility_allowed(_access(client=False), "internal")


def test_activity_order_defaults_to_desc() -> None:
    assert "DESC" in str(activity_order(None)).upper()
    assert "DESC" in str(activity_order("desc")).upper()
    assert "ASC" in str(activity_order("asc")).upper()
