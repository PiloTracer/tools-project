from __future__ import annotations

import secrets
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.webhook_subscription import WebhookSubscription

router = APIRouter(prefix="/v1/admin/webhook-subscriptions", tags=["admin"])


class WebhookSubscriptionCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2000)
    events: list[str] = Field(min_length=1)
    label: str | None = Field(default=None, max_length=100)


class WebhookSubscriptionOut(BaseModel):
    id: uuid.UUID
    label: str | None
    url: str
    events: list[str]
    hmac_secret: str = ""


class WebhookSubscriptionList(BaseModel):
    items: list[WebhookSubscriptionOut]


def _mask_secret(secret: str) -> str:
    return secret[:8] + "..." if len(secret) > 8 else "***"


@router.post("", response_model=WebhookSubscriptionOut, status_code=status.HTTP_201_CREATED)
async def create_webhook_subscription(
    body: WebhookSubscriptionCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not user.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin only")
    secret = "whsec_" + secrets.token_urlsafe(32)
    sub = WebhookSubscription(
        url=body.url.strip(),
        events=body.events,
        label=body.label.strip() if body.label else None,
        hmac_secret=secret,
        created_by=user.id,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return WebhookSubscriptionOut(
        id=sub.id, label=sub.label, url=sub.url, events=sub.events, hmac_secret=secret,
    )


@router.get("", response_model=WebhookSubscriptionList)
async def list_webhook_subscriptions(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not user.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin only")
    rows = (await db.execute(select(WebhookSubscription).order_by(WebhookSubscription.created_at.desc()))).scalars().all()
    return WebhookSubscriptionList(items=[
        WebhookSubscriptionOut(
            id=r.id, label=r.label, url=r.url, events=r.events,
            hmac_secret=_mask_secret(r.hmac_secret),
        )
        for r in rows
    ])


@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_subscription(
    sub_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not user.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin only")
    row = await db.get(WebhookSubscription, sub_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
