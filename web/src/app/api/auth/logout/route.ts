import { NextResponse } from "next/server";

export async function POST() {
  const access = process.env.SESSION_COOKIE_NAME || "prj_auth";
  const refresh = process.env.REFRESH_COOKIE_NAME || "prj_refresh";
  const res = NextResponse.json({ ok: true });
  res.cookies.set(access, "", {
    httpOnly: true,
    path: "/",
    maxAge: 0,
  });
  res.cookies.set(refresh, "", {
    httpOnly: true,
    path: "/",
    maxAge: 0,
  });
  return res;
}
