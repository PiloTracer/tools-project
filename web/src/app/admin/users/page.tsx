import Link from "next/link";
import { cookies } from "next/headers";

import { AdminUsersPanel } from "./AdminUsersPanel";

type UserRow = {
  id: string;
  email: string;
  display_name: string | null;
  auth_source: string;
  is_active: boolean;
  is_superuser: boolean;
};

export default async function AdminUsersPage() {
  const jar = await cookies();
  const cookieName = process.env.SESSION_COOKIE_NAME || "prj_auth";
  const token = jar.get(cookieName)?.value;
  const base =
    process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300";

  let rows: UserRow[] | null = null;
  let forbidden = false;
  let meId = "";

  if (token) {
    const meR = await fetch(`${base}/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (meR.ok) {
      const me = (await meR.json()) as { id: string };
      meId = me.id;
    }
    const r = await fetch(`${base}/v1/admin/users`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (r.status === 401 || r.status === 403) {
      forbidden = true;
    } else if (r.ok) {
      const data = (await r.json()) as { items: UserRow[] };
      rows = data.items;
    }
  } else {
    forbidden = true;
  }

  if (forbidden || rows === null) {
    return (
      <div className="page-inner">
        <main className="card stack wide">
          <h1>User management</h1>
          <p>
            This screen requires a <strong>local superuser</strong> session (JWT issued by this app).
            SSO access tokens are intentionally <strong>not</strong> accepted on{" "}
            <code>/v1/admin/users</code> — operate via a local bootstrap/admin account, or adjust this
            policy when IdP admin claims are wired (see repo <code>.ai/context/HANDOFF.md</code>).
          </p>
          <p>
            <Link className="btn btn-primary" href="/login">
              Sign in
            </Link>{" "}
            <Link href="/">← Home</Link>
          </p>
        </main>
      </div>
    );
  }

  return (
    <div className="page-inner">
      <main className="stack-lg wide" style={{ maxWidth: "920px", margin: "0 auto" }}>
        <div>
          <h1>Local users</h1>
          <p className="muted text-sm">
            Create and patch users via OpenAPI-backed forms (local JWT only).
          </p>
        </div>
        <AdminUsersPanel initialUsers={rows} currentUserId={meId} />
        <p>
          <Link href="/">← Home</Link>
        </p>
      </main>
    </div>
  );
}
