import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { getTenantSlugFromCookies } from "@/shared/server/session";

const SESSION = process.env.SESSION_COOKIE_NAME || "prj_auth";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const jar = await cookies();
  const token = jar.get(SESSION)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  const { id } = await params;
  const base =
    process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300";
  const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
  const tenant = await getTenantSlugFromCookies();
  if (tenant) headers["X-Tenant-Slug"] = tenant;
  const r = await fetch(`${base}/v1/projects/${id}/activities/stream`, {
    headers,
    cache: "no-store",
  });
  if (!r.ok || !r.body) {
    const text = await r.text();
    return new NextResponse(text, { status: r.status });
  }
  return new NextResponse(r.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
      Connection: "keep-alive",
    },
  });
}
