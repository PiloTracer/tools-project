from __future__ import annotations

import hashlib
import hmac
import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.models.client_contact import ClientContact
from app.models.tenant import Tenant
from app.models.user import User
from app.services.auth_local import decode_local_token
from app.services.oauth_userinfo import upsert_user_from_oauth_access_token

_http_bearer = HTTPBearer(auto_error=False)


async def get_current_tenant(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Tenant | None:
    """Resolve the current tenant from subdomain → JWT → X-Tenant-Slug header.

    Returns None when multi_tenancy is disabled (backward-compatible single-tenant mode).
    Tenant is cached on request.state for downstream dependencies.
    """
    settings = get_settings()
    if not settings.multi_tenancy_enabled:
        request.state.tenant_id = None
        return None

    tenant_slug: str | None = None

    # 1. Subdomain resolution from Host header
    host = (request.headers.get("host") or "").split(":")[0].lower()
    public_host = (settings.public_host or "localhost").lower()
    if host.endswith("." + public_host) and host != public_host:
        tenant_slug = host[: -len("." + public_host)].split(".")[-1]

    # 2. JWT tenant_id claim (resolved in get_current_user and stored on request.state)
    if not tenant_slug:
        jwt_tenant_id = getattr(request.state, "tenant_id", None)
        if jwt_tenant_id:
            tenant = await db.get(Tenant, uuid.UUID(jwt_tenant_id))
            if tenant is not None and tenant.is_active:
                request.state._tenant = tenant
                return tenant

    # 3. X-Tenant-Slug header
    if not tenant_slug:
        tenant_slug = (request.headers.get("x-tenant-slug") or "").strip().lower() or None

    if tenant_slug:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
        if tenant is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Tenant not found")
        if not tenant.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Organization account is disabled")
        request.state._tenant = tenant
        request.state.tenant_id = str(tenant.id)
        return tenant

    # No tenant resolved — allow only on auth/config, health, login endpoints
    path = request.url.path
    if path in ("/healthz", "/v1/auth/config") or path.startswith("/v1/auth/"):
        request.state.tenant_id = None
        return None

    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Tenant context required")


async def get_current_user_local(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    settings = get_settings()
    if not settings.auth_local_enabled:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Local auth is disabled"
        )
    payload = decode_local_token(creds.credentials)
    if not payload:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        )
    try:
        user_uuid = uuid.UUID(uid)
    except ValueError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        ) from None
    row = await db.scalar(select(User).where(User.id == user_uuid))
    if row is None or not row.is_active:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )
    # Multi-tenancy: validate tenant_id claim matches user's tenant
    if settings.multi_tenancy_enabled:
        jwt_tenant_id = payload.get("tenant_id")
        if row.tenant_id is not None and jwt_tenant_id and str(row.tenant_id) != jwt_tenant_id:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        request.state.tenant_id = str(row.tenant_id) if row.tenant_id else None
    return row


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    settings = get_settings()
    token = creds.credentials

    if settings.auth_local_enabled:
        payload = decode_local_token(token)
        if payload:
            uid = payload.get("sub")
            if not uid:
                raise HTTPException(
                    status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
                )
            try:
                user_uuid = uuid.UUID(uid)
            except ValueError:
                raise HTTPException(
                    status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
                ) from None
            row = await db.scalar(select(User).where(User.id == user_uuid))
            if row is None or not row.is_active:
                raise HTTPException(
                    status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
                )
            # Multi-tenancy: store tenant_id on request.state
            if settings.multi_tenancy_enabled:
                jwt_tenant_id = payload.get("tenant_id")
                if row.tenant_id is not None and jwt_tenant_id and str(row.tenant_id) != jwt_tenant_id:
                    raise HTTPException(
                        status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                    )
                request.state.tenant_id = str(row.tenant_id) if row.tenant_id else None
            return row

    if settings.auth_oauth_enabled:
        oauth_user = await upsert_user_from_oauth_access_token(db, token, settings)
        if oauth_user is not None and oauth_user.is_active:
            if settings.multi_tenancy_enabled:
                request.state.tenant_id = str(oauth_user.tenant_id) if oauth_user.tenant_id else None
            return oauth_user

    raise HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
    )


