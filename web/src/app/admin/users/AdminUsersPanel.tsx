"use client";

import { useRouter } from "next/navigation";
import { useState, useMemo, useEffect, useRef } from "react";

import { Dialog } from "@/components/Dialog";
import { toast } from "@/components/Toast";

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

type LinkableContact = {
  id: string;
  client_id: string;
  client_name: string;
  name: string;
  email: string;
  role: string;
};

type ProjectHit = {
  id: string;
  name: string;
  slug: string;
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
                  onRefresh={refreshList}
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

// ── Single user row (with expandable detail) ──────────────────────

function UserRowView({
  user,
  isCurrent,
  expanded,
  busy,
  onToggle,
  onPatch,
  onRefresh,
}: {
  user: UserRow;
  isCurrent: boolean;
  expanded: boolean;
  busy: boolean;
  onToggle: () => void;
  onPatch: (data: Record<string, unknown>) => void;
  onRefresh: () => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [displayName, setDisplayName] = useState(user.display_name ?? "");
  const [isActive, setIsActive] = useState(user.is_active);
  const [isSuperuser, setIsSuperuser] = useState(user.is_superuser);
  const [password, setPassword] = useState("");

  // Contact linking state
  const [showContactSearch, setShowContactSearch] = useState(false);
  const [contactQuery, setContactQuery] = useState("");
  const [contactResults, setContactResults] = useState<LinkableContact[]>([]);
  const [contactPending, setContactPending] = useState(false);
  const contactTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Project add state
  const [showProjectSearch, setShowProjectSearch] = useState(false);
  const [projectQuery, setProjectQuery] = useState("");
  const [projectResults, setProjectResults] = useState<ProjectHit[]>([]);
  const [projectPending, setProjectPending] = useState(false);
  const [selectedProject, setSelectedProject] = useState<ProjectHit | null>(null);
  const [newRole, setNewRole] = useState("contributor");
  const projectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Project membership edit state
  const [editingRole, setEditingRole] = useState<{
    project_id: string;
    role: string;
  } | null>(null);

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

  // ── Contact search ──────────────────────────────────────────

  useEffect(() => {
    if (contactTimer.current) clearTimeout(contactTimer.current);
    if (!contactQuery.trim() || !showContactSearch) {
      setContactResults([]);
      return;
    }
    contactTimer.current = setTimeout(async () => {
      setContactPending(true);
      try {
        const r = await fetch(
          `/api/admin/users/${user.id}/linkable-contacts?q=${encodeURIComponent(contactQuery)}`,
        );
        if (r.ok) setContactResults((await r.json()) ?? []);
        else setContactResults([]);
      } catch {
        setContactResults([]);
      } finally {
        setContactPending(false);
      }
    }, 200);
    return () => {
      if (contactTimer.current) clearTimeout(contactTimer.current);
    };
  }, [contactQuery, user.id, showContactSearch]);

  async function linkContact(contactId: string) {
    const r = await fetch(`/api/admin/users/${user.id}/link-contact`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_contact_id: contactId }),
    });
    if (!r.ok) {
      const text = await r.text();
      toast(text, "error");
      return;
    }
    toast("Contact linked");
    setShowContactSearch(false);
    setContactQuery("");
    setContactResults([]);
    await onRefresh();
  }

  async function unlinkContact() {
    const r = await fetch(`/api/admin/users/${user.id}/link-contact`, {
      method: "DELETE",
    });
    if (!r.ok) {
      const text = await r.text();
      toast(text, "error");
      return;
    }
    toast("Contact unlinked");
    await onRefresh();
  }

  // ── Project search ──────────────────────────────────────────

  useEffect(() => {
    if (projectTimer.current) clearTimeout(projectTimer.current);
    if (!projectQuery.trim() || !showProjectSearch) {
      setProjectResults([]);
      return;
    }
    const memberProjectIds = new Set(user.memberships.map((m) => m.project_id));
    projectTimer.current = setTimeout(async () => {
      setProjectPending(true);
      try {
        const r = await fetch("/api/projects", { cache: "no-store" });
        if (r.ok) {
          const data = (await r.json()) as { items: ProjectHit[] };
          const filtered = data.items.filter(
            (p) =>
              !memberProjectIds.has(p.id) &&
              (p.name.toLowerCase().includes(projectQuery.toLowerCase()) ||
                p.slug.toLowerCase().includes(projectQuery.toLowerCase())),
          );
          setProjectResults(filtered);
        } else {
          setProjectResults([]);
        }
      } catch {
        setProjectResults([]);
      } finally {
        setProjectPending(false);
      }
    }, 200);
    return () => {
      if (projectTimer.current) clearTimeout(projectTimer.current);
    };
  }, [projectQuery, user.memberships, showProjectSearch]);

  async function addToProject() {
    if (!selectedProject) return;
    const r = await fetch(`/api/admin/users/${user.id}/add-to-project`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_id: selectedProject.id,
        role: newRole,
      }),
    });
    if (!r.ok) {
      const text = await r.text();
      toast(text, "error");
      return;
    }
    toast(`Added to ${selectedProject.name}`);
    setShowProjectSearch(false);
    setProjectQuery("");
    setSelectedProject(null);
    setProjectResults([]);
    await onRefresh();
  }

  async function changeRole(projectId: string, role: string) {
    const r = await fetch(
      `/api/admin/users/${user.id}/project-membership/${projectId}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      },
    );
    if (!r.ok) {
      const text = await r.text();
      toast(text, "error");
      return;
    }
    toast("Role updated");
    setEditingRole(null);
    await onRefresh();
  }

  async function removeFromProject(projectId: string, projectName: string) {
    if (!window.confirm(`Remove this user from "${projectName}"?`)) return;
    const r = await fetch(
      `/api/admin/users/${user.id}/project-membership/${projectId}`,
      { method: "DELETE" },
    );
    if (!r.ok) {
      const text = await r.text();
      toast(text, "error");
      return;
    }
    toast(`Removed from ${projectName}`);
    await onRefresh();
  }

  // ── Row data ────────────────────────────────────────────────

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
              ` · ${user.client_contacts.length} contact`}
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
              {/* ── Edit user properties ──────────────────────── */}
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.6rem",
                  alignItems: "flex-end",
                  marginBottom: "1rem",
                  paddingBottom: "0.75rem",
                  borderBottom: "1px solid var(--border)",
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

              {/* ── Client contact linking ────────────────────── */}
              <div style={{ marginBottom: "0.75rem" }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "0.35rem",
                  }}
                >
                  <h4 className="text-sm" style={{ margin: 0, fontWeight: 600 }}>
                    Client contact
                  </h4>
                  {user.client_contacts.length > 0 ? (
                    <button
                      type="button"
                      className="btn btn-ghost text-sm"
                      onClick={unlinkContact}
                      style={{ color: "var(--err)", minHeight: "1.8rem" }}
                    >
                      Unlink
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="btn btn-ghost text-sm"
                      onClick={() => setShowContactSearch(true)}
                      style={{ minHeight: "1.8rem" }}
                    >
                      + Link contact
                    </button>
                  )}
                </div>

                {user.client_contacts.length > 0 ? (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                    {user.client_contacts.map((c) => (
                      <span
                        key={c.id}
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
                ) : (
                  <p className="muted text-sm" style={{ margin: 0 }}>
                    No linked client contact.
                  </p>
                )}

                {/* Contact search dropdown */}
                {showContactSearch && (
                  <div style={{ marginTop: "0.5rem", position: "relative" }}>
                    <input
                      className="input text-sm"
                      placeholder="Search contacts by name, email, or company…"
                      value={contactQuery}
                      onChange={(e) => setContactQuery(e.target.value)}
                      autoComplete="off"
                      style={{ width: "100%", minHeight: "2.25rem" }}
                    />
                    {contactPending && (
                      <p className="muted text-sm" style={{ margin: "0.3rem 0" }}>
                        Searching…
                      </p>
                    )}
                    {contactResults.length > 0 && (
                      <div
                        style={{
                          marginTop: "0.25rem",
                          maxHeight: "12rem",
                          overflowY: "auto",
                          border: "1px solid var(--border)",
                          borderRadius: 6,
                          background: "var(--bg-elevated)",
                        }}
                      >
                        {contactResults.map((c) => (
                          <button
                            key={c.id}
                            type="button"
                            className="btn-ghost"
                            style={{
                              display: "block",
                              width: "100%",
                              textAlign: "left",
                              padding: "0.5rem",
                              borderRadius: 0,
                              border: "none",
                              borderBottom: "1px solid var(--border)",
                              cursor: "pointer",
                              background: "transparent",
                              fontFamily: "inherit",
                              fontSize: "0.85rem",
                              color: "var(--text)",
                            }}
                            onClick={() => linkContact(c.id)}
                          >
                            <div style={{ fontWeight: 600 }}>{c.name}</div>
                            <div className="muted" style={{ fontSize: "0.78rem" }}>
                              {c.email} · {c.client_name} ({c.role})
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                    {contactQuery && !contactPending && contactResults.length === 0 && (
                      <p className="muted text-sm" style={{ margin: "0.3rem 0" }}>
                        No matching contacts.
                      </p>
                    )}
                    <button
                      type="button"
                      className="btn btn-ghost text-sm"
                      onClick={() => {
                        setShowContactSearch(false);
                        setContactQuery("");
                        setContactResults([]);
                      }}
                      style={{ marginTop: "0.3rem" }}
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>

              {/* ── Project memberships ────────────────────────── */}
              <div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "0.35rem",
                  }}
                >
                  <h4 className="text-sm" style={{ margin: 0, fontWeight: 600 }}>
                    Project memberships
                  </h4>
                  <button
                    type="button"
                    className="btn btn-ghost text-sm"
                    onClick={() => setShowProjectSearch(true)}
                    style={{ minHeight: "1.8rem" }}
                  >
                    + Add to project
                  </button>
                </div>

                {user.memberships.length === 0 ? (
                  <p className="muted text-sm" style={{ margin: 0 }}>
                    Not a member of any project.
                  </p>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                    {user.memberships.map((m) => (
                      <div
                        key={m.project_id}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "0.5rem",
                          padding: "0.3rem 0.5rem",
                          borderRadius: 6,
                          background: "var(--bg-subtle, #f5f5f5)",
                        }}
                      >
                        <span style={{ flex: 1, fontSize: "0.85rem", fontWeight: 500 }}>
                          {m.project_name}
                        </span>

                        {editingRole?.project_id === m.project_id ? (
                          <>
                            <select
                              className="input text-sm"
                              value={editingRole.role}
                              onChange={(e) =>
                                setEditingRole({ ...editingRole, role: e.target.value })
                              }
                              style={{ width: "auto", minHeight: "2rem", padding: "0.2rem 0.4rem" }}
                            >
                              <option value="viewer">viewer</option>
                              <option value="contributor">contributor</option>
                              <option value="maintainer">maintainer</option>
                              <option value="owner">owner</option>
                            </select>
                            <button
                              type="button"
                              className="btn btn-primary text-sm"
                              onClick={() => changeRole(m.project_id, editingRole.role)}
                              style={{ minHeight: "2rem", padding: "0.2rem 0.6rem", fontSize: "0.78rem" }}
                            >
                              Save
                            </button>
                            <button
                              type="button"
                              className="btn btn-ghost text-sm"
                              onClick={() => setEditingRole(null)}
                              style={{ minHeight: "2rem", padding: "0.2rem 0.4rem", fontSize: "0.78rem" }}
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <>
                            <span
                              className="pill"
                              style={{ fontSize: "0.72rem", background: "var(--accent)", color: "#fff" }}
                            >
                              {m.role}
                            </span>
                            <button
                              type="button"
                              className="btn btn-ghost text-sm"
                              onClick={() =>
                                setEditingRole({ project_id: m.project_id, role: m.role })
                              }
                              style={{ minHeight: "1.8rem", padding: "0.2rem 0.4rem", fontSize: "0.78rem" }}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              className="btn btn-ghost text-sm"
                              onClick={() => removeFromProject(m.project_id, m.project_name)}
                              style={{
                                color: "var(--err)",
                                minHeight: "1.8rem",
                                padding: "0.2rem 0.4rem",
                                fontSize: "0.78rem",
                              }}
                            >
                              Remove
                            </button>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Add to project search */}
                {showProjectSearch && (
                  <div
                    style={{
                      marginTop: "0.5rem",
                      padding: "0.5rem",
                      border: "1px solid var(--border)",
                      borderRadius: 6,
                      background: "var(--bg-elevated)",
                    }}
                  >
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "flex-end" }}>
                      <label className="stack" style={{ flex: "1 1 200px", gap: "0.15rem" }}>
                        <span className="text-sm muted">Search project</span>
                        <input
                          className="input text-sm"
                          value={
                            selectedProject
                              ? selectedProject.name
                              : projectQuery
                          }
                          onChange={(e) => {
                            setSelectedProject(null);
                            setProjectQuery(e.target.value);
                          }}
                          placeholder="Type to search…"
                          autoComplete="off"
                          style={{ minHeight: "2.25rem" }}
                        />
                      </label>
                      <label className="stack" style={{ gap: "0.15rem" }}>
                        <span className="text-sm muted">Role</span>
                        <select
                          className="input text-sm"
                          value={newRole}
                          onChange={(e) => setNewRole(e.target.value)}
                          style={{ minHeight: "2.25rem" }}
                        >
                          <option value="viewer">viewer</option>
                          <option value="contributor">contributor</option>
                          <option value="maintainer">maintainer</option>
                          <option value="owner">owner</option>
                        </select>
                      </label>
                      <button
                        type="button"
                        className="btn btn-primary text-sm"
                        disabled={!selectedProject}
                        onClick={addToProject}
                        style={{ minHeight: "2.25rem" }}
                      >
                        Add
                      </button>
                      <button
                        type="button"
                        className="btn btn-ghost text-sm"
                        onClick={() => {
                          setShowProjectSearch(false);
                          setProjectQuery("");
                          setSelectedProject(null);
                          setProjectResults([]);
                        }}
                        style={{ minHeight: "2.25rem" }}
                      >
                        Cancel
                      </button>
                    </div>

                    {selectedProject ? (
                      <p className="text-sm" style={{ margin: "0.3rem 0 0", color: "var(--muted)" }}>
                        Selected: <strong>{selectedProject.name}</strong>
                      </p>
                    ) : projectPending ? (
                      <p className="muted text-sm" style={{ margin: "0.3rem 0 0" }}>
                        Searching…
                      </p>
                    ) : projectResults.length > 0 ? (
                      <div
                        style={{
                          marginTop: "0.3rem",
                          maxHeight: "10rem",
                          overflowY: "auto",
                          border: "1px solid var(--border)",
                          borderRadius: 6,
                        }}
                      >
                        {projectResults.map((p) => (
                          <button
                            key={p.id}
                            type="button"
                            className="btn-ghost"
                            style={{
                              display: "block",
                              width: "100%",
                              textAlign: "left",
                              padding: "0.4rem 0.5rem",
                              borderRadius: 0,
                              border: "none",
                              borderBottom: "1px solid var(--border)",
                              cursor: "pointer",
                              background: "transparent",
                              fontFamily: "inherit",
                              fontSize: "0.85rem",
                              color: "var(--text)",
                            }}
                            onClick={() => {
                              setSelectedProject(p);
                              setProjectResults([]);
                            }}
                          >
                            {p.name}
                          </button>
                        ))}
                      </div>
                    ) : projectQuery && !selectedProject && (
                      <p className="muted text-sm" style={{ margin: "0.3rem 0 0" }}>
                        No matching projects.
                      </p>
                    )}
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
