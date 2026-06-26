"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect, useCallback, useRef } from "react";

import { Badge } from "@/components/Badge";
import { Dialog } from "@/components/Dialog";
import { toast } from "@/components/Toast";
import { apiRequest } from "@/shared/client/api";

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
  const [unlinkClientId, setUnlinkClientId] = useState<string | null>(null);
  const [revokeAccessId, setRevokeAccessId] = useState<string | null>(null);

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
    const r = await apiRequest(`/api/projects/${projectId}/clients?client_id=${clientId}`, { method: "DELETE" });
    if (!r.ok) { toast(r.error, "error"); return; }
    toast("Client unlinked");
    setUnlinkClientId(null);
    fetchData();
    router.refresh();
  };

  const handleRevokeAccess = async (accessId: string) => {
    const r = await apiRequest(`/api/projects/${projectId}/client-access/${accessId}`, { method: "DELETE" });
    if (!r.ok) { toast(r.error, "error"); return; }
    toast("Access revoked");
    setRevokeAccessId(null);
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
    <><div>
      <h2 style={{ marginTop: 0, display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <span style={{
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          width: "1.3rem", height: "1.3rem", borderRadius: "var(--radius-sm)",
          background: "rgb(56 189 248 / 12%)", color: "var(--accent)", fontSize: "0.65rem",
        }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
          </svg>
        </span>
        Clients
      </h2>

      {linkedClients.length > 0 ? (
        <div className="stack" style={{ gap: "0.4rem", marginBottom: "0.75rem" }}>
          {linkedClients.map((c) => (
            <div key={c.id} style={{
              display: "flex", alignItems: "center", gap: "0.6rem",
              padding: "0.55rem 0.75rem",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              borderLeft: "3px solid rgb(56 189 248 / 50%)",
            }}>
              <span style={{
                display: "inline-flex", alignItems: "center", justifyContent: "center",
                width: "1.5rem", height: "1.5rem", borderRadius: "var(--radius-sm)",
                background: "rgb(56 189 248 / 12%)", color: "var(--accent)", flexShrink: 0, fontSize: "0.7rem",
              }}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
                </svg>
              </span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>{c.client_name}</div>
                <div style={{ fontSize: "0.72rem", color: "var(--muted)", fontFamily: "ui-monospace, monospace" }}>{c.client_slug}</div>
              </div>
              <button className="btn btn-sm btn-ghost" style={{ color: "var(--danger)", fontSize: "0.72rem", flexShrink: 0 }} onClick={() => setUnlinkClientId(c.client_id)}>
                Unlink
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted text-sm" style={{ marginBottom: "0.75rem" }}>No clients linked to this project yet.</p>
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
                    display: "flex",
                    width: "100%",
                    textAlign: "left",
                    padding: "0.5rem",
                    borderRadius: 0,
                    borderBottom: "1px solid var(--border)",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                  onClick={() => {
                    setSelectedClient(h);
                    setSearchResults([]);
                  }}
                >
                  <span style={{
                    display: "inline-flex", alignItems: "center", justifyContent: "center",
                    width: "1.4rem", height: "1.4rem", borderRadius: "var(--radius-sm)",
                    background: "rgb(56 189 248 / 12%)", color: "var(--accent)", flexShrink: 0, fontSize: "0.65rem",
                  }}>
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
                    </svg>
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: "0.85rem" }}>{h.client_name}</div>
                    <div style={{ fontSize: "0.72rem", color: "var(--muted)" }}>
                      {h.contact_name ?? ""}
                      {h.contact_name && h.contact_email ? " — " : ""}
                      {h.contact_email ?? ""}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          ) : null}

        </form>
      </Dialog>

      <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "1.25rem 0" }} />

      <h2 style={{ marginTop: 0, display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <span style={{
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          width: "1.3rem", height: "1.3rem", borderRadius: "var(--radius-sm)",
          background: "rgb(148 163 184 / 12%)", color: "var(--muted)", fontSize: "0.65rem",
        }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
        </span>
        Client Access
      </h2>

      {accessGrants.length > 0 ? (
        <div className="stack" style={{ gap: "0.4rem", marginBottom: "0.75rem" }}>
          {accessGrants.map((a) => (
            <div key={a.id} style={{
              display: "flex", alignItems: "center", gap: "0.6rem",
              padding: "0.5rem 0.75rem",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              borderLeft: "3px solid rgb(148 163 184 / 40%)",
            }}>
              <span style={{
                display: "inline-flex", alignItems: "center", justifyContent: "center",
                width: "1.6rem", height: "1.6rem", borderRadius: "50%",
                background: "rgb(148 163 184 / 10%)", color: "var(--muted)", flexShrink: 0,
                fontSize: "0.65rem", fontWeight: 700,
              }}>
                {(a.contact_name ?? "?")[0].toUpperCase()}
              </span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
                  <span style={{ fontWeight: 500, fontSize: "0.85rem" }}>{a.contact_name ?? "—"}</span>
                  <Badge variant="neutral" style={{ fontSize: "0.6rem" }}>{a.role}</Badge>
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: "0.1rem" }}>
                  {a.contact_email ?? ""}
                  {a.client_name ? <span> · {a.client_name}</span> : null}
                </div>
              </div>
              <div style={{ display: "flex", gap: "0.3rem", flexShrink: 0 }}>
                <button className="btn btn-sm btn-ghost" style={{ fontSize: "0.72rem" }} onClick={() => { setEditAccess(a); setEditRole(a.role); setEditViewTasks(a.can_view_tasks); setEditViewTickets(a.can_view_tickets); setEditCreateTasks(a.can_create_tasks); }}>
                  Edit
                </button>
                <button className="btn btn-sm btn-ghost" style={{ color: "var(--danger)", fontSize: "0.72rem" }} onClick={() => setRevokeAccessId(a.id)}>
                  Revoke
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted text-sm" style={{ marginBottom: "0.75rem" }}>No client access grants yet.</p>
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
            <div className="stack" style={{ gap: "0.3rem", maxHeight: "18rem", overflowY: "auto" }}>
              {contacts.map((c) => {
                const granted = alreadyHasAccess(c.id);
                return (
                  <label
                    key={c.id}
                    style={{
                      display: "flex", alignItems: "center", gap: "0.6rem",
                      padding: "0.45rem 0.65rem",
                      borderRadius: "var(--radius-sm)",
                      border: `1px solid ${selectedContactId === c.id ? "var(--accent)" : "var(--border)"}`,
                      background: selectedContactId === c.id ? "rgb(56 189 248 / 5%)" : "transparent",
                      opacity: granted ? 0.4 : 1,
                      cursor: granted ? "default" : "pointer",
                    }}
                  >
                    <input
                      type="radio"
                      name="contact"
                      value={c.id}
                      checked={selectedContactId === c.id}
                      onChange={() => setSelectedContactId(c.id)}
                      disabled={granted}
                      style={{ flexShrink: 0 }}
                    />
                    <span style={{
                      display: "inline-flex", alignItems: "center", justifyContent: "center",
                      width: "1.5rem", height: "1.5rem", borderRadius: "50%",
                      background: "rgb(148 163 184 / 10%)", color: "var(--muted)", flexShrink: 0,
                      fontSize: "0.6rem", fontWeight: 700,
                    }}>
                      {c.name[0].toUpperCase()}
                    </span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 500, fontSize: "0.85rem" }}>{c.name}</div>
                      <div style={{ fontSize: "0.72rem", color: "var(--muted)" }}>
                        {c.email} · {c.client_name ?? "—"}
                      </div>
                    </div>
                    {granted ? <span className="muted text-sm" style={{ fontSize: "0.7rem" }}>already granted</span> : null}
                  </label>
                );
              })}
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

    <Dialog
      open={unlinkClientId !== null}
      onClose={() => setUnlinkClientId(null)}
      title="Unlink client"
      actions={
        <>
          <button type="button" className="btn btn-ghost" onClick={() => setUnlinkClientId(null)}>Cancel</button>
          <button
            type="button"
            className="btn btn-primary"
            style={{ background: "var(--danger)", color: "var(--text)", boxShadow: "none" }}
            onClick={() => unlinkClientId && handleUnlink(unlinkClientId)}
          >
            Unlink
          </button>
        </>
      }
    >
      <p className="text-sm">Unlink this client from the project? Any related access grants will also be lost.</p>
    </Dialog>

    <Dialog
      open={revokeAccessId !== null}
      onClose={() => setRevokeAccessId(null)}
      title="Revoke access"
      actions={
        <>
          <button type="button" className="btn btn-ghost" onClick={() => setRevokeAccessId(null)}>Cancel</button>
          <button
            type="button"
            className="btn btn-primary"
            style={{ background: "var(--danger)", color: "var(--text)", boxShadow: "none" }}
            onClick={() => revokeAccessId && handleRevokeAccess(revokeAccessId)}
          >
            Revoke
          </button>
        </>
      }
    >
      <p className="text-sm">Revoke this client contact access to the project? This action cannot be undone.</p>
    </Dialog>
    </>
  );
}
