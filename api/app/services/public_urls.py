"""Public base URLs for links emitted by the API (SPEC amendment 01 §R3/R5).

`PUBLIC_API_BASE_URL` / `PUBLIC_WEB_BASE_URL` are the explicit, deployment-set
origins. When the API origin is not configured it is derived from the request
(`X-Forwarded-Proto`/`X-Forwarded-Host`, then `Host`) so Caddy/Cloudflare
deployments get `https://…` without extra configuration. These URLs are only
emitted to the authenticated caller — they are never cached or used for
redirects — so trusting the forwarded headers has no cross-caller effect.
"""

from __future__ import annotations

from fastapi import Request

from app.config import get_settings


def _normalize(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().rstrip("/")
    return cleaned or None


def api_base_url(request: Request) -> str:
    """Absolute API origin used for `download_url` values."""
    configured = _normalize(get_settings().public_api_base_url)
    if configured:
        return configured

    proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
    host = request.headers.get("x-forwarded-host", "").split(",")[0].strip()
    host = host or request.headers.get("host", "").strip()
    if host:
        scheme = proto or request.url.scheme
        return f"{scheme}://{host}".rstrip("/")

    return str(request.base_url).rstrip("/")


def web_base_url() -> str | None:
    """Absolute web origin for human-facing ticket links, or None when unset."""
    return _normalize(get_settings().public_web_base_url)
