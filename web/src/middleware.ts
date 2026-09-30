import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

// Keep in sync with web/src/shared/server/session.ts
const SESSION = process.env.SESSION_COOKIE_NAME || "prj_auth";
// Keep in sync with web/src/shared/server/tenant.ts
const TENANT = process.env.TENANT_COOKIE_NAME || "prj_tenant";

function multiTenancyOn(): boolean {
  const v = (process.env.MULTI_TENANCY_ENABLED || "").trim().toLowerCase();
  return v === "1" || v === "true" || v === "yes" || v === "on";
}

/**
 * Redirects to the signin page when the session cookie is absent on
 * protected app paths. The cookie's maxAge matches the JWT lifetime, so an
 * expired token means the cookie is already gone — presence is a reliable
 * proxy. (Edge middleware cannot validate the JWT itself; the secret is not
 * shared with the web app.)
 *
 * Multi-tenancy: a session without a tenant selection (a cross-tenant superuser
 * who named no tenant) goes to the tenant picker, because tenant-scoped API
 * calls need `X-Tenant-Slug`. Client-portal paths resolve tenants themselves.
 */
export function middleware(req: NextRequest) {
  const { pathname, search } = req.nextUrl;

  if (!req.cookies.has(SESSION)) {
    const target = pathname.startsWith("/client/") ? "/client/login" : "/login";
    const url = req.nextUrl.clone();
    url.pathname = target;
    url.search = `?next=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }

  if (
    multiTenancyOn() &&
    !pathname.startsWith("/select-tenant") &&
    !pathname.startsWith("/client/") &&
    !req.cookies.get(TENANT)?.value
  ) {
    const url = req.nextUrl.clone();
    url.pathname = "/select-tenant";
    url.search = `?next=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/today/:path*",
    "/projects/:path*",
    "/inbox/:path*",
    "/prospects/:path*",
    "/clients/:path*",
    "/reports/:path*",
    "/settings/:path*",
    "/admin/:path*",
    "/client/dashboard/:path*",
    "/client/projects/:path*",
  ],
};
