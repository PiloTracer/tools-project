from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.deps import get_current_user
from app.models.client_contact import ClientContact
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas import LocalLoginRequest, MeResponse, TenantChoice, TokenResponse
from app.services.auth_local import create_local_access_token, decode_local_token, verify_password
from app.services.rate_limiter import check_login_rate_limit

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.get("/config")
def auth_config(request: Request):
    s = get_settings()
    resp: dict = {
        "local_enabled": s.auth_local_enabled,
        "oauth_enabled": s.auth_oauth_enabled,
        "multi_tenant": s.multi_tenancy_enabled,
    }
    if s.multi_tenancy_enabled:
        host = (request.headers.get("host") or "").split(":")[0].lower()
        public_host = s.public_host.lower()
        if host.endswith("." + public_host) and host != public_host:
            slug = host[: -len("." + public_host)].split(".")[-1]
            resp["tenant"] = {"slug": slug}
        else:
            resp["tenant"] = None
    return resp


@router.post("/local/login", response_model=TokenResponse)
async def local_login(
    body: LocalLoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rate_limit: None = Depends(check_login_rate_limit),
):
    s = get_settings()
    if not s.auth_local_enabled:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Local authentication is disabled for this deployment",
        )
    email = body.email.strip().lower()

    # Multi-tenancy: resolve tenant context from subdomain / tenant_slug
    tenant_id: uuid.UUID | None = None
    requested_tenant: Tenant | None = None
    if s.multi_tenancy_enabled:
        host = (request.headers.get("host") or "").split(":")[0].lower()
        public_host = s.public_host.lower()
        if host.endswith("." + public_host) and host != public_host:
            slug = host[: -len("." + public_host)].split(".")[-1]
            tenant = await db.scalar(select(Tenant).where(Tenant.slug == slug))
            if tenant is not None and tenant.is_active:
                tenant_id = tenant.id
                requested_tenant = tenant

        if body.tenant_slug and not tenant_id:
            tenant = await db.scalar(select(Tenant).where(Tenant.slug == body.tenant_slug))
            if tenant is not None and tenant.is_active:
                tenant_id = tenant.id
                requested_tenant = tenant

    # Tenant-scoped user lookup. Cross-tenant superusers (tenant_id IS NULL) stay
    # reachable from every tenant context (R4a/R4c), so a tenant-bound account
    # with the same email wins over the tenant-less superuser row.
    user_stmt = select(User).where(User.email == email)
    if tenant_id is not None:
        user_stmt = user_stmt.where(
            or_(User.tenant_id == tenant_id, User.tenant_id.is_(None))
        )
    user_stmt = user_stmt.order_by(User.tenant_id.is_(None).asc())

    user: User
    if tenant_id is None:
        # No tenant context: authenticate against every account carrying this email
        # (per-tenant emails allow duplicates — R5). Never pick one arbitrarily.
        candidates = list((await db.scalars(user_stmt)).all())
        authenticated = [
            u
            for u in candidates
            if u.is_active and u.password_hash and verify_password(body.password, u.password_hash)
        ]
        if not authenticated:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if s.multi_tenancy_enabled and len(authenticated) > 1:
            # Multiple tenants — 300 Multiple Choices with the tenant list (R9b/R13)
            tenant_ids = [u.tenant_id for u in authenticated if u.tenant_id is not None]
            tenant_rows: list[Tenant] = []
            if tenant_ids:
                tenant_rows = list((await db.scalars(
                    select(Tenant).where(Tenant.id.in_(tenant_ids)).order_by(Tenant.name.asc())
                )).all())
            choices = [
                TenantChoice(tenant_slug=t.slug, tenant_name=t.name)
                for t in tenant_rows
            ]
            return JSONResponse(
                status_code=status.HTTP_300_MULTIPLE_CHOICES,
                content=TokenResponse(
                    access_token="", expires_in=0, choices=choices
                ).model_dump(mode="json"),
            )
        user = authenticated[0]
    else:
        found = await db.scalar(user_stmt)
        if (
            found is None
            or not found.is_active
            or not found.password_hash
            or not verify_password(body.password, found.password_hash)
        ):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        user = found

    token, expires_in = create_local_access_token(
        user_id=str(user.id),
        email=user.email,
        is_superuser=user.is_superuser,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
        settings=s,
    )
    # Echo the tenant binding (tenant_id/tenant_slug = the user's own tenant, None
    # for a cross-tenant superuser) and the tenant context this login resolved, so
    # the web client can persist the selection for X-Tenant-Slug on later calls.
    bound_tenant_slug: str | None = None
    if s.multi_tenancy_enabled and user.tenant_id is not None:
        bound_tenant = await db.get(Tenant, user.tenant_id)
        if bound_tenant is not None:
            bound_tenant_slug = bound_tenant.slug
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        tenant_id=user.tenant_id,
        tenant_slug=bound_tenant_slug,
        request_tenant_slug=requested_tenant.slug if requested_tenant is not None else None,
    )


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Current session",
    description=(
        "Requires `Authorization: Bearer`. Local JWTs are decoded with `JWT_SECRET` when "
        "`AUTH_LOCAL_ENABLED` is true; otherwise the bearer token is treated as an OAuth access "
        "token and the user record is resolved via `OAUTH_USER_INFO_ENDPOINT` (userinfo lookup — "
        "accounts are provisioned by an admin, never auto-created), not JWKS signature verification."
    ),
)
async def auth_me(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    auth_kind = "oauth"
    if get_settings().auth_local_enabled:
        auth_header = (request.headers.get("authorization") or "").strip()
        token = ""
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
        if token and decode_local_token(token):
            auth_kind = "local"

    client_contact_id: uuid.UUID | None = None
    client_name: str | None = None
    contact = await db.scalar(
        select(ClientContact)
        .where(ClientContact.user_id == user.id)
        .limit(1)
    )
    if contact is not None:
        client_contact_id = contact.id
        client_name = contact.client.name if contact.client else None

    # Multi-tenancy: include tenant info
    tenant_id_val: uuid.UUID | None = None
    tenant_slug: str | None = None
    tenant_name: str | None = None
    if get_settings().multi_tenancy_enabled and user.tenant_id is not None:
        tenant_id_val = user.tenant_id
        tenant_row = await db.get(Tenant, user.tenant_id)
        if tenant_row is not None:
            tenant_slug = tenant_row.slug
            tenant_name = tenant_row.name

    return MeResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        is_superuser=user.is_superuser,
        auth=auth_kind,
        client_contact_id=client_contact_id,
        client_name=client_name,
        tenant_id=tenant_id_val,
        tenant_slug=tenant_slug,
        tenant_name=tenant_name,
    )
