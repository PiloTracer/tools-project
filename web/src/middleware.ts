import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

// Keep in sync with web/src/shared/server/session.ts
const SESSION = process.env.SESSION_COOKIE_NAME || "prj_auth";

/**
 * Redirects to the signin page when the session cookie is absent on
 * protected app paths. The cookie's maxAge matches the JWT lifetime, so an
 * expired token means the cookie is already gone — presence is a reliable
 * proxy. (Edge middleware cannot validate the JWT itself; the secret is not
 * shared with the web app.)
 */
export function middleware(req: NextRequest) {
  const { pathname, search } = req.nextUrl;
  if (req.cookies.has(SESSION)) {
    return NextResponse.next();
  }
  const target = pathname.startsWith("/client/") ? "/client/login" : "/login";
  const url = req.nextUrl.clone();
  url.pathname = target;
  url.search = `?next=${encodeURIComponent(pathname + search)}`;
  return NextResponse.redirect(url);
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
