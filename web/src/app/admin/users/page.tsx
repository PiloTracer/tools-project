import Link from "next/link";
import { redirect } from "next/navigation";
import { cookies } from "next/headers";

import { AdminUsersPanel } from "./AdminUsersPanel";

type UserMembership = {
  project_id: string;
  project_name: string;
  role: string;
};

type UserClientContact = {
  id: string;
  client_id: string;
  client_name: string;
  role: string;
  email: string;
  name: string;
};

type UserRow = {
  id: string;
  email: string;
  display_name: string | null;
  auth_source: string;
  is_active: boolean;
  is_superuser: boolean;
  memberships: UserMembership[];
  client_contacts: UserClientContact[];
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
    redirect("/login");
  }

  if (forbidden || !rows) {
    redirect("/login");
  }

  return (
    <div className="page-inner">
      <main className="stack-lg wide" style={{ maxWidth: "960px", margin: "0 auto" }}>
        <div>
          <h1>User administration</h1>
          <p className="muted text-sm">
            Manage all users, their roles, and project memberships.
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
