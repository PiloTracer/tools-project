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
from app.services.agent_identity import AGENT_USER_EMAIL, AGENT_USER_ID
from app.services.auth_local import decode_local_token
from app.services.oauth_userinfo import (
    OAuthTenantAmbiguousError,
    upsert_user_from_oauth_access_token,
)
from app.services.tenancy import get_default_tenant

_http_bearer = HTTPBearer(auto_error=False)


def _remember_user_tenant(request: Request, user: User) -> None:
    """Publish the authenticated user's tenant for get_current_tenant (SPEC R2)."""
    request.state.tenant_id = str(user.tenant_id) if user.tenant_id else None


def _tenant_slug_from_host(request: Request) -> str | None:
    """Tenant slug carried by the Host header subdomain (``acme.example.com``)."""
    settings = get_settings()
    host = (request.headers.get("host") or "").split(":")[0].lower()
    public_host = (settings.public_host or "localhost").lower()
    if host.endswith("." + public_host) and host != public_host:
        return host[: -len("." + public_host)].split(".")[-1]
    return None


def _selected_tenant_slug(request: Request) -> str | None:
    """Tenant slug selected by the request itself: subdomain, then X-Tenant-Slug."""
    slug = _tenant_slug_from_host(request)
    if slug:
        return slug
    return (request.headers.get("x-tenant-slug") or "").strip().lower() or None


async def _request_tenant_id(request: Request, db: AsyncSession) -> uuid.UUID | None:
    """Tenant selected by the request, for flows without a resolved user row.

    Used by OAuth sign-in, where the user (and therefore its tenant claim) does
    not exist yet; single-tenant deployments have exactly one tenant, so no
    header or subdomain is needed there.
    """
    settings = get_settings()
    if not settings.multi_tenancy_enabled:
        tenant = await get_default_tenant(db)
        return tenant.id if tenant is not None else None
    slug = _selected_tenant_slug(request)
    if not slug:
        return None
    tenant = await db.scalar(select(Tenant).where(Tenant.slug == slug))
    if tenant is None or not tenant.is_active:
        return None
    return tenant.id


async def get_current_tenant(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Tenant | None:
    """Resolve the current tenant: subdomain → X-Tenant-Slug → authenticated user.

    When multi-tenancy is disabled this is a single-tenant deployment, so the
    ``default`` tenant is returned silently (SPEC multi-tenancy §Feature flag) —
    including for the bootstrap superuser, whose ``tenant_id`` is NULL.

    Returns None only when no tenant can be resolved, which for a single-tenant
    deployment means the ``default`` row is missing; tenant-scoped writes then
    fail with a clear error instead of writing NULL into a NOT NULL column.
    The resolved tenant is stored on ``request.state._tenant`` for logging and
    downstream readers.
    """
    settings = get_settings()
    if not settings.multi_tenancy_enabled:
        tenant = await get_default_tenant(db)
        if tenant is not None:
            request.state._tenant = tenant
        return tenant

    user_tenant_id = getattr(request.state, "tenant_id", None)

    # 1. Subdomain resolution from Host header, then 2. X-Tenant-Slug header
    #    (for API clients that cannot set subdomains)
    tenant_slug = _selected_tenant_slug(request)

    if tenant_slug:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
        if tenant is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Tenant not found")
        if not tenant.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Organization account is disabled")
        # The subdomain / header only *selects* a tenant; authorization still comes
        # from the JWT or API key (SPEC R2b) — a tenant-bound caller cannot widen
        # their scope by pointing at another tenant's subdomain or slug.
        if user_tenant_id is not None and str(tenant.id) != user_tenant_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Tenant context does not match the authenticated user",
            )
        request.state._tenant = tenant
        return tenant

    # 3. Tenant of the authenticated user (JWT claim, validated in
    #    get_current_user / get_current_user_local and stored on request.state)
    if user_tenant_id:
        tenant = await db.get(Tenant, uuid.UUID(user_tenant_id))
        if tenant is not None and tenant.is_active:
            request.state._tenant = tenant
            return tenant

    # No tenant resolved — allow only on auth/config, health, login endpoints
    path = request.url.path
    if path in ("/healthz", "/v1/auth/config") or path.startswith("/v1/auth/"):
        return None

    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Tenant context required")


async def get_current_user_local(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
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
    # Multi-tenancy: validate JWT tenant_id claim matches user's tenant
    if settings.multi_tenancy_enabled:
        jwt_tenant_id = payload.get("tenant_id")
        if row.tenant_id is not None and jwt_tenant_id and str(row.tenant_id) != jwt_tenant_id:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
    _remember_user_tenant(request, row)
    return row


async def get_current_user(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
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
            # Multi-tenancy: validate JWT tenant_id claim matches user's tenant
            if settings.multi_tenancy_enabled:
                jwt_tenant_id = payload.get("tenant_id")
                if row.tenant_id is not None and jwt_tenant_id and str(row.tenant_id) != jwt_tenant_id:
                    raise HTTPException(
                        status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                    )
            _remember_user_tenant(request, row)
            return row

    if settings.auth_oauth_enabled:
        try:
            oauth_user = await upsert_user_from_oauth_access_token(
                db,
                token,
                settings,
                tenant_id=await _request_tenant_id(request, db),
            )
        except OAuthTenantAmbiguousError as exc:
            # R9b: the email exists in several tenants and none was selected.
            raise HTTPException(
                status.HTTP_300_MULTIPLE_CHOICES,
                detail={
                    "choices": [
                        {"tenant_slug": slug, "tenant_name": name}
                        for slug, name in exc.choices
                    ]
                },
            ) from exc
        if oauth_user is not None and oauth_user.is_active:
            _remember_user_tenant(request, oauth_user)
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
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
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
                id=AGENT_USER_ID,
                email=AGENT_USER_EMAIL,
                display_name="Agent",
                is_superuser=True,
                is_active=True,
                tenant_id=None,
            )
            _remember_user_tenant(request, user)
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
            # Multi-tenancy: the key owner's tenant is published on request.state
            # and enforced by get_current_tenant (SPEC R2c).
            api_key_row.last_used_at = func.now()
            await db.commit()
            _remember_user_tenant(request, api_key_row.user)
            return api_key_row.user

    # Fall back to Bearer JWT
    return await get_current_user(request, creds, db)


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


def _tenant_can_read(user: User, resource_tenant_id: uuid.UUID | None) -> bool:
    """Check whether the caller's tenant may read a resource tenant.

    Returns True when:
    - multi_tenancy is disabled (single-tenant deployment, no-op)
    - the caller is a tenant-less *superuser* (cross-tenant admin, R4a)
    - resource_tenant_id matches the caller's tenant

    The tenant-less branch is deliberately gated on ``is_superuser``: the
    ``users`` CHECK constraint (``is_superuser = true OR tenant_id IS NOT NULL``)
    already forbids tenant-less regular users, and this keeps that rule explicit
    for callers. Currently unused — kept as the documented boundary helper.
    """
    if not get_settings().multi_tenancy_enabled:
        return True
    if user.tenant_id is None:
        return user.is_superuser
    return resource_tenant_id == user.tenant_id


def _tenant_can_write(user: User, resource_tenant_id: uuid.UUID | None) -> bool:
    """Same as _tenant_can_read — write access follows same tenant boundary."""
    return _tenant_can_read(user, resource_tenant_id)


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
