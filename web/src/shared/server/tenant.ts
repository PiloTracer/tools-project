import { cookies } from "next/headers";

import { parseAuthFlag } from "@/shared/server/auth-flags";

/**
 * Multi-tenancy helpers shared by the BFF routes and server components.
 *
 * The browser session cookie (JWT) is not enough in a multi-tenant deployment: a
 * cross-tenant superuser carries no `tenant_id` claim, so the tenant the user is
 * working in is persisted in its own cookie and forwarded to the API as
 * `X-Tenant-Slug` (SPEC multi-tenancy R2b).
 */

/** Tenant selection cookie — forwarded to the API as `X-Tenant-Slug`. */
export const TENANT_COOKIE = process.env.TENANT_COOKIE_NAME || "prj_tenant";
/** Short-lived carry-over of the API's `300 Multiple Choices` list (R9b). */
export const TENANT_CHOICES_COOKIE = "prj_tenant_choices";

export function multiTenancyEnabled(): boolean {
  return parseAuthFlag(process.env.MULTI_TENANCY_ENABLED, false);
}

/**
 * Tenant slug encoded in a `{slug}.PUBLIC_HOST` host header, else null.
 * Mirrors `_tenant_slug_from_host` in the API (api/app/deps.py).
 */
export function tenantSlugFromHost(host: string | null | undefined): string | null {
  const publicHost = (process.env.PUBLIC_HOST || "localhost").trim().toLowerCase();
  const bare = (host || "").split(":")[0].trim().toLowerCase();
  if (!bare || bare === publicHost) return null;
  const suffix = `.${publicHost}`;
  if (!bare.endsWith(suffix)) return null;
  const slug = bare.slice(0, -suffix.length).split(".").pop() || "";
  return slug || null;
}

export function normalizeTenantSlug(raw: unknown): string | null {
  if (typeof raw !== "string") return null;
  const slug = raw.trim().toLowerCase();
  if (!slug || slug.length > 50 || !/^[a-z0-9][a-z0-9-]*$/.test(slug)) return null;
  return slug;
}

export async function tenantSlugFromCookies(): Promise<string | null> {
  const jar = await cookies();
  return normalizeTenantSlug(jar.get(TENANT_COOKIE)?.value);
}

export async function tenantChoicesFromCookies(): Promise<
  Array<{ tenant_slug: string; tenant_name: string }>
> {
  const jar = await cookies();
  const raw = jar.get(TENANT_CHOICES_COOKIE)?.value;
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map((c) => {
        const row = c as { tenant_slug?: unknown; tenant_name?: unknown };
        const slug = normalizeTenantSlug(row.tenant_slug);
        if (!slug) return null;
        return {
          tenant_slug: slug,
          tenant_name: typeof row.tenant_name === "string" ? row.tenant_name : slug,
        };
      })
      .filter((c): c is { tenant_slug: string; tenant_name: string } => c !== null);
  } catch {
    return [];
  }
}

export const TENANT_COOKIE_MAX_AGE = 8 * 60 * 60;
