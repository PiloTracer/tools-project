import { cookies } from "next/headers";
import { TenantsPanel } from "./TenantsPanel";

export type TenantRow = {
  id: string;
  slug: string;
  name: string;
  settings: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export default async function AdminTenantsPage() {
  const jar = await cookies();
  const cookieName = process.env.SESSION_COOKIE_NAME || "prj_auth";
  const token = jar.get(cookieName)?.value;
  const base =
    process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300";

  let rows: TenantRow[] = [];
  let forbidden = false;

  if (token) {
    const meR = await fetch(`${base}/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!meR.ok) {
      forbidden = true;
    }
    const r = await fetch(`${base}/v1/admin/tenants`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (r.status === 401 || r.status === 403) {
      forbidden = true;
    } else if (r.ok) {
      rows = (await r.json()) as TenantRow[];
    }
  }

  if (!token) {
    return (
      <main className="stack" style={{ padding: "2rem", maxWidth: 900, margin: "0 auto" }}>
        <h1>Tenants</h1>
        <p className="muted">Please sign in to manage tenants.</p>
      </main>
    );
  }

  if (forbidden) {
    return (
      <main className="stack" style={{ padding: "2rem", maxWidth: 900, margin: "0 auto" }}>
        <h1>Tenants</h1>
        <p className="muted">You do not have permission to manage tenants.</p>
      </main>
    );
  }

  return (
    <main className="stack" style={{ padding: "2rem", maxWidth: 900, margin: "0 auto" }}>
      <h1>Tenants</h1>
      <TenantsPanel tenants={rows} token={token} base={base} />
    </main>
  );
}
