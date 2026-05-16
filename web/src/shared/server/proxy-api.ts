import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const SESSION = process.env.SESSION_COOKIE_NAME || "prj_auth";

export async function proxyToApi(
  path: string,
  init?: RequestInit,
): Promise<NextResponse> {
  const jar = await cookies();
  const token = jar.get(SESSION)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  const base =
    process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300";
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (init?.body != null && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const r = await fetch(`${base}${path}`, { ...init, headers });
  const text = await r.text();
  return new NextResponse(text, {
    status: r.status,
    headers: {
      "Content-Type": r.headers.get("content-type") || "application/json",
    },
  });
}
