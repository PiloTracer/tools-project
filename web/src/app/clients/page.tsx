"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

import { DataTable, type Column } from "@/components/DataTable";
import { Dialog } from "@/components/Dialog";
import { toast, ToastContainer } from "@/components/Toast";
import { useDownload } from "@/components/useDownload";
import { MarkdownEditor } from "@/components/MarkdownEditor";

type ClientRow = {
  id: string;
  name: string;
  slug: string;
  industry: string | null;
  notes: string | null;
  created_at: string;
};

function formatDate(d: string) {
  return new Date(d).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

export default function ClientsPage() {
  const router = useRouter();
  const [rows, setRows] = useState<ClientRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const download = useDownload();

  const [showCreate, setShowCreate] = useState(false);
  const [formName, setFormName] = useState("");
  const [formIndustry, setFormIndustry] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [formErr, setFormErr] = useState<string | null>(null);

  const fetchRows = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch("/api/clients");
      if (!r.ok) throw new Error(`Failed to load (${r.status})`);
      const data = await r.json() as { items: ClientRow[] };
      setRows(data.items ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchRows();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filtered = rows.filter((r) =>
    !search || r.name.toLowerCase().includes(search.toLowerCase()) || r.slug.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErr(null);
    const body: Record<string, string> = { name: formName.trim() };
    if (formIndustry.trim()) body.industry = formIndustry.trim();
    if (formNotes.trim()) body.notes = formNotes.trim();
    const r = await fetch("/api/clients", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Create failed" }));
      setFormErr(err.detail);
      return;
    }
    setShowCreate(false);
    setFormName(""); setFormIndustry(""); setFormNotes("");
    toast(`Created client ${formName.trim()}`);
    fetchRows();
  };

  const columns: Column<ClientRow>[] = [
    {
      key: "name",
      label: "Name",
      sortable: true,
      render: (r) => <span style={{ fontWeight: 600 }}>{r.name}</span>,
    },
    {
      key: "slug",
      label: "Slug",
      render: (r) => <span style={{ fontFamily: "ui-monospace, monospace", fontSize: "0.82rem", color: "var(--muted)" }}>{r.slug}</span>,
    },
    {
      key: "industry",
      label: "Industry",
      sortable: true,
      render: (r) => r.industry ? <span>{r.industry}</span> : <span className="muted text-sm">—</span>,
    },
    {
      key: "created_at",
      label: "Created",
      sortable: true,
      render: (r) => <span className="muted text-sm">{formatDate(r.created_at)}</span>,
    },
  ];

  return (
    <div className="page-inner">
      <header className="page-header">
        <div className="page-header__text">
          <span className="pill">CRM</span>
          <h1>Clients</h1>
          <p className="muted page-header__lead">Company clients and organizations</p>
        </div>
        <div className="page-header__actions">
          <button className="btn btn-primary" onClick={() => { setFormName(""); setFormIndustry(""); setFormNotes(""); setFormErr(null); setShowCreate(true); }}>
            New client
          </button>
        </div>
      </header>

      <section className="page-body" aria-label="Client list">
        {error ? (
          <div style={{
            padding: "0.75rem 1rem", background: "rgb(251 113 133 / 10%)", border: "1px solid rgb(251 113 133 / 30%)",
            borderRadius: "var(--radius)", marginBottom: "1rem", display: "flex", justifyContent: "space-between", alignItems: "center",
          }}>
            <span style={{ color: "var(--danger)", fontSize: "0.9rem" }}>{error}</span>
            <button className="btn btn-sm btn-secondary" onClick={() => fetchRows()}>Retry</button>
          </div>
        ) : null}

        <div className="filter-bar" style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "center", marginBottom: "1rem" }}>
          <input
            className="input"
            placeholder="Search by name or slug…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ maxWidth: "260px", fontSize: "0.88rem" }}
            aria-label="Search clients"
          />
          <button className="btn btn-sm btn-secondary" style={{ marginLeft: "auto" }} onClick={() => download("/api/reports/clients", "clients-report.xlsx")} title="Export to Excel">
            Export
          </button>
        </div>

        <DataTable
          columns={columns}
          rows={filtered}
          loading={loading}
          onRowClick={(r) => router.push(`/clients/${r.id}`)}
          emptyMessage="No clients yet."
        />
      </section>

      <Dialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="New client"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" form="client-form" className="btn btn-primary">Create</button>
          </>
        }
      >
        <form id="client-form" onSubmit={handleCreate} className="stack" style={{ gap: "0.65rem" }}>
          <label className="field">
            <span className="label">Company name *</span>
            <input className="input" value={formName} onChange={(e) => setFormName(e.target.value)} required placeholder="Acme Corp" />
          </label>
          <label className="field">
            <span className="label">Industry</span>
            <input className="input" value={formIndustry} onChange={(e) => setFormIndustry(e.target.value)} placeholder="Technology, Healthcare…" />
          </label>
          <label className="field">
            <span className="label">Notes</span>
            <MarkdownEditor value={formNotes} onChange={setFormNotes} rows={3} />
          </label>
          {formErr ? <p id="client-form-err" className="err text-sm" role="alert">{formErr}</p> : null}
        </form>
      </Dialog>
      <ToastContainer />
    </div>
  );
}
