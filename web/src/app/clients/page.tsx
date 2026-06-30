"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { DataTable, type Column } from "@/components/DataTable";
import { Dialog } from "@/components/Dialog";
import { toast } from "@/components/Toast";
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

type HealthItem = {
  client_id: string;
  client_name: string;
  client_slug: string;
  project_count: number;
  task_completion_pct: number | null;
  open_ticket_count: number;
  days_since_last_activity: number | null;
  days_since_project_update: number | null;
  health_score: number | null;
  health_label: string | null;
};

function formatDate(d: string) {
  return new Date(d).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function healthColor(label: string | null): string {
  if (label === "green") return "var(--success)";
  if (label === "yellow") return "rgb(250 204 21)";
  if (label === "red") return "var(--danger)";
  return "var(--muted)";
}

export default function ClientsPage() {
  const router = useRouter();
  const [rows, setRows] = useState<ClientRow[]>([]);
  const [healthItems, setHealthItems] = useState<HealthItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [healthTab, setHealthTab] = useState(false);
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

  const fetchHealth = useCallback(async () => {
    try {
      const r = await fetch("/api/clients/health");
      if (!r.ok) return;
      const data = await r.json() as { items: HealthItem[] };
      setHealthItems(data.items ?? []);
    } catch {
      // health data is secondary
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchRows();
    fetchHealth();
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
      label: "Company",
      sortable: true,
      render: (r) => (
        <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{
            display: "inline-flex", alignItems: "center", justifyContent: "center",
            width: "1.6rem", height: "1.6rem", borderRadius: "var(--radius-sm)",
            background: "rgb(56 189 248 / 12%)", color: "var(--accent)",
            fontSize: "0.75rem", fontWeight: 700, flexShrink: 0,
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
            </svg>
          </span>
          <div>
            <div style={{ fontWeight: 600, lineHeight: 1.3 }}>{r.name}</div>
            <div style={{ fontSize: "0.72rem", color: "var(--muted)", marginTop: "0.1rem" }}>
              {r.slug}
            </div>
          </div>
        </span>
      ),
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

  const healthCounts = { green: 0, yellow: 0, red: 0, none: 0 };
  for (const h of healthItems) {
    if (h.health_label === "green") healthCounts.green++;
    else if (h.health_label === "yellow") healthCounts.yellow++;
    else if (h.health_label === "red") healthCounts.red++;
    else healthCounts.none++;
  }

  return (
    <div className="page-inner">
      <header className="page-header">
        <div className="page-header__text">
          <span className="pill">CRM</span>
          <h1>Clients</h1>
          <p className="muted page-header__lead">Company clients and organizations</p>
        </div>
        <div className="page-header__actions">
          <button className="btn btn-sm" style={{ marginRight: "0.5rem" }} onClick={() => { setHealthTab(!healthTab); if (!healthTab) fetchHealth(); }}>
            {healthTab ? "List" : "Health"}
          </button>
          <button className="btn btn-primary" onClick={() => { setFormName(""); setFormIndustry(""); setFormNotes(""); setFormErr(null); setShowCreate(true); }}>
            New client
          </button>
        </div>
      </header>

      {healthTab ? (
        <section className="page-body" aria-label="Client health dashboard">
          <div className="stat-card-row" style={{ marginBottom: "1rem" }}>
            <div className="stat-card">
              <span className="text-sm muted">Healthy</span>
              <span className="stat-value" style={{ color: "var(--success)" }}>{healthCounts.green}</span>
            </div>
            <div className="stat-card">
              <span className="text-sm muted">At risk</span>
              <span className="stat-value" style={{ color: "rgb(250 204 21)" }}>{healthCounts.yellow}</span>
            </div>
            <div className="stat-card">
              <span className="text-sm muted">Critical</span>
              <span className="stat-value" style={{ color: "var(--danger)" }}>{healthCounts.red}</span>
            </div>
            <div className="stat-card">
              <span className="text-sm muted">No projects</span>
              <span className="stat-value">{healthCounts.none}</span>
            </div>
          </div>
          {healthItems.length === 0 ? (
            <p className="muted text-sm">No health data yet.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {healthItems.map((h) => (
                <Link
                  key={h.client_id}
                  href={h.project_count > 0 ? `/clients/${h.client_id}` : "#"}
                  style={{ textDecoration: "none", color: "inherit" }}
                >
                  <div className="card" style={{ display: "flex", alignItems: "center", gap: "1rem", padding: "0.75rem 1rem", cursor: h.project_count > 0 ? "pointer" : "default" }}>
                    <div style={{
                      width: "0.6rem", height: "0.6rem", borderRadius: "50%",
                      background: healthColor(h.health_label), flexShrink: 0,
                    }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>{h.client_name}</div>
                      <div className="text-sm muted" style={{ marginTop: "0.1rem" }}>
                        {h.project_count > 0
                          ? `${h.project_count} project${h.project_count !== 1 ? "s" : ""} · ${h.task_completion_pct != null ? Math.round(h.task_completion_pct * 100) + "% tasks done" : "no tasks"} · ${h.open_ticket_count} open ticket${h.open_ticket_count !== 1 ? "s" : ""}`
                          : "No linked projects"}
                      </div>
                    </div>
                    <div style={{ textAlign: "right", flexShrink: 0 }}>
                      {h.health_score != null ? (
                        <>
                          <div style={{ fontWeight: 700, fontSize: "1.1rem", color: healthColor(h.health_label) }}>
                            {h.health_score}
                          </div>
                          <div className="text-sm muted" style={{ textTransform: "capitalize" }}>{h.health_label}</div>
                        </>
                      ) : (
                        <span className="muted text-sm">N/A</span>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      ) : (
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
      )}

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
    </div>
  );
}
