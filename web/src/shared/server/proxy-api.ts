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

/** Multipart POST (e.g. file upload). Do not set Content-Type — boundary is automatic. */
export async function proxyFormDataToApi(
  path: string,
  formData: FormData,
): Promise<NextResponse> {
  const jar = await cookies();
  const token = jar.get(SESSION)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  const base =
    process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300";
  const r = await fetch(`${base}${path}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const text = await r.text();
  return new NextResponse(text, {
    status: r.status,
    headers: {
      "Content-Type": r.headers.get("content-type") || "application/json",
    },
  });
}

export async function proxyBinaryFromApi(path: string): Promise<NextResponse> {
  const jar = await cookies();
  const token = jar.get(SESSION)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  const base =
    process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300";
  const r = await fetch(`${base}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  const buf = await r.arrayBuffer();
  const ct = r.headers.get("content-type") || "application/octet-stream";
  return new NextResponse(buf, {
    status: r.status,
    headers: { "Content-Type": ct, "Cache-Control": "private, max-age=600" },
  });
}
