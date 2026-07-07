from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
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


async def _dispatch(
    event_type: str, data: dict, tenant_id: uuid.UUID | None = None
) -> None:
    """Internal: look up subscriptions and deliver. Uses its own DB session."""
    fac = session_factory()
    async with fac() as db:
        stmt = select(WebhookSubscription).where(
            WebhookSubscription.events.contains([event_type])
        )
        # Multi-tenancy: only deliver to subscriptions in the source tenant.
        if tenant_id is not None:
            stmt = stmt.where(WebhookSubscription.tenant_id == tenant_id)
        rows: Sequence[WebhookSubscription] = (
            await db.execute(stmt)
        ).scalars().all()

        if not rows:
            return

        # Tenant-aware dispatch: load tenant slug for the payload.
        from app.models.tenant import Tenant
        tenant_slug: str | None = None
        if tenant_id is not None:
            tenant_row = await db.get(Tenant, tenant_id)
            if tenant_row is not None:
                tenant_slug = tenant_row.slug

        for sub in rows:
            sub_body = json.dumps({
                "event": event_type,
                "timestamp": time.time(),
                "data": data,
                "tenant_id": str(tenant_id) if tenant_id else None,
                "tenant_slug": tenant_slug,
            }).encode()
            ok = await _post_with_retry(sub, sub_body)
            if ok:
                from datetime import datetime
                sub.last_delivered_at = datetime.now(UTC)
                db.add(sub)
                log.info("webhook.dispatched event=%s url=%s", event_type, sub.url)
            else:
                log.warning("webhook.exhausted event=%s url=%s", event_type, sub.url)


def dispatch_event(event_type: str, data: dict, tenant_id: uuid.UUID | None = None) -> None:
    """Fire-and-forget: dispatch webhooks in background, never blocks the caller.

    tenant_id: the source tenant for the event. Only subscriptions in that tenant
    receive the event. When None, the event is dispatched globally (legacy mode).
    """
    asyncio.ensure_future(
        _dispatch_with_logged_exception(_dispatch(event_type, data, tenant_id))
    )