async def require_superuser(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_superuser:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return user


async def require_agent_or_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    x_api_key: Annotated[str | None, Header(alias="X-Api-Key")] = None,
) -> User:
    """Accept a personal API key, server-wide agent key, or Bearer JWT.

    Auth resolution (first match wins):
      1. X-Api-Key matches Settings.agent_api_key → synthetic agent superuser
      2. X-Api-Key matches a user_api_keys row (SHA-256) → authenticated user
      3. Bearer JWT → normal user session
      4. None → 401

    Multi-tenancy: personal API keys are tenant-scoped. If an X-Tenant-Slug header
    is present and the key's owner belongs to a different tenant, the request is rejected.
    """
    import hashlib

    settings = get_settings()

    if x_api_key:
        plaintext = x_api_key.strip()

        # Server-wide shared agent key is disabled in multi-tenant mode because
        # it is not tied to a tenant. Personal API keys must be used instead.
        if settings.agent_api_key and plaintext == settings.agent_api_key.strip():
            if settings.multi_tenancy_enabled:
                raise HTTPException(
                    status.HTTP_401_UNAUTHORIZED,
                    detail="Shared agent API key is not allowed in multi-tenant mode; use a personal API key",
                )
            user = User(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, "agent.localhost"),
                email="agent@localhost",
                display_name="Agent",
                is_superuser=True,
                is_active=True,
                tenant_id=None,
            )
            request.state.tenant_id = None
            return user

        # Personal API key — look up by SHA-256 hash
        from sqlalchemy.orm import joinedload

        from app.models.user_api_key import UserApiKey

        key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
        api_key_row = await db.scalar(
            select(UserApiKey)
            .where(UserApiKey.key_hash == key_hash)
            .options(joinedload(UserApiKey.user))
        )
        if api_key_row is not None and api_key_row.user.is_active:
            # Multi-tenancy: API keys are tenant-scoped
            if settings.multi_tenancy_enabled:
                tenant_slug = (request.headers.get("x-tenant-slug") or "").strip().lower()
                if tenant_slug and api_key_row.user.tenant_id is not None:
                    tenant = await db.get(Tenant, api_key_row.user.tenant_id)
                    if tenant is None or tenant.slug != tenant_slug:
                        raise HTTPException(
                            status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid API key for tenant",
                        )
                request.state.tenant_id = str(api_key_row.user.tenant_id) if api_key_row.user.tenant_id else None

            api_key_row.last_used_at = func.now()
            await db.commit()
            return api_key_row.user

    # Fall back to Bearer JWT
    return await get_current_user(creds, db, request)


async def get_current_client_participant(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> tuple[User, ClientContact]:
    """Returns (user, client_contact) if the current user has a linked contact."""
    contact = await db.scalar(
        select(ClientContact).where(ClientContact.user_id == user.id)
    )
    if contact is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="User is not linked to any client contact",
        )
    return user, contact


def _tenant_can_read(tenant_id: uuid.UUID | None, resource_tenant_id: uuid.UUID | None) -> bool:
    """Check if the current tenant can read a resource by comparing tenant IDs.

    Returns True when:
    - multi_tenancy is disabled (no-op)
    - tenant_id is None (cross-tenant superuser or feature disabled)
    - resource_tenant_id matches tenant_id
    """
    if not get_settings().multi_tenancy_enabled:
        return True
    if tenant_id is None:
        return True  # cross-tenant superuser
    return resource_tenant_id == tenant_id


def _tenant_can_write(tenant_id: uuid.UUID | None, resource_tenant_id: uuid.UUID | None) -> bool:
    """Same as _tenant_can_read — write access follows same tenant boundary."""
    return _tenant_can_read(tenant_id, resource_tenant_id)


async def verify_webhook_signature(
    request: Request,
    x_webhook_signature: Annotated[str | None, Header()] = None,
):
    settings = get_settings()
    secret = settings.rfp_webhook_secret
    if not secret:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Webhook secret not configured"
        )
    if not x_webhook_signature:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Missing X-Webhook-Signature header"
        )
    body = await request.body()
    expected = "sha256=" + hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, x_webhook_signature):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid signature"
        )
