import { NextResponse } from "next/server";

import { localEnabledServer } from "@/shared/server/auth-flags";
import {
  multiTenancyEnabled,
  normalizeTenantSlug,
  TENANT_CHOICES_COOKIE,
  TENANT_COOKIE,
  TENANT_COOKIE_MAX_AGE,
  tenantSlugFromHost,
} from "@/shared/server/tenant";

export async function POST(req: Request) {
  if (!localEnabledServer()) {
    return NextResponse.json({ error: "local_auth_disabled" }, { status: 403 });
  }

  const contentType = req.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return NextResponse.json({ error: "unsupported_media_type" }, { status: 415 });
  }

  let body: { email?: string; password?: string; tenant_slug?: string };
  try {
    body = (await req.json()) as { email?: string; password?: string; tenant_slug?: string };
  } catch {
    return NextResponse.json({ error: "invalid_json" }, { status: 400 });
  }
  const base =
    process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300";
  const r = await fetch(`${base}/v1/auth/local/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: body.email ?? "",
      password: body.password ?? "",
      tenant_slug: body.tenant_slug || undefined,
    }),
  });

  if (!r.ok) {
    let detail = "login_failed";
    try {
      const j = (await r.json()) as {
        detail?:
          | string
          | Array<{ msg?: string }>
          | { choices?: Array<{ tenant_slug: string; tenant_name: string }> };
        choices?: Array<{ tenant_slug: string; tenant_name: string }>;
      };
      if (typeof j.detail === "string") detail = j.detail;
      else if (Array.isArray(j.detail)) detail = "validation_error";
      // Multi-tenancy: 300 ambiguous — hand the choices to the client's tenant
      // picker (R9b). The API carries them top-level for login; other endpoints
      // (the auth dependency) nest them under `detail`.
      const choices =
        j.choices ??
        (typeof j.detail === "object" && !Array.isArray(j.detail)
          ? j.detail.choices
          : undefined);
      if (r.status === 300 && choices) {
        return NextResponse.json({ choices }, { status: 300 });
      }
    } catch {
      /* keep */
    }
    return NextResponse.json({ error: detail }, { status: r.status });
  }

  const data = (await r.json()) as {
    access_token: string;
    expires_in: number;
    /** Tenant the authenticated user belongs to (null for a cross-tenant superuser). */
    tenant_slug?: string | null;
    /** Tenant context this login resolved (subdomain / requested tenant_slug). */
    request_tenant_slug?: string | null;
  };
  const cookieName = process.env.SESSION_COOKIE_NAME || "prj_auth";
  const secure = process.env.NODE_ENV === "production";
  const res = NextResponse.json({ ok: true });
  res.cookies.set(cookieName, data.access_token, {
    httpOnly: true,
    secure,
    sameSite: "strict",
    path: "/",
    maxAge: data.expires_in,
  });

  // Persist the tenant this session works in: a tenant-bound user always has one,
  // a cross-tenant superuser only when they named one (subdomain / form field).
  // Without it the app routes them to the tenant picker.
  const tenant =
    normalizeTenantSlug(data.tenant_slug) ??
    normalizeTenantSlug(data.request_tenant_slug) ??
    (multiTenancyEnabled()
      ? normalizeTenantSlug(tenantSlugFromHost(req.headers.get("host")))
      : null);
  res.cookies.set(TENANT_COOKIE, tenant ?? "", {
    httpOnly: true,
    secure,
    sameSite: "strict",
    path: "/",
    maxAge: tenant ? Math.min(data.expires_in, TENANT_COOKIE_MAX_AGE) : 0,
  });
  res.cookies.set(TENANT_CHOICES_COOKIE, "", { path: "/", maxAge: 0 });
  return res;
}
