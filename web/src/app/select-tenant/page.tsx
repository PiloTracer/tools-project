import Link from "next/link";
import { redirect } from "next/navigation";

import { SelectTenantPanel } from "./SelectTenantPanel";
import { fetchMe, apiServerFetch } from "@/shared/server/session";
import {
  multiTenancyEnabled,
  tenantChoicesFromCookies,
  tenantSlugFromCookies,
} from "@/shared/server/tenant";

export type TenantOption = {
  slug: string;
  name: string;
  is_active: boolean;
};

/**
 * Tenant picker (multi-tenancy R2b). Needed whenever the session has no tenant
 * claim — i.e. the bootstrap / cross-tenant superuser — because tenant-scoped
 * endpoints require an explicit `X-Tenant-Slug` selection.
 */
export default async function SelectTenantPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  // Only allow same-origin paths as redirect targets (open-redirect guard).
  const next =
    typeof sp.next === "string" && sp.next.startsWith("/") && !sp.next.startsWith("//")
      ? sp.next
      : undefined;

  const me = await fetchMe();
  if (!me) {
    redirect(`/login${next ? `?next=${encodeURIComponent(next)}` : ""}`);
  }

  const current = await tenantSlugFromCookies();
  const choices = await tenantChoicesFromCookies();

  let options: TenantOption[] = [];
  const r = await apiServerFetch("/v1/admin/tenants");
  if (r.ok) {
    const rows = (await r.json()) as Array<{
      slug: string;
      name: string;
      is_active: boolean;
    }>;
    options = rows
      .filter((t) => t.is_active !== false)
      .map((t) => ({ slug: t.slug, name: t.name, is_active: t.is_active !== false }));
  }

  // An ambiguous e-mail meant the API told us exactly which tenants apply (R9b).
  if (choices.length > 0) {
    const allowed = new Set(options.map((o) => o.slug));
    const narrowed = choices.filter((c) => allowed.size === 0 || allowed.has(c.tenant_slug));
    if (narrowed.length > 0) {
      const byslug = new Map(options.map((o) => [o.slug, o]));
      options = narrowed.map((c) => ({
        slug: c.tenant_slug,
        name: c.tenant_name,
        is_active: byslug.get(c.tenant_slug)?.is_active ?? true,
      }));
    }
  }

  if (!multiTenancyEnabled()) {
    return (
      <main className="page-inner stack">
        <h1>Organization</h1>
        <p className="muted">
          This deployment is single-tenant — every account works in one organization.
        </p>
        <p>
          <Link className="btn btn-primary" href={next ?? "/projects"}>
            Continue
          </Link>
        </p>
      </main>
    );
  }

  return (
    <main className="page-inner stack">
      <header className="page-header">
        <div className="page-header__text">
          <span className="pill">Multi-tenant</span>
          <h1>Choose an organization</h1>
          <p className="muted page-header__lead">
            Your account is not bound to a single organization, so pick the one you want to work
            in. Every request is scoped to it until you sign out.
          </p>
        </div>
      </header>
      {options.length === 0 ? (
        <p className="muted">
          No organizations are available to this account. Ask an administrator to grant access,
          then reload this page.
        </p>
      ) : (
        <SelectTenantPanel options={options} current={current} next={next} />
      )}
      <p className="muted">
        Signed in as <strong>{me.email}</strong> · <Link href="/login">Switch account</Link>
      </p>
    </main>
  );
}
