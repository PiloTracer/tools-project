"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type UserRow = {
  id: string;
  email: string;
  display_name: string | null;
  auth_source: string;
  is_active: boolean;
  is_superuser: boolean;
};

export function AdminUsersPanel({
  initialUsers,
  currentUserId,
}: {
  initialUsers: UserRow[];
  currentUserId: string;
}) {
  const router = useRouter();
  const [users, setUsers] = useState(initialUsers);
  const [createMsg, setCreateMsg] = useState<string | null>(null);

  async function refreshList() {
    const r = await fetch("/api/admin/users", { cache: "no-store" });
    if (r.ok) {
      const data = (await r.json()) as { items: UserRow[] };
      setUsers(data.items);
    }
    router.refresh();
  }

  async function createUser(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setCreateMsg(null);
    const fd = new FormData(e.currentTarget);
    const body = {
      email: String(fd.get("email") || "").trim(),
      password: String(fd.get("password") || ""),
      display_name: String(fd.get("display_name") || "").trim() || null,
      is_superuser: fd.get("is_superuser") === "on",
    };
    const r = await fetch("/api/admin/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const text = await r.text();
    if (!r.ok) {
      try {
        const j = JSON.parse(text) as { detail?: string };
        setCreateMsg(j.detail ?? text);
      } catch {
        setCreateMsg(text || `Error ${r.status}`);
      }
      return;
    }
    (e.target as HTMLFormElement).reset();
    await refreshList();
  }

  async function patchUser(userId: string, form: HTMLFormElement) {
    const fd = new FormData(form);
    const payload: Record<string, unknown> = {};
    const dn = String(fd.get("display_name") ?? "").trim();
    payload.display_name = dn || null;
    payload.is_active = fd.get("is_active") === "on";
    payload.is_superuser = fd.get("is_superuser") === "on";
    const pw = String(fd.get("password") ?? "").trim();
    if (pw) {
      payload.password = pw;
    }
    const r = await fetch(`/api/admin/users/${userId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) {
      const text = await r.text();
      alert(text);
      return;
    }
    await refreshList();
  }

  return (
    <div className="stack-lg">
      <section className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Create local user</h2>
        <form className="stack" style={{ gap: "0.65rem", maxWidth: "28rem" }} onSubmit={createUser}>
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span className="text-sm muted">Email</span>
            <input className="input" name="email" type="email" required />
          </label>
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span className="text-sm muted">Password (min 8)</span>
            <input className="input" name="password" type="password" minLength={8} required />
          </label>
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span className="text-sm muted">Display name</span>
            <input className="input" name="display_name" />
          </label>
          <label className="row" style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <input name="is_superuser" type="checkbox" />
            <span className="text-sm">Superuser</span>
          </label>
          <button type="submit" className="btn btn-primary">
            Create user
          </button>
        </form>
        {createMsg ? <p className="err text-sm">{createMsg}</p> : null}
      </section>

      <section className="card wide">
        <h2 style={{ marginTop: 0 }}>Users</h2>
        <div className="stack" style={{ gap: "1rem" }}>
          {users.map((u) => (
            <form
              key={u.id}
              className="stack"
              style={{
                gap: "0.5rem",
                padding: "0.75rem 0",
                borderBottom: "1px solid var(--border)",
              }}
              onSubmit={(e) => {
                e.preventDefault();
                patchUser(u.id, e.currentTarget);
              }}
            >
              <div className="text-sm muted">
                {u.email}{" "}
                <span className="pill" style={{ fontSize: "0.7rem", marginLeft: "0.4rem" }}>
                  {u.auth_source}
                </span>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "flex-end" }}>
                <label className="stack" style={{ gap: "0.15rem", flex: "1 1 160px" }}>
                  <span className="text-sm muted">Display name</span>
                  <input
                    className="input text-sm"
                    name="display_name"
                    defaultValue={u.display_name ?? ""}
                    style={{ minHeight: "2.25rem" }}
                  />
                </label>
                <label className="row text-sm" style={{ display: "flex", gap: "0.35rem", alignItems: "center" }}>
                  <input name="is_active" type="checkbox" defaultChecked={u.is_active} />
                  Active
                </label>
                <label className="row text-sm" style={{ display: "flex", gap: "0.35rem", alignItems: "center" }}>
                  <input
                    name="is_superuser"
                    type="checkbox"
                    defaultChecked={u.is_superuser}
                    disabled={u.id === currentUserId}
                  />
                  Superuser
                </label>
                <label className="stack" style={{ gap: "0.15rem", flex: "1 1 180px" }}>
                  <span className="text-sm muted">New password</span>
                  <input
                    className="input text-sm"
                    name="password"
                    type="password"
                    minLength={8}
                    placeholder="optional"
                    style={{ minHeight: "2.25rem" }}
                  />
                </label>
                <button type="submit" className="btn btn-primary text-sm">
                  Save
                </button>
              </div>
            </form>
          ))}
        </div>
      </section>
    </div>
  );
}
