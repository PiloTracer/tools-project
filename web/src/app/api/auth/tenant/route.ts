import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import {
  multiTenancyEnabled,
  normalizeTenantSlug,
  TENANT_CHOICES_COOKIE,
  TENANT_COOKIE,
  TENANT_COOKIE_MAX_AGE,
} from "@/shared/server/tenant";

const SESSION = process.env.SESSION_COOKIE_NAME || "prj_auth";

type TenantRow = { slug: string };

/**
 * Select the tenant this session works in (multi-tenancy R2b).
 *
 * The slug is validated against `GET /v1/admin/tenants`, which only returns
 * tenants the caller may see: every tenant for a cross-tenant superuser, just
 * their own for an org admin. That keeps the selection fail-closed.
 */
export async function POST(req: Request) {
  if (!multiTenancyEnabled()) {
    return NextResponse.json({ error: "multi_tenancy_disabled" }, { status: 400 });
  }

  const contentType = req.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return NextResponse.json({ error: "unsupported_media_type" }, { status: 415 });
  }

  let body: { tenant_slug?: unknown };
  try {
    body = (await req.json()) as { tenant_slug?: unknown };
  } catch {
    return NextResponse.json({ error: "invalid_json" }, { status: 400 });
  }

  const slug = normalizeTenantSlug(body.tenant_slug);
  if (!slug) {
    return NextResponse.json({ error: "invalid_tenant_slug" }, { status: 400 });
  }

  const jar = await cookies();
  const token = jar.get(SESSION)?.value;
  if (!token) {
    return NextResponse.json({ error: "not_authenticated" }, { status: 401 });
  }

  const base =
    process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300";
  let allowed: TenantRow[] = [];
  try {
    const r = await fetch(`${base}/v1/admin/tenants`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (r.status === 401 || r.status === 403) {
      return NextResponse.json({ error: "not_allowed" }, { status: 403 });
    }
    if (r.ok) {
      allowed = (await r.json()) as TenantRow[];
    }
  } catch {
    return NextResponse.json({ error: "api_unreachable" }, { status: 502 });
  }

  if (!allowed.some((t) => t.slug === slug)) {
    return NextResponse.json({ error: "tenant_not_found" }, { status: 404 });
  }

  const res = NextResponse.json({ ok: true, tenant_slug: slug });
  res.cookies.set(TENANT_COOKIE, slug, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: TENANT_COOKIE_MAX_AGE,
  });
  res.cookies.set(TENANT_CHOICES_COOKIE, "", { path: "/", maxAge: 0 });
  return res;
}
