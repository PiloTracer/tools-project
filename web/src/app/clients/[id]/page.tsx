"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import { Badge } from "@/components/Badge";
import { DataTable, type Column } from "@/components/DataTable";
import { Dialog } from "@/components/Dialog";
import { toast, ToastContainer } from "@/components/Toast";

type ClientDetail = {
  id: string;
  name: string;
  slug: string;
  industry: string | null;
  notes: string | null;
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
  const [activeTab, setActiveTab] = useState<"details" | "contacts">("details");

  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editIndustry, setEditIndustry] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [editErr, setEditErr] = useState<string | null>(null);

  const [showDelete, setShowDelete] = useState(false);

  const [showAddContact, setShowAddContact] = useState(false);
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [contactTitle, setContactTitle] = useState("");
  const [contactErr, setContactErr] = useState<string | null>(null);

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
    await fetch(`/api/clients/${id}`, { method: "DELETE" });
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
    await fetch(`/api/clients/${id}/contacts/${contactId}`, { method: "DELETE" });
    toast("Contact removed");
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

  const contactColumns: Column<ContactRow>[] = [
    {
      key: "name",
      label: "Name",
      render: (r) => (
        <span>
          {r.name}
          {r.is_primary ? <Badge variant="accent" style={{ marginLeft: "0.4rem", fontSize: "0.65rem" }}>Primary</Badge> : null}
        </span>
      ),
    },
    { key: "email", label: "Email", render: (r) => <span className="text-sm">{r.email}</span> },
    { key: "phone", label: "Phone", render: (r) => <span className="text-sm">{r.phone ?? "—"}</span> },
    { key: "title", label: "Title", render: (r) => <span className="text-sm">{r.title ?? "—"}</span> },
    { key: "role", label: "Role", render: (r) => <Badge variant="neutral">{r.role}</Badge> },
    {
      key: "actions",
      label: "",
      style: { width: "40px", textAlign: "right" },
      render: (r) => (
        <button
          type="button"
          className="btn btn-sm btn-ghost"
          onClick={() => handleDeleteContact(r.id)}
          style={{ color: "var(--danger)" }}
        >
          Remove
        </button>
      ),
    },
  ];

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/clients" className="muted text-sm">← Clients</Link>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
          <div>
            <h1 style={{ margin: "0.35rem 0 0.15rem" }}>{client.name}</h1>
            <span style={{ fontFamily: "ui-monospace, monospace", fontSize: "0.82rem", color: "var(--muted)" }}>
              {client.slug}
            </span>
            {client.industry ? <Badge variant="neutral" style={{ marginLeft: "0.5rem" }}>{client.industry}</Badge> : null}
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button className="btn btn-sm btn-secondary" onClick={() => { setEditing(true); setEditName(client.name); setEditIndustry(client.industry ?? ""); setEditNotes(client.notes ?? ""); setEditErr(null); }}>
              Edit
            </button>
            <button className="btn btn-sm btn-ghost" onClick={() => setShowDelete(true)} style={{ color: "var(--danger)" }}>Delete</button>
          </div>
        </div>
      </div>

      <div role="tablist" aria-label="Client sections" style={{ display: "flex", gap: "0.5rem", borderBottom: "1px solid var(--border)", paddingBottom: "0.5rem" }}>
        <button
          role="tab"
          id="tab-details"
          aria-selected={activeTab === "details"}
          aria-controls="panel-details"
          className={activeTab === "details" ? "btn btn-sm btn-primary" : "btn btn-sm btn-ghost"}
          onClick={() => setActiveTab("details")}
        >
          Details
        </button>
        <button
          role="tab"
          id="tab-contacts"
          aria-selected={activeTab === "contacts"}
          aria-controls="panel-contacts"
          className={activeTab === "contacts" ? "btn btn-sm btn-primary" : "btn btn-sm btn-ghost"}
          onClick={() => setActiveTab("contacts")}
        >
          Contacts ({contacts.length})
        </button>
      </div>

      {activeTab === "details" ? (
        <div role="tabpanel" id="panel-details" aria-labelledby="tab-details">
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
          </div>
          {client.notes ? (
            <div className="card" style={{ maxWidth: "700px" }}>
              <h2 style={{ marginBottom: "0.5rem" }}>Notes</h2>
              <p className="text-sm" style={{ whiteSpace: "pre-wrap", margin: 0 }}>{client.notes}</p>
            </div>
          ) : null}
        </div>
      ) : (
        <div role="tabpanel" id="panel-contacts" aria-labelledby="tab-contacts">
          <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "1rem" }}>
            <button className="btn btn-primary btn-sm" onClick={() => { setContactName(""); setContactEmail(""); setContactPhone(""); setContactTitle(""); setContactErr(null); setShowAddContact(true); }}>
              Add contact
            </button>
          </div>
          <DataTable
            columns={contactColumns}
            rows={contacts}
            emptyMessage="No contacts yet."
          />
        </div>
      )}

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
            <textarea className="input" rows={3} value={editNotes} onChange={(e) => setEditNotes(e.target.value)} />
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
      <ToastContainer />
    </div>
  );
}
