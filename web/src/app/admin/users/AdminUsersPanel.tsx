"use client";

import { useRouter } from "next/navigation";
import { useState, useMemo } from "react";

import { Dialog } from "@/components/Dialog";
import { toast } from "@/components/Toast";

type UserMembership = {
  project_id: string;
  project_name: string;
  role: string;
};

type UserClientContact = {
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

export function AdminUsersPanel({
  initialUsers,
  currentUserId,
}: {
  initialUsers: UserRow[];
  currentUserId: string;
}) {
  const router = useRouter();
  const [users, setUsers] = useState(initialUsers);
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    if (!search.trim()) return users;
    const t = search.trim().toLowerCase();
    return users.filter(
      (u) =>
        u.email.toLowerCase().includes(t) ||
        (u.display_name ?? "").toLowerCase().includes(t),
    );
  }, [users, search]);

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
        toast(j.detail ?? text, "error");
      } catch {
        toast(text || `Error ${r.status}`, "error");
      }
      return;
    }
    setShowCreate(false);
    toast("User created");
    await refreshList();
  }

  async function patchUser(
    userId: string,
    data: Record<string, unknown>,
  ) {
    setBusyId(userId);
    try {
      const r = await fetch(`/api/admin/users/${userId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!r.ok) {
        const text = await r.text();
        toast(text, "error");
        return;
      }
      await refreshList();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="stack-lg">
      {/* Toolbar */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.75rem",
          alignItems: "center",
        }}
      >
        <input
          className="input"
          placeholder="Search by email or name…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: "1 1 240px", minHeight: "2.5rem" }}
          autoComplete="off"
        />
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => setShowCreate(true)}
        >
          + Create user
        </button>
      </div>

      {/* User count */}
      <p className="muted text-sm">
        {filtered.length} user{filtered.length !== 1 ? "s" : ""}
        {search.trim() && filtered.length !== users.length
          ? ` (filtered from ${users.length})`
          : ""}
      </p>

      {/* User list */}
      <div className="card wide" style={{ padding: 0, overflow: "hidden" }}>
        {filtered.length === 0 ? (
          <p className="muted" style={{ padding: "1.5rem" }}>
            {search.trim() ? "No users match your search." : "No users yet."}
          </p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr
                style={{
                  textAlign: "left",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <th style={{ padding: "0.75rem 0.75rem 0.5rem" }}>User</th>
                <th style={{ padding: "0.75rem 0.75rem 0.5rem" }}>Status</th>
                <th style={{ padding: "0.75rem 0.75rem 0.5rem" }}>Auth</th>
                <th style={{ padding: "0.75rem 0.75rem 0.5rem" }}>
                  Memberships
                </th>
                <th style={{ width: 0, padding: "0.75rem 0.75rem 0.5rem" }} />
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => (
                <UserRowView
                  key={u.id}
                  user={u}
                  isCurrent={u.id === currentUserId}
                  expanded={expandedId === u.id}
                  busy={busyId === u.id}
                  onToggle={() =>
                    setExpandedId(expandedId === u.id ? null : u.id)
                  }
                  onPatch={(data) => patchUser(u.id, data)}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create user dialog */}
      <Dialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="Create local user"
      >
        <form
          className="stack"
          style={{ gap: "0.75rem", minWidth: "22rem" }}
          onSubmit={createUser}
          autoComplete="off"
        >
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span className="text-sm muted">Email</span>
            <input
              className="input"
              name="email"
              type="email"
              required
              autoComplete="off"
            />
          </label>
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span className="text-sm muted">Password (min 8)</span>
            <input
              className="input"
              name="password"
              type="password"
              minLength={8}
              required
              autoComplete="new-password"
            />
          </label>
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span className="text-sm muted">Display name</span>
            <input className="input" name="display_name" autoComplete="off" />
          </label>
          <label
            className="row"
            style={{
              display: "flex",
              gap: "0.5rem",
              alignItems: "center",
            }}
          >
            <input name="is_superuser" type="checkbox" />
            <span className="text-sm">Superuser</span>
          </label>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ flex: 1 }}
            >
              Create user
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setShowCreate(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}

function UserRowView({
  user,
  isCurrent,
  expanded,
  busy,
  onToggle,
  onPatch,
}: {
  user: UserRow;
  isCurrent: boolean;
  expanded: boolean;
  busy: boolean;
  onToggle: () => void;
  onPatch: (data: Record<string, unknown>) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [displayName, setDisplayName] = useState(user.display_name ?? "");
  const [isActive, setIsActive] = useState(user.is_active);
  const [isSuperuser, setIsSuperuser] = useState(user.is_superuser);
  const [password, setPassword] = useState("");

  function save() {
    const payload: Record<string, unknown> = {};
    if (displayName !== (user.display_name ?? "")) {
      payload.display_name = displayName || null;
    }
    if (isActive !== user.is_active) {
      payload.is_active = isActive;
    }
    if (isSuperuser !== user.is_superuser) {
      payload.is_superuser = isSuperuser;
    }
    if (password) {
      payload.password = password;
    }
    if (Object.keys(payload).length === 0) {
      setEditing(false);
      return;
    }
    onPatch(payload);
    setEditing(false);
    setPassword("");
  }

  function cancel() {
    setDisplayName(user.display_name ?? "");
    setIsActive(user.is_active);
    setIsSuperuser(user.is_superuser);
    setPassword("");
    setEditing(false);
  }

  const statusColor = user.is_active ? "var(--success)" : "var(--err)";
  const statusLabel = user.is_active ? "Active" : "Inactive";

  return (
    <>
      <tr
        style={{
          borderBottom: "1px solid var(--border)",
          cursor: "pointer",
          opacity: user.is_active ? 1 : 0.55,
        }}
        onClick={onToggle}
      >
        <td style={{ padding: "0.7rem 0.75rem" }}>
          <div style={{ fontWeight: 600 }}>{user.email}</div>
          {user.display_name && (
            <div className="muted text-sm">{user.display_name}</div>
          )}
        </td>
        <td style={{ padding: "0.7rem 0.75rem" }}>
          <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
            <span
              className="pill"
              style={{
                background: statusColor,
                color: "#fff",
                fontSize: "0.7rem",
              }}
            >
              {statusLabel}
            </span>
            {user.is_superuser && (
              <span
                className="pill"
                style={{
                  background: "var(--accent)",
                  color: "#fff",
                  fontSize: "0.7rem",
                }}
              >
                Superuser
              </span>
            )}
          </div>
        </td>
        <td style={{ padding: "0.7rem 0.75rem" }}>
          <span className="pill text-sm">{user.auth_source}</span>
        </td>
        <td style={{ padding: "0.7rem 0.75rem" }}>
          <span className="text-sm">
            {user.memberships.length} project
            {user.memberships.length !== 1 ? "s" : ""}
            {user.client_contacts.length > 0 &&
              ` · ${user.client_contacts.length} client contact${user.client_contacts.length !== 1 ? "s" : ""}`}
          </span>
        </td>
        <td style={{ padding: "0.7rem 0.75rem" }}>
          <span className="text-sm muted" style={{ whiteSpace: "nowrap" }}>
            {expanded ? "▲" : "▼"}
          </span>
        </td>
      </tr>

      {expanded && (
        <tr>
          <td colSpan={5} style={{ padding: 0 }}>
            <div
              style={{
                padding: "0.75rem 1rem 1rem",
                background: "var(--bg-elevated, #fafafa)",
                borderBottom: "1px solid var(--border)",
              }}
            >
              {/* Edit user properties */}
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.6rem",
                  alignItems: "flex-end",
                  marginBottom: "1rem",
                }}
              >
                <label className="stack" style={{ gap: "0.15rem", flex: "1 1 180px" }}>
                  <span className="text-sm muted">Display name</span>
                  <input
                    className="input text-sm"
                    value={editing ? displayName : (user.display_name ?? "")}
                    onChange={(e) => {
                      setDisplayName(e.target.value);
                      if (!editing) setEditing(true);
                    }}
                    autoComplete="off"
                    style={{ minHeight: "2.25rem" }}
                  />
                </label>
                <label
                  className="row text-sm"
                  style={{
                    display: "flex",
                    gap: "0.35rem",
                    alignItems: "center",
                    padding: "0.25rem 0",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={editing ? isActive : user.is_active}
                    onChange={(e) => {
                      setIsActive(e.target.checked);
                      if (!editing) setEditing(true);
                    }}
                  />
                  Active
                </label>
                <label
                  className="row text-sm"
                  style={{
                    display: "flex",
                    gap: "0.35rem",
                    alignItems: "center",
                    padding: "0.25rem 0",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={editing ? isSuperuser : user.is_superuser}
                    onChange={(e) => {
                      if (!isCurrent) {
                        setIsSuperuser(e.target.checked);
                        if (!editing) setEditing(true);
                      }
                    }}
                    disabled={isCurrent}
                  />
                  Superuser
                </label>
                <label className="stack" style={{ gap: "0.15rem", flex: "1 1 160px" }}>
                  <span className="text-sm muted">New password</span>
                  <input
                    className="input text-sm"
                    type="password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (!editing) setEditing(true);
                    }}
                    minLength={8}
                    placeholder="unchanged"
                    autoComplete="new-password"
                    style={{ minHeight: "2.25rem" }}
                  />
                </label>
                {editing && (
                  <div style={{ display: "flex", gap: "0.4rem", alignItems: "flex-end", padding: "0.25rem 0" }}>
                    <button
                      type="button"
                      className="btn btn-primary text-sm"
                      disabled={busy}
                      onClick={save}
                      style={{ minHeight: "2.25rem" }}
                    >
                      {busy ? "Saving…" : "Save"}
                    </button>
                    <button
                      type="button"
                      className="btn btn-ghost text-sm"
                      onClick={cancel}
                      style={{ minHeight: "2.25rem" }}
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>

              {/* Memberships section */}
              <div style={{ marginBottom: "0.75rem" }}>
                <h4
                  className="text-sm"
                  style={{
                    margin: 0,
                    marginBottom: "0.35rem",
                    fontWeight: 600,
                  }}
                >
                  Project memberships
                </h4>
                {user.memberships.length === 0 ? (
                  <p className="muted text-sm" style={{ margin: 0 }}>
                    Not a member of any project.
                  </p>
                ) : (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                    {user.memberships.map((m) => (
                      <span
                        key={m.project_id}
                        className="pill"
                        style={{ fontSize: "0.78rem", background: "var(--bg-subtle, #eee)" }}
                      >
                        {m.project_name}{" "}
                        <span style={{ fontWeight: 600 }}>{m.role}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Client contacts section */}
              <div>
                <h4
                  className="text-sm"
                  style={{
                    margin: 0,
                    marginBottom: "0.35rem",
                    fontWeight: 600,
                  }}
                >
                  Client contacts
                </h4>
                {user.client_contacts.length === 0 ? (
                  <p className="muted text-sm" style={{ margin: 0 }}>
                    No linked client contacts.
                  </p>
                ) : (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                    {user.client_contacts.map((c, i) => (
                      <span
                        key={`${c.client_id}-${i}`}
                        className="pill"
                        style={{
                          fontSize: "0.78rem",
                          background: "var(--bg-subtle, #eee)",
                        }}
                      >
                        {c.name} @ {c.client_name}
                        <span style={{ fontWeight: 600 }}> ({c.role})</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
