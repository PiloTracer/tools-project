import type { NextRequest } from "next/server";

function sanitizeListenOrigin(origin: string): string {
  try {
    const u = new URL(origin);
    if (u.hostname === "0.0.0.0") {
      u.hostname = "localhost";
    }
    return u.origin;
  } catch {
    return origin;
  }
}

function redirectBaseFromEnvOrOrigin(rawOrigin: string): string {
  return sanitizeListenOrigin(rawOrigin.trim()).replace(/\/+$/, "");
}

export function redirectBaseFromRequest(request: Request): string {
  const fromEnv = (process.env.PUBLIC_ORIGIN || "").trim();
  const raw = fromEnv || new URL(request.url).origin;
  return redirectBaseFromEnvOrOrigin(raw);
}

export function absoluteUrl(req: NextRequest, pathWithQuery: string): URL {
  const fromEnv = (process.env.PUBLIC_ORIGIN || "").trim();
  const raw = fromEnv || req.nextUrl.origin;
  const base = redirectBaseFromEnvOrOrigin(raw);
  return new URL(pathWithQuery, base);
}
