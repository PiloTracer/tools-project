"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import { Badge } from "@/components/Badge";
import { Dialog } from "@/components/Dialog";
import { toast } from "@/components/Toast";
import { MarkdownEditor } from "@/components/MarkdownEditor";
import { apiRequest } from "@/shared/client/api";

type ClientDetail = {
  id: string;
  name: string;
  slug: string;
  industry: string | null;
  notes: string | null;
  contacts_count: number;
  created_by: string;
  created_at: string;
  updated_at: string;
};

type ContactRow = {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  title: string | null;
  role: string;
  is_primary: boolean;
  user_id: string | null;
  user_email: string | null;
  user_name: string | null;
};

type UserHit = {
  id: string;
  email: string;
  display_name: string | null;
};

function formatDate(d: string) {
  return new Date(d).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

export default function ClientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [client, setClient] = useState<ClientDetail | null>(null);
  const [contacts, setContacts] = useState<ContactRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editIndustry, setEditIndustry] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [editErr, setEditErr] = useState<string | null>(null);

  const [showDelete, setShowDelete] = useState(false);
  const [deleteContactId, setDeleteContactId] = useState<string | null>(null);

  const [showAddContact, setShowAddContact] = useState(false);
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [contactTitle, setContactTitle] = useState("");
  const [contactErr, setContactErr] = useState<string | null>(null);

  const [showLinkUser, setShowLinkUser] = useState(false);
  const [linkContactId, setLinkContactId] = useState<string | null>(null);
  const [userSearchQuery, setUserSearchQuery] = useState("");
  const [userResults, setUserResults] = useState<UserHit[]>([]);
  const [userSearchPending, setUserSearchPending] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserHit | null>(null);
  const [linkUserErr, setLinkUserErr] = useState<string | null>(null);
  const userSearchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [cr, ctr] = await Promise.all([
        fetch(`/api/clients/${id}`),
        fetch(`/api/clients/${id}/contacts`),
      ]);
      if (cr.status === 404) { router.push("/clients"); return; }
      if (!cr.ok || !ctr.ok) throw new Error("Failed to load");
      setClient(await cr.json() as ClientDetail);
      const cd = await ctr.json() as { items: ContactRow[] };
      setContacts(cd.items ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!showLinkUser) return;
    if (userSearchTimer.current) clearTimeout(userSearchTimer.current);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (!userSearchQuery.trim()) { setUserResults([]); return; }
    if (selectedUser) return;
    userSearchTimer.current = setTimeout(async () => {
      setUserSearchPending(true);
      try {
        const r = await fetch(`/api/clients/${id}/contacts/search-users?q=${encodeURIComponent(userSearchQuery)}`);
        if (r.ok) setUserResults((await r.json()) ?? []);
      } catch {
        setUserResults([]);
      } finally {
        setUserSearchPending(false);
      }
    }, 200);
    return () => {
      if (userSearchTimer.current) clearTimeout(userSearchTimer.current);
    };
  }, [userSearchQuery, showLinkUser, selectedUser, id]);

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEditErr(null);
    const body: Record<string, string> = {};
    if (editName.trim()) body.name = editName.trim();
    if (editIndustry.trim()) body.industry = editIndustry.trim();
    else body.industry = "";
    if (editNotes.trim()) body.notes = editNotes.trim();
    else body.notes = "";
    const r = await fetch(`/api/clients/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Update failed" }));
      setEditErr(err.detail);
      return;
    }
    setEditing(false);
    toast("Client updated");
    fetchData();
  };

  const handleDelete = async () => {
    const r = await apiRequest(`/api/clients/${id}`, { method: "DELETE" });
    if (!r.ok) { toast(r.error, "error"); return; }
    toast("Client deleted");
    router.push("/clients");
  };

  const handleAddContact = async (e: React.FormEvent) => {
    e.preventDefault();
    setContactErr(null);
    const body = { name: contactName.trim(), email: contactEmail.trim() };
    if (contactPhone.trim()) (body as Record<string, string>).phone = contactPhone.trim();
    if (contactTitle.trim()) (body as Record<string, string>).title = contactTitle.trim();
    const r = await fetch(`/api/clients/${id}/contacts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Failed to add contact" }));
      setContactErr(err.detail);
      return;
    }
    setShowAddContact(false);
    setContactName(""); setContactEmail(""); setContactPhone(""); setContactTitle("");
    toast(`Added contact ${contactName.trim()}`);
    fetchData();
  };

  const handleDeleteContact = async (contactId: string) => {
    const r = await apiRequest(`/api/clients/${id}/contacts/${contactId}`, { method: "DELETE" });
    if (!r.ok) { toast(r.error, "error"); return; }
    setDeleteContactId(null);
    toast("Contact removed");
    fetchData();
  };

  const openLinkUser = (contactId: string) => {
    setLinkContactId(contactId);
    setUserSearchQuery("");
    setUserResults([]);
    setSelectedUser(null);
    setLinkUserErr(null);
    setShowLinkUser(true);
  };

  const handleLinkUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!linkContactId || !selectedUser) return;
    setLinkUserErr(null);
    const r = await fetch(`/api/clients/${id}/contacts/${linkContactId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: selectedUser.id }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Failed to link user" }));
      setLinkUserErr(err.detail);
      return;
    }
    setShowLinkUser(false);
    toast(`Linked ${selectedUser.email} to contact`);
    fetchData();
  };

  const handleUnlinkUser = async (contactId: string) => {
    const r = await fetch(`/api/clients/${id}/contacts/${contactId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: null }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Failed to unlink user" }));
      toast(err.detail || "Failed to unlink");
      return;
    }
    toast("User unlinked");
    fetchData();
  };

  if (loading) {
    return (
      <div className="page-inner">
        <div className="stack" style={{ maxWidth: "600px" }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} aria-hidden style={{
              height: "1rem", borderRadius: "var(--radius-sm)",
              background: "linear-gradient(90deg, var(--surface) 25%, var(--surface-elevated) 50%, var(--surface) 75%)",
              backgroundSize: "200% 100%", animation: "skeleton-pulse 1.4s ease infinite",
            }} />
          ))}
        </div>
      </div>
    );
  }

  if (error || !client) {
    return (
      <div className="page-inner">
        <p className="err">{error ?? "Not found"}</p>
        <Link href="/clients">← Clients</Link>
      </div>
    );
  }

  return (
    <div className="page-inner stack-lg">
      {/* --- Client header (prominent company card) --- */}
      <div style={{
        background: "linear-gradient(135deg, rgb(56 189 248 / 8%), rgb(56 189 248 / 2%))",
        border: "1px solid rgb(56 189 248 / 25%)",
        borderRadius: "var(--radius)",
        padding: "1.25rem 1.5rem",
      }}>
        <Link href="/clients" className="muted text-sm" style={{ textDecoration: "none" }}>← Clients</Link>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem", marginTop: "0.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <span style={{
              display: "inline-flex", alignItems: "center", justifyContent: "center",
              width: "2.5rem", height: "2.5rem", borderRadius: "var(--radius-sm)",
              background: "rgb(56 189 248 / 15%)", color: "var(--accent)", flexShrink: 0,
            }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
              </svg>
            </span>
            <div>
              <h1 style={{ margin: 0, fontSize: "1.35rem" }}>{client.name}</h1>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.25rem" }}>
                <span style={{ fontFamily: "ui-monospace, monospace", fontSize: "0.8rem", color: "var(--muted)" }}>
                  {client.slug}
                </span>
                {client.industry ? <Badge variant="neutral">{client.industry}</Badge> : null}
                <Badge variant="accent">client</Badge>
              </div>
            </div>
          </div>
          <div style={{ display: "flex", gap: "0.5rem", flexShrink: 0 }}>
            <button className="btn btn-sm btn-secondary" onClick={() => { setEditing(true); setEditName(client.name); setEditIndustry(client.industry ?? ""); setEditNotes(client.notes ?? ""); setEditErr(null); }}>
              Edit
            </button>
            <button className="btn btn-sm btn-ghost" onClick={() => setShowDelete(true)} style={{ color: "var(--danger)" }}>Delete</button>
          </div>
        </div>
      </div>

      {/* --- Client metadata card --- */}
      <div className="card" style={{ maxWidth: "700px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem" }}>
          <div>
            <span className="text-sm muted" style={{ display: "block", marginBottom: "0.15rem" }}>Industry</span>
            <span>{client.industry ?? "—"}</span>
          </div>
          <div>
            <span className="text-sm muted" style={{ display: "block", marginBottom: "0.15rem" }}>Created</span>
            <span>{formatDate(client.created_at)}</span>
          </div>
        </div>
        {client.notes ? (
          <div style={{ marginTop: "1rem", borderTop: "1px solid var(--border)", paddingTop: "1rem" }}>
            <span className="text-sm muted" style={{ display: "block", marginBottom: "0.35rem" }}>Notes</span>
            <p className="text-sm" style={{ whiteSpace: "pre-wrap", margin: 0 }}>{client.notes}</p>
          </div>
        ) : null}
      </div>

      {/* --- Contacts section (sub-component) --- */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <h2 style={{ margin: 0, fontSize: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{
              display: "inline-flex", alignItems: "center", justifyContent: "center",
              width: "1.3rem", height: "1.3rem", borderRadius: "var(--radius-sm)",
              background: "rgb(148 163 184 / 12%)", color: "var(--muted)", fontSize: "0.65rem",
            }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </span>
            Contacts
            <span className="muted text-sm" style={{ fontWeight: 400 }}>({contacts.length})</span>
          </h2>
          <button className="btn btn-primary btn-sm" onClick={() => { setContactName(""); setContactEmail(""); setContactPhone(""); setContactTitle(""); setContactErr(null); setShowAddContact(true); }}>
            Add contact
          </button>
        </div>

        {contacts.length === 0 ? (
          <p className="muted text-sm" style={{ padding: "0.75rem 0" }}>No contacts yet. Add a contact to this client.</p>
        ) : (
          <div className="stack" style={{ gap: "0.5rem" }}>
            {contacts.map((c) => (
              <div key={c.id} style={{
                display: "flex", alignItems: "center", gap: "0.75rem",
                padding: "0.75rem 1rem",
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-sm)",
                borderLeft: "3px solid rgb(148 163 184 / 40%)",
              }}>
                {/* Person avatar */}
                <span style={{
                  display: "inline-flex", alignItems: "center", justifyContent: "center",
                  width: "1.8rem", height: "1.8rem", borderRadius: "50%",
                  background: "rgb(148 163 184 / 10%)", color: "var(--muted)", flexShrink: 0,
                  fontSize: "0.75rem", fontWeight: 700,
                }}>
                  {c.name.charAt(0).toUpperCase()}
                </span>

                {/* Contact info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
                    <span style={{ fontWeight: 500, fontSize: "0.9rem" }}>{c.name}</span>
                    {c.is_primary ? <Badge variant="accent" style={{ fontSize: "0.6rem" }}>Primary</Badge> : null}
                    {c.role !== "contact" ? <Badge variant="neutral" style={{ fontSize: "0.6rem" }}>{c.role}</Badge> : null}
                    {c.title ? <span className="muted text-sm">· {c.title}</span> : null}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginTop: "0.15rem", flexWrap: "wrap" }}>
                    <span className="text-sm" style={{ color: "var(--muted)" }}>{c.email}</span>
                    {c.phone ? <span className="text-sm" style={{ color: "var(--muted)" }}>· {c.phone}</span> : null}
                    {c.user_id ? (
                      <Badge variant="success" style={{ fontSize: "0.6rem" }}>
                        linked {c.user_name ?? c.user_email ?? ""}
                      </Badge>
                    ) : null}
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: "flex", gap: "0.3rem", flexShrink: 0 }}>
                  {c.user_id ? (
                    <button type="button" className="btn btn-sm btn-ghost" onClick={() => handleUnlinkUser(c.id)} style={{ color: "var(--danger)", fontSize: "0.72rem" }}>
                      Unlink
                    </button>
                  ) : (
                    <button type="button" className="btn btn-sm btn-secondary" onClick={() => openLinkUser(c.id)} style={{ fontSize: "0.72rem" }}>
                      Link User
                    </button>
                  )}
                  <button type="button" className="btn btn-sm btn-ghost" onClick={() => setDeleteContactId(c.id)} style={{ color: "var(--danger)", fontSize: "0.72rem" }}>
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div> 

      <Dialog
        open={editing}
        onClose={() => setEditing(false)}
        title="Edit client"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setEditing(false)}>Cancel</button>
            <button type="submit" form="edit-client-form" className="btn btn-primary">Save</button>
          </>
        }
      >
        <form id="edit-client-form" onSubmit={handleEdit} className="stack" style={{ gap: "0.65rem" }}>
          <label className="field">
            <span className="label">Company name</span>
            <input className="input" value={editName} onChange={(e) => setEditName(e.target.value)} required />
          </label>
          <label className="field">
            <span className="label">Industry</span>
            <input className="input" value={editIndustry} onChange={(e) => setEditIndustry(e.target.value)} />
          </label>
          <label className="field">
            <span className="label">Notes</span>
            <MarkdownEditor value={editNotes} onChange={setEditNotes} rows={3} />
          </label>
          {editErr ? <p id="edit-client-form-err" className="err text-sm" role="alert">{editErr}</p> : null}
        </form>
      </Dialog>

      <Dialog
        open={showDelete}
        onClose={() => setShowDelete(false)}
        title="Delete client"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setShowDelete(false)}>Cancel</button>
            <button type="button" className="btn btn-primary" style={{ background: "var(--danger)", color: "var(--text)", boxShadow: "none" }} onClick={handleDelete}>Delete</button>
          </>
        }
      >
        <p className="text-sm">Are you sure you want to delete <strong>{client.name}</strong>? This action cannot be undone.</p>
      </Dialog>

      <Dialog
        open={showAddContact}
        onClose={() => setShowAddContact(false)}
        title="Add contact"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setShowAddContact(false)}>Cancel</button>
            <button type="submit" form="contact-form" className="btn btn-primary">Add</button>
          </>
        }
      >
        <form id="contact-form" onSubmit={handleAddContact} className="stack" style={{ gap: "0.65rem" }}>
          <label className="field">
            <span className="label">Name *</span>
            <input className="input" value={contactName} onChange={(e) => setContactName(e.target.value)} required />
          </label>
          <label className="field">
            <span className="label">Email *</span>
            <input className="input" type="email" value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} required />
          </label>
          <label className="field">
            <span className="label">Phone</span>
            <input className="input" value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} />
          </label>
          <label className="field">
            <span className="label">Title / role</span>
            <input className="input" value={contactTitle} onChange={(e) => setContactTitle(e.target.value)} />
          </label>
          {contactErr ? <p id="contact-form-err" className="err text-sm" role="alert">{contactErr}</p> : null}
        </form>
      </Dialog>

      <Dialog
        open={showLinkUser}
        onClose={() => setShowLinkUser(false)}
        title="Link user to contact"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setShowLinkUser(false)}>Cancel</button>
            <button
              type="submit"
              form="link-user-form"
              className="btn btn-primary"
              disabled={!selectedUser}
            >
              Link
            </button>
          </>
        }
      >
        <form id="link-user-form" onSubmit={handleLinkUser} className="stack" style={{ gap: "0.65rem" }}>
          <label className="field">
            <span className="label">Search by email or name</span>
            <input
              className="input"
              value={selectedUser ? `${selectedUser.email}${selectedUser.display_name ? ` (${selectedUser.display_name})` : ""}` : userSearchQuery}
              onChange={(e) => {
                setSelectedUser(null);
                setUserSearchQuery(e.target.value);
              }}
              placeholder="Type to search for a user…"
              autoFocus
              autoComplete="off"
            />
          </label>

          {selectedUser ? (
            <div style={{ padding: "0.35rem 0", color: "var(--muted)", fontSize: "0.85rem" }}>
              Selected: <strong>{selectedUser.email}</strong>
              {selectedUser.display_name ? ` (${selectedUser.display_name})` : ""}
            </div>
          ) : userSearchPending ? (
            <p className="muted text-sm">Searching…</p>
          ) : userSearchQuery && userResults.length === 0 ? (
            <p className="muted text-sm">No matching users found.</p>
          ) : userResults.length > 0 ? (
            <div style={{ maxHeight: "14rem", overflowY: "auto", border: "1px solid var(--border)", borderRadius: 6 }}>
              {userResults.map((u) => (
                <button
                  key={u.id}
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
                    setSelectedUser(u);
                    setUserResults([]);
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{u.email}</div>
                  {u.display_name ? (
                    <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>{u.display_name}</div>
                  ) : null}
                </button>
              ))}
            </div>
          ) : null}

          {linkUserErr ? <p className="err text-sm">{linkUserErr}</p> : null}
        </form>
      </Dialog>

      <Dialog
        open={deleteContactId !== null}
        onClose={() => setDeleteContactId(null)}
        title="Remove contact"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setDeleteContactId(null)}>Cancel</button>
            <button
              type="button"
              className="btn btn-primary"
              style={{ background: "var(--danger)", color: "var(--text)", boxShadow: "none" }}
              onClick={() => deleteContactId && handleDeleteContact(deleteContactId)}
            >
              Remove
            </button>
          </>
        }
      >
        <p className="text-sm">Remove this contact? This action cannot be undone.</p>
      </Dialog>

    </div>
  );
}
