import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const origin = req.headers.get("origin") || "";
  const referer = req.headers.get("referer") || "";
  const allowedHost = process.env.PUBLIC_HOST || "localhost";
  const allowedOrigins = [
    `http://${allowedHost}`,
    `https://${allowedHost}`,
    `http://localhost:18513`,
    `http://localhost:8300`,
  ];

  const isAllowed =
    allowedOrigins.some((a) => origin.startsWith(a)) ||
    allowedOrigins.some((a) => referer.startsWith(a));

  if (!isAllowed) {
    return NextResponse.json({ error: "csrf_rejected" }, { status: 403 });
  }

  const contentType = req.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return NextResponse.json({ error: "unsupported_media_type" }, { status: 415 });
  }

  const access = process.env.SESSION_COOKIE_NAME || "prj_auth";
  const refresh = process.env.REFRESH_COOKIE_NAME || "prj_refresh";
  const secure = process.env.NODE_ENV === "production";
  const res = NextResponse.json({ ok: true });
  res.cookies.set(access, "", {
    httpOnly: true,
    secure,
    sameSite: "strict",
    path: "/",
    maxAge: 0,
  });
  res.cookies.set(refresh, "", {
    httpOnly: true,
    secure,
    sameSite: "strict",
    path: "/",
    maxAge: 0,
  });
  return res;
}
