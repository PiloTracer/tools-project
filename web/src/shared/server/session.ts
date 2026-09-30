import { cookies } from "next/headers";

import { TENANT_COOKIE } from "@/shared/server/tenant";
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

/**
 * Tenant selection for the API's `X-Tenant-Slug` header (multi-tenancy R2b):
 * needed whenever the session token carries no tenant claim.
 */
export async function getTenantSlugFromCookies(): Promise<string | null> {
  const jar = await cookies();
  return jar.get(TENANT_COOKIE)?.value?.trim().toLowerCase() || null;
}

/** Server-side: current user from API, or null if anonymous / invalid token. */
export async function fetchMe(): Promise<MeResponse | null> {
  const token = await getBearerFromCookies();
  if (!token) return null;
  try {
    const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
    const tenant = await getTenantSlugFromCookies();
    if (tenant) headers["X-Tenant-Slug"] = tenant;
    const r = await fetch(`${apiBase()}/v1/auth/me`, {
      headers,
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
  const tenant = await getTenantSlugFromCookies();
  if (tenant) headers.set("X-Tenant-Slug", tenant);
  return fetch(`${apiBase()}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}
