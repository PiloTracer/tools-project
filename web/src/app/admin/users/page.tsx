import Link from "next/link";
import { cookies } from "next/headers";

type UserRow = {
  id: string;
  email: string;
  display_name: string | null;
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

  if (token) {
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
          This screen requires a <strong>local superuser</strong> session (JWT issued
          by this app). SSO-only tokens are not accepted here yet — use the API with a
          local admin account, or call <code>/v1/admin/users</code> from OpenAPI when
          authenticated.
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
      <main className="card stack wide">
      <h1>Local users</h1>
      <p className="muted">
        Admin CRUD via <code>/v1/admin/users</code>. Add UI forms in a follow-up.
      </p>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
            <th style={{ padding: "0.5rem 0" }}>Email</th>
            <th>Name</th>
            <th>Active</th>
            <th>Superuser</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((u) => (
            <tr key={u.id} style={{ borderBottom: "1px solid var(--border)" }}>
              <td style={{ padding: "0.35rem 0" }}>{u.email}</td>
              <td>{u.display_name ?? "—"}</td>
              <td>{u.is_active ? "yes" : "no"}</td>
              <td>{u.is_superuser ? "yes" : "no"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p>
        <Link href="/">← Home</Link>
      </p>
    </main>
    </div>
  );
}
