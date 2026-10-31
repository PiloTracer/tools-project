"""Public base URL resolution (SPEC amendment 01 §R3/R5)."""

from __future__ import annotations

from fastapi import Request

from app.config import get_settings
from app.services.public_urls import api_base_url, web_base_url


def _request(headers: dict[str, str] | None = None) -> Request:
    raw = [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()]
    if not raw:
        raw = [(b"host", b"internal:8300")]
    return Request(
        {
            "type": "http",
            "scheme": "http",
            "path": "/",
            "query_string": b"",
            "headers": raw,
        }
    )


def test_configured_origins_win(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example/")
    monkeypatch.setenv("PUBLIC_WEB_BASE_URL", "https://web.example/")
    get_settings.cache_clear()
    try:
        assert api_base_url(_request()) == "https://api.example"
        assert web_base_url() == "https://web.example"
    finally:
        get_settings.cache_clear()


def test_api_origin_derived_from_forwarded_headers(monkeypatch) -> None:
    monkeypatch.delenv("PUBLIC_API_BASE_URL", raising=False)
    get_settings.cache_clear()
    try:
        request = _request(
            {"x-forwarded-proto": "https", "x-forwarded-host": "project.example"}
        )
        assert api_base_url(request) == "https://project.example"
    finally:
        get_settings.cache_clear()


def test_web_url_is_null_when_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv("PUBLIC_WEB_BASE_URL", raising=False)
    get_settings.cache_clear()
    try:
        assert web_base_url() is None
    finally:
        get_settings.cache_clear()
