import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function GET(
  _req: Request,
  context: { params: Promise<{ id: string }> },
) {
  const jar = await cookies();
  const token = jar.get(process.env.SESSION_COOKIE_NAME || "prj_auth")?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  const { id } = await context.params;
  const base = process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300";
  const r = await fetch(`${base}/v1/projects/${id}/board-columns`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const text = await r.text();
  return new NextResponse(text, {
    status: r.status,
    headers: { "Content-Type": r.headers.get("content-type") || "application/json" },
  });
}
