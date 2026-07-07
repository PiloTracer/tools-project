import { NextResponse } from "next/server";

import { localEnabledServer } from "@/shared/server/auth-flags";

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
      const j = (await r.json()) as { detail?: string | Array<{ msg?: string }>; choices?: Array<{ tenant_slug: string; tenant_name: string }> };
      if (typeof j.detail === "string") detail = j.detail;
      else if (Array.isArray(j.detail)) detail = "validation_error";
      // Multi-tenancy: 300 ambiguous — return choices to client for tenant picker
      if (r.status === 300 && j.choices) {
        return NextResponse.json({ choices: j.choices }, { status: 300 });
      }
    } catch {
      /* keep */
    }
    return NextResponse.json({ error: detail }, { status: r.status });
  }

  const data = (await r.json()) as {
    access_token: string;
    expires_in: number;
  };
  const cookieName = process.env.SESSION_COOKIE_NAME || "prj_auth";
  const res = NextResponse.json({ ok: true });
  res.cookies.set(cookieName, data.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: data.expires_in,
  });
  return res;
}
