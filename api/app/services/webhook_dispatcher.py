from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
from collections.abc import Sequence
from datetime import UTC

import httpx
from sqlalchemy import select

from app.db import session_factory
from app.models.webhook_subscription import WebhookSubscription

log = logging.getLogger(__name__)


async def _dispatch_with_logged_exception(coro) -> None:
    try:
        await coro
    except Exception:
        log.exception("webhook.dispatch_failed")


def _sign_payload(payload: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


async def _post_with_retry(sub: WebhookSubscription, body: bytes) -> bool:
    sig = _sign_payload(body, sub.hmac_secret)
    for attempt in range(1, sub.max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    sub.url, content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": sig,
                        "User-Agent": "tools-project-webhook/1.0",
                    },
                )
                if resp.is_success:
                    return True
                log.warning("webhook.failed url=%s attempt=%d status=%d", sub.url, attempt, resp.status_code)
        except Exception as exc:
            log.warning("webhook.error url=%s attempt=%d exc=%s", sub.url, attempt, exc)
        if attempt < sub.max_retries:
            await asyncio.sleep(2 ** attempt)
    return False


async def _dispatch(event_type: str, data: dict) -> None:
    """Internal: look up subscriptions and deliver. Uses its own DB session."""
    fac = session_factory()
    async with fac() as db:
        rows: Sequence[WebhookSubscription] = (
            await db.execute(
                select(WebhookSubscription).where(
                    WebhookSubscription.events.contains([event_type])
                )
            )
        ).scalars().all()

        if not rows:
            return

        body = json.dumps({
            "event": event_type,
            "timestamp": time.time(),
            "data": data,
        }).encode()

        for sub in rows:
            ok = await _post_with_retry(sub, body)
            if ok:
                from datetime import datetime
                sub.last_delivered_at = datetime.now(UTC)
                db.add(sub)
                log.info("webhook.dispatched event=%s url=%s", event_type, sub.url)
            else:
                log.warning("webhook.exhausted event=%s url=%s", event_type, sub.url)


def dispatch_event(event_type: str, data: dict) -> None:
    """Fire-and-forget: dispatch webhooks in background, never blocks the caller."""
    asyncio.ensure_future(_dispatch_with_logged_exception(_dispatch(event_type, data)))
