from __future__ import annotations

import hashlib
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import verify_webhook_signature
from app.models.client_contact import ClientContact
from app.models.prospect import PIPELINE_STAGE_ORDER, Prospect
from app.models.user import User
from app.schemas import RfpAwardPayload, RfpAwardResponse
from app.services.pipeline_service import (
    auto_scaffold_onboarding_project,
    promote_prospect_to_client,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])

_idempotency_store: dict[str, tuple[str, dict, float]] = {}
_IDEMPOTENCY_TTL = 86400


def _prune_idempotency_store():
    now = time.time()
    stale = [k for k, (_, _, ttl) in _idempotency_store.items() if ttl < now]
    for k in stale:
        del _idempotency_store[k]


def _payload_hash(payload: RfpAwardPayload) -> str:
    raw = payload.model_dump_json().encode()
    return hashlib.sha256(raw).hexdigest()


async def _get_system_user(db: AsyncSession) -> User:
    user = await db.scalar(
        select(User)
        .where(User.is_superuser.is_(True))
        .order_by(User.tenant_id.asc().nulls_last())
        .limit(1)
    )
    if user is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No superuser found for system action")
    return user


@router.post("/rfp/award", response_model=RfpAwardResponse, status_code=status.HTTP_201_CREATED)
async def rfp_award(
    payload: RfpAwardPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(verify_webhook_signature)],
    x_idempotency_key: Annotated[str | None, Header()] = None,
):
    _prune_idempotency_store()
    request_hash = _payload_hash(payload)

    if x_idempotency_key:
        existing = _idempotency_store.get(x_idempotency_key)
        if existing is not None:
            stored_hash, stored_result, _expiry = existing
            if stored_hash != request_hash:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail="Idempotency key already processed with different payload",
                )
            return RfpAwardResponse(**stored_result)

    email = payload.contact_email.strip().lower()
    company = payload.company_name.strip()

    contact = await db.scalar(
        select(ClientContact).where(ClientContact.email == email)
    )
    if contact is not None and contact.prospect_id is not None:
        existing_prospect = await db.get(Prospect, contact.prospect_id)
        if existing_prospect is not None:
            log.info("rfp_webhook.received company=%s email=%s prospect_id=%s result=existing", company, email, existing_prospect.id)
            result = await _promote(existing_prospect, db)
            if x_idempotency_key:
                _idempotency_store[x_idempotency_key] = (request_hash, result, time.time() + _IDEMPOTENCY_TTL)
            return RfpAwardResponse(**result)

    system_user = await _get_system_user(db)
    tenant_id = system_user.tenant_id
    if tenant_id is None:
        from app.models.tenant import Tenant
        default_tenant = await db.scalar(select(Tenant).where(Tenant.slug == "default"))
        if default_tenant is None:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Default tenant not found")
        tenant_id = default_tenant.id

    prospect = Prospect(
        company_name=company,
        pipeline_stage="target",
        source="rfp_webhook",
        created_by=system_user.id,
        tenant_id=tenant_id,
    )
    db.add(prospect)
    await db.commit()
    await db.refresh(prospect)

    log.info("rfp_webhook.received company=%s email=%s prospect_id=%s result=created", company, email, prospect.id)

    result = await _promote(prospect, db)
    if x_idempotency_key:
        _idempotency_store[x_idempotency_key] = (request_hash, result, time.time() + _IDEMPOTENCY_TTL)
    return RfpAwardResponse(**result)


async def _promote(prospect: Prospect, db: AsyncSession) -> dict:
    system_user = await _get_system_user(db)

    if prospect.pipeline_stage != "won":
        won_idx = PIPELINE_STAGE_ORDER.index("won")
        current_idx = PIPELINE_STAGE_ORDER.index(prospect.pipeline_stage)
        if current_idx < won_idx:
            prospect.pipeline_stage = "won"
            db.add(prospect)
            await db.commit()
            await db.refresh(prospect)

    client = await promote_prospect_to_client(db, prospect, created_by=system_user.id)
    await db.commit()
    await db.refresh(client)

    project = await auto_scaffold_onboarding_project(
        db, client, prospect, promoting_user_id=system_user.id
    )
    await db.commit()
    await db.refresh(project)

    return {
        "client_id": client.id,
        "client_name": client.name,
        "project_id": project.id,
        "project_name": project.name,
        "prospect_id": prospect.id,
    }
