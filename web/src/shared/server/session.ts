import { cookies } from "next/headers";

import type { MeResponse } from "@/shared/types/me";

function apiBase(): string {
  return (
    process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300"
  );
}

const SESSION = process.env.SESSION_COOKIE_NAME || "prj_auth";

export function getSessionCookieName(): string {
  return SESSION;
}

export async function getBearerFromCookies(): Promise<string | null> {
  const jar = await cookies();
  return jar.get(SESSION)?.value ?? null;
}

/** Server-side: current user from API, or null if anonymous / invalid token. */
export async function fetchMe(): Promise<MeResponse | null> {
  const token = await getBearerFromCookies();
  if (!token) return null;
  try {
    const r = await fetch(`${apiBase()}/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!r.ok) return null;
    return (await r.json()) as MeResponse;
  } catch {
    return null;
  }
}

export async function apiServerFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const token = await getBearerFromCookies();
  const headers = new Headers(init?.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(`${apiBase()}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}
