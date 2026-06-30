"""In-memory sliding-window rate limiter for login endpoints."""

from __future__ import annotations

import time

from fastapi import HTTPException, Request, status

_MAX_ATTEMPTS = 10
_WINDOW_SECONDS = 60
_CLEANUP_INTERVAL = 300


class _Bucket:
    def __init__(self) -> None:
        self.attempts: list[float] = []


_buckets: dict[str, _Bucket] = {}
_last_cleanup: float = time.monotonic()


def _cleanup() -> None:
    now = time.monotonic()
    cutoff = now - _WINDOW_SECONDS
    expired = [k for k, b in _buckets.items() if b.attempts and b.attempts[-1] < cutoff]
    for k in expired:
        del _buckets[k]


async def check_login_rate_limit(request: Request) -> None:
    global _last_cleanup
    now = time.monotonic()

    if now - _last_cleanup > _CLEANUP_INTERVAL:
        _cleanup()
        _last_cleanup = now

    client_ip = request.client.host if request.client else "unknown"
    bucket = _buckets.get(client_ip)
    if bucket is None:
        bucket = _Bucket()
        _buckets[client_ip] = bucket

    cutoff = now - _WINDOW_SECONDS
    bucket.attempts = [t for t in bucket.attempts if t > cutoff]
    bucket.attempts.append(now)

    if len(bucket.attempts) > _MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )
