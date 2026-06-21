"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect, useCallback, useRef } from "react";

import { Badge } from "@/components/Badge";
import { Dialog } from "@/components/Dialog";
import { toast } from "@/components/Toast";

type LinkedClientRow = {
  id: string;
  client_id: string;
  client_name: string;
  client_slug: string;
  created_at: string;
};

type AccessRow = {
  id: string;
  client_contact_id: string;
  contact_name: string | null;
  contact_email: string | null;
  client_name: string | null;
  role: string;
  can_view_tasks: boolean;
  can_view_tickets: boolean;
  can_create_tasks: boolean;
};

type ContactRow = {
  id: string;
  client_id: string;
  client_name: string | null;
  name: string;
  email: string;
  phone: string | null;
  title: string | null;
  role: string;
  is_primary: boolean;
};

type SearchHit = {
  client_id: string;
  client_name: string;
  client_slug: string;
  contact_name: string | null;
  contact_email: string | null;
};

const CLIENT_ROLES = ["view", "contribute", "decision_maker", "billing"];

export function ClientSettingsForm({
  projectId,
  canEdit,
}: {
  projectId: string;
  canEdit: boolean;
}) {
  const router = useRouter();
  const [linkedClients, setLinkedClients] = useState<LinkedClientRow[]>([]);
  const [accessGrants, setAccessGrants] = useState<AccessRow[]>([]);
  const [showLinkClient, setShowLinkClient] = useState(false);
  const [showGrantAccess, setShowGrantAccess] = useState(false);
  const [contacts, setContacts] = useState<ContactRow[]>([]);
  const [contactsLoading, setContactsLoading] = useState(false);
  const [selectedContactId, setSelectedContactId] = useState("");
  const [selectedRole, setSelectedRole] = useState("view");
  const [canCreateTasks, setCanCreateTasks] = useState(false);
  const [editAccess, setEditAccess] = useState<AccessRow | null>(null);
  const [editRole, setEditRole] = useState("view");
  const [editViewTasks, setEditViewTasks] = useState(true);
  const [editViewTickets, setEditViewTickets] = useState(false);
  const [editCreateTasks, setEditCreateTasks] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchHit[]>([]);
  const [searchPending, setSearchPending] = useState(false);
  const [selectedClient, setSelectedClient] = useState<SearchHit | null>(null);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchData = useCallback(async () => {
    const [lc, ag] = await Promise.all([
      fetch(`/api/projects/${projectId}/clients`),
      fetch(`/api/projects/${projectId}/client-access`),
    ]);
    if (lc.ok) setLinkedClients((await lc.json()).items ?? []);
    if (ag.ok) setAccessGrants((await ag.json()).items ?? []);
  }, [projectId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
  }, [fetchData]);

  const openGrantAccess = async () => {
    setContactsLoading(true);
    setShowGrantAccess(true);
    try {
      const r = await fetch(`/api/projects/${projectId}/client-contacts`);
      if (r.ok) {
        setContacts((await r.json()).items ?? []);
      } else {
        setContacts([]);
      }
    } catch {
      setContacts([]);
    } finally {
      setContactsLoading(false);
    }
  };

  const openLinkClient = () => {
    setSearchQuery("");
    setSearchResults([]);
    setSelectedClient(null);
    setShowLinkClient(true);
  };

  const doSearch = useCallback(
    async (q: string) => {
      if (q.length < 1) {
        setSearchResults([]);
        setSearchPending(false);
        return;
      }
      setSearchPending(true);
      try {
        const r = await fetch(
          `/api/projects/${projectId}/clients/search?q=${encodeURIComponent(q)}`,
        );
        if (r.ok) {
          setSearchResults((await r.json()).items ?? []);
        }
      } catch {
        setSearchResults([]);
      } finally {
        setSearchPending(false);
      }
    },
    [projectId],
  );

  useEffect(() => {
    if (!showLinkClient) return;
    if (searchTimer.current) clearTimeout(searchTimer.current);
    if (selectedClient) return;
    searchTimer.current = setTimeout(() => doSearch(searchQuery), 200);
    return () => {
      if (searchTimer.current) clearTimeout(searchTimer.current);
    };
  }, [searchQuery, showLinkClient, selectedClient, doSearch]);

  if (!canEdit) {
    return (
      <div>
        <h2 style={{ marginTop: 0 }}>Clients</h2>
        <p className="muted text-sm">Only owners and maintainers can manage client links.</p>
        {linkedClients.length > 0 && (
          <ul style={{ marginTop: "0.5rem" }}>
            {linkedClients.map((c) => <li key={c.id}>{c.client_name}</li>)}
          </ul>
        )}
      </div>
    );
  }

  const handleLinkClient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClient) return;
    const r = await fetch(`/api/projects/${projectId}/clients`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: selectedClient.client_id }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Failed to link" }));
      toast(err.detail, "error");
      return;
    }
    toast("Client linked");
    setSelectedClient(null);
    setSearchQuery("");
    setSearchResults([]);
    setShowLinkClient(false);
    fetchData();
    router.refresh();
  };

  const handleUnlink = async (clientId: string) => {
    const r = await fetch(`/api/projects/${projectId}/clients?client_id=${clientId}`, { method: "DELETE" });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Failed to unlink" }));
      toast(err.detail, "error");
      return;
    }
    toast("Client unlinked");
    fetchData();
    router.refresh();
  };

  const handleRevokeAccess = async (accessId: string) => {
    const r = await fetch(`/api/projects/${projectId}/client-access/${accessId}`, { method: "DELETE" });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Failed to revoke access" }));
      toast(err.detail, "error");
      return;
    }
    toast("Access revoked");
    fetchData();
  };

  const handleGrantAccess = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedContactId) return;
    const r = await fetch(`/api/projects/${projectId}/client-access`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_contact_id: selectedContactId,
        role: selectedRole,
        can_create_tasks: canCreateTasks,
      }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Failed to grant access" }));
      toast(err.detail, "error");
      return;
    }
    toast("Access granted");
    setShowGrantAccess(false);
    fetchData();
  };

  const alreadyHasAccess = (contactId: string) =>
    accessGrants.some((a) => a.client_contact_id === contactId);

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Clients</h2>

      {linkedClients.length > 0 ? (
        <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "1rem" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
              <th style={{ padding: "0.5rem 0" }}>Client</th>
              <th>Slug</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {linkedClients.map((c) => (
              <tr key={c.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: "0.35rem 0", fontWeight: 600 }}>{c.client_name}</td>
                <td style={{ fontFamily: "ui-monospace, monospace", fontSize: "0.82rem", color: "var(--muted)" }}>
                  {c.client_slug}
                </td>
                <td style={{ textAlign: "right" }}>
                  <button className="btn btn-sm btn-ghost" style={{ color: "var(--danger)" }} onClick={() => handleUnlink(c.client_id)}>
                    Unlink
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="muted text-sm">No clients linked to this project yet.</p>
      )}

      <button className="btn btn-sm btn-secondary" onClick={openLinkClient}>
        Link client
      </button>

      <Dialog
        open={showLinkClient}
        onClose={() => setShowLinkClient(false)}
        title="Link client to project"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setShowLinkClient(false)}>Cancel</button>
            <button type="submit" form="link-client-form" className="btn btn-primary" disabled={!selectedClient}>Link</button>
          </>
        }
      >
        <form id="link-client-form" onSubmit={handleLinkClient} className="stack" style={{ gap: "0.65rem" }}>
          <label className="field">
            <span className="label">Search by name, email or company</span>
            <input
              className="input"
              value={selectedClient ? `${selectedClient.client_name} — ${selectedClient.contact_name ?? selectedClient.contact_email ?? ""}` : searchQuery}
              onChange={(e) => {
                setSelectedClient(null);
                setSearchQuery(e.target.value);
              }}
              placeholder="Type to search…"
              autoFocus
              autoComplete="off"
            />
          </label>

          {selectedClient ? (
            <div style={{ padding: "0.35rem 0", color: "var(--muted)", fontSize: "0.85rem" }}>
              Selected: <strong>{selectedClient.client_name}</strong>
              {selectedClient.contact_name ? ` — ${selectedClient.contact_name}` : ""}
              {selectedClient.contact_email ? ` (${selectedClient.contact_email})` : ""}
            </div>
          ) : searchPending ? (
            <p className="muted text-sm">Searching…</p>
          ) : searchQuery && searchResults.length === 0 ? (
            <p className="muted text-sm">No matching clients found.</p>
          ) : searchResults.length > 0 ? (
            <div style={{ maxHeight: "14rem", overflowY: "auto", border: "1px solid var(--border)", borderRadius: 6 }}>
              {searchResults.map((h) => (
                <button
                  key={h.client_id}
                  type="button"
                  className="btn btn-ghost"
                  style={{
                    display: "block",
                    width: "100%",
                    textAlign: "left",
                    padding: "0.5rem",
                    borderRadius: 0,
                    borderBottom: "1px solid var(--border)",
                  }}
                  onClick={() => {
                    setSelectedClient(h);
                    setSearchResults([]);
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{h.client_name}</div>
                  <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>
                    {h.contact_name ?? ""}
                    {h.contact_name && h.contact_email ? " — " : ""}
                    {h.contact_email ?? ""}
                  </div>
                </button>
              ))}
            </div>
          ) : null}

        </form>
      </Dialog>

      <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "1.25rem 0" }} />

      <h2 style={{ marginTop: 0 }}>Client Access</h2>

      {accessGrants.length > 0 ? (
        <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "1rem" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
              <th style={{ padding: "0.5rem 0" }}>Contact</th>
              <th>Client</th>
              <th>Role</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {accessGrants.map((a) => (
              <tr key={a.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: "0.35rem 0" }}>
                  <div style={{ fontWeight: 600 }}>{a.contact_name ?? "—"}</div>
                  <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>{a.contact_email}</div>
                </td>
                <td style={{ color: "var(--muted)", fontSize: "0.88rem" }}>{a.client_name ?? "—"}</td>
                <td><Badge variant="neutral">{a.role}</Badge></td>
                <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                  <button className="btn btn-sm btn-ghost" onClick={() => { setEditAccess(a); setEditRole(a.role); setEditViewTasks(a.can_view_tasks); setEditViewTickets(a.can_view_tickets); setEditCreateTasks(a.can_create_tasks); }}>
                    Edit
                  </button>
                  <button className="btn btn-sm btn-ghost" style={{ color: "var(--danger)" }} onClick={() => handleRevokeAccess(a.id)}>
                    Revoke
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="muted text-sm">No client access grants yet.</p>
      )}

      {linkedClients.length > 0 && (
        <button className="btn btn-sm btn-secondary" onClick={openGrantAccess}>
          Grant Access
        </button>
      )}

      <Dialog
        open={showGrantAccess}
        onClose={() => setShowGrantAccess(false)}
        title="Grant client access"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setShowGrantAccess(false)}>Cancel</button>
            <button
              type="submit"
              form="grant-access-form"
              className="btn btn-primary"
              disabled={!selectedContactId}
            >
              Grant Access
            </button>
          </>
        }
      >
        <form id="grant-access-form" onSubmit={handleGrantAccess} className="stack" style={{ gap: "0.65rem" }}>
          {contactsLoading ? (
            <p className="muted text-sm">Loading contacts…</p>
          ) : contacts.length === 0 ? (
            <p className="muted text-sm">No contacts found for linked clients.</p>
          ) : (
            <div style={{ maxHeight: "18rem", overflowY: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
                    <th style={{ padding: "0.35rem 0" }}></th>
                    <th>Name</th>
                    <th>Client</th>
                  </tr>
                </thead>
                <tbody>
                  {contacts.map((c) => {
                    const granted = alreadyHasAccess(c.id);
                    return (
                      <tr
                        key={c.id}
                        style={{
                          borderBottom: "1px solid var(--border)",
                          opacity: granted ? 0.45 : 1,
                        }}
                      >
                        <td style={{ padding: "0.35rem 0" }}>
                          <input
                            type="radio"
                            name="contact"
                            value={c.id}
                            checked={selectedContactId === c.id}
                            onChange={() => setSelectedContactId(c.id)}
                            disabled={granted}
                          />
                        </td>
                        <td>
                          <div style={{ fontWeight: 500 }}>{c.name}</div>
                          <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>{c.email}</div>
                        </td>
                        <td style={{ color: "var(--muted)", fontSize: "0.88rem" }}>
                          {c.client_name ?? "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {selectedContactId && (
            <>
              <label className="field">
                <span className="label">Role</span>
                <select
                  className="input"
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                >
                  {CLIENT_ROLES.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </label>
              <label className="row" style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                <input
                  type="checkbox"
                  checked={canCreateTasks}
                  onChange={(e) => setCanCreateTasks(e.target.checked)}
                />
                <span className="text-sm">Can create tasks</span>
              </label>
            </>
          )}

        </form>
      </Dialog>

      <Dialog
        open={editAccess !== null}
        onClose={() => setEditAccess(null)}
        title="Edit client access"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setEditAccess(null)}>Cancel</button>
            <button type="submit" form="edit-access-form" className="btn btn-primary">Save</button>
          </>
        }
      >
        <form id="edit-access-form" onSubmit={async (e) => {
          e.preventDefault();
          if (!editAccess) return;
          const r = await fetch(`/api/projects/${projectId}/client-access/${editAccess.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              role: editRole,
              can_view_tasks: editViewTasks,
              can_view_tickets: editViewTickets,
              can_create_tasks: editCreateTasks,
            }),
          });
          if (!r.ok) {
            const err = await r.json().catch(() => ({ detail: "Failed to update" }));
            toast(err.detail, "error");
            return;
          }
          toast("Access updated");
          setEditAccess(null);
          fetchData();
        }} className="stack" style={{ gap: "0.65rem" }}>
          <p className="text-sm muted" style={{ margin: 0 }}>
            Contact: <strong>{editAccess?.contact_name ?? editAccess?.contact_email ?? "—"}</strong>
            {editAccess?.client_name ? ` (${editAccess.client_name})` : ""}
          </p>
          <label className="field">
            <span className="label">Role</span>
            <select className="input" value={editRole} onChange={(e) => setEditRole(e.target.value)}>
              {CLIENT_ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </label>
          <label className="row" style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <input type="checkbox" checked={editViewTasks} onChange={(e) => setEditViewTasks(e.target.checked)} />
            <span className="text-sm">Can view tasks</span>
          </label>
          <label className="row" style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <input type="checkbox" checked={editViewTickets} onChange={(e) => setEditViewTickets(e.target.checked)} />
            <span className="text-sm">Can view tickets</span>
          </label>
          <label className="row" style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <input type="checkbox" checked={editCreateTasks} onChange={(e) => setEditCreateTasks(e.target.checked)} />
            <span className="text-sm">Can create tasks</span>
          </label>
        </form>
      </Dialog>
    </div>
  );
}
