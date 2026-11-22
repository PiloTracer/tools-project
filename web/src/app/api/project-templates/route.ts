import { cookies } from "next/headers";
import { NextResponse } from "next/server";

async function proxy(req: Request, method: "GET" | "POST") {
  const jar = await cookies();
  const token = jar.get(process.env.SESSION_COOKIE_NAME || "prj_auth")?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  const base = process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300";
  const r = await fetch(`${base}/v1/project-templates`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(method === "POST" ? { "Content-Type": "application/json" } : {}),
    },
    body: method === "POST" ? await req.text() : undefined,
  });
  const text = await r.text();
  return new NextResponse(text, {
    status: r.status,
    headers: { "Content-Type": r.headers.get("content-type") || "application/json" },
  });
}

export function GET(req: Request) {
  return proxy(req, "GET");
}

export function POST(req: Request) {
  return proxy(req, "POST");
}
