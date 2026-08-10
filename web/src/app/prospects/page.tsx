"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

import { Badge, stageBadgeVariant } from "@/components/Badge";
import { DataTable, type Column } from "@/components/DataTable";
import { Dialog } from "@/components/Dialog";
import { DropdownMenu, DropdownItem } from "@/components/DropdownMenu";
import { Chip } from "@/components/Chip";
import { toast } from "@/components/Toast";
import { PipelineFunnel, type PipelineStageRow } from "@/components/PipelineFunnel";
import { useDownload } from "@/components/useDownload";
import { MarkdownEditor } from "@/components/MarkdownEditor";
import { ProspectBoard } from "@/components/ProspectBoard";
import { apiRequest, redirectToLogin } from "@/shared/client/api";

const PIPELINE_STAGES = [
  "target", "connected", "engaged", "call_scheduled", "call_done",
  "proposal_sent", "negotiating", "won", "lost",
];

const STAGE_LABELS: Record<string, string> = {
  target: "Target",
  connected: "Connected",
  engaged: "Engaged",
  call_scheduled: "Call scheduled",
  call_done: "Call done",
  proposal_sent: "Proposal sent",
  negotiating: "Negotiating",
  won: "Won",
  lost: "Lost",
};

const TERMINAL_STAGES = new Set(["won", "lost"]);

type ProspectRow = {
  id: string;
  company_name: string;
  pipeline_stage: string;
  pipeline_value: number | null;
  source: string | null;
  first_contact_date: string | null;
  last_interaction: string | null;
  next_action: string | null;
  next_action_date: string | null;
  notes: string | null;
  client_id: string | null;
  created_at: string;
};

function formatCurrency(v: number | null) {
  if (v == null) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(v);
}

function formatDate(d: string | null) {
  if (!d) return "—";
  const dt = new Date(d);
  const now = new Date();
  const diff = now.getTime() - dt.getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return dt.toLocaleDateString();
}

function getNextStage(current: string): string | null {
  const idx = PIPELINE_STAGES.indexOf(current);
  if (idx === -1 || idx >= PIPELINE_STAGES.length - 1) return null;
  return PIPELINE_STAGES[idx + 1];
}

export default function ProspectsPage() {
  const router = useRouter();
  const [rows, setRows] = useState<ProspectRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStage, setFilterStage] = useState("");
  const [filterSource, setFilterSource] = useState("");
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const [pipelineStats, setPipelineStats] = useState<PipelineStageRow[] | null>(null);
  const [pipelineTotal, setPipelineTotal] = useState(0);
  const download = useDownload();

  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState<ProspectRow | null>(null);
  const [showDelete, setShowDelete] = useState<ProspectRow | null>(null);
  const [view, setView] = useState<"board" | "table">("table");
  const [promotedResult, setPromotedResult] = useState<{ client: { id: string; name: string }; project: { id: string; name: string } } | null>(null);

  const [formName, setFormName] = useState("");
  const [formStage, setFormStage] = useState("target");
  const [formValue, setFormValue] = useState("");
  const [formSource, setFormSource] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [formErr, setFormErr] = useState<string | null>(null);

  const fetchRows = useCallback(async (opts?: { stage?: string; source?: string }) => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (opts?.stage) params.set("stage", opts.stage);
    if (opts?.source) params.set("source", opts.source);
    try {
      const r = await fetch(`/api/prospects${params.toString() ? `?${params}` : ""}`);
      if (r.status === 401) { redirectToLogin(); return; }
      if (!r.ok) throw new Error(`Failed to load (${r.status})`);
      const data = await r.json() as { items: ProspectRow[] };
      setRows(data.items ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchRows({ stage: filterStage || undefined, source: filterSource || undefined });
    fetch("/api/stats/pipeline").then(r => r.ok && r.json()).then(d => {
      if (d) {
        setPipelineStats(d.by_stage ?? []);
        setPipelineTotal(d.total_value ?? 0);
      }
    }).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterStage, filterSource]);

  const filtered = rows.filter((r) =>
    !search || r.company_name.toLowerCase().includes(search.toLowerCase())
  );

  const handlePromote = async (prospect: ProspectRow) => {
    const r = await fetch(`/api/prospects/${prospect.id}/promote`, { method: "POST" });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Promotion failed" }));
      toast(err.detail, "error");
      return;
    }
    const data = await r.json();
    setPromotedResult(data);
    fetchRows({ stage: filterStage || undefined, source: filterSource || undefined });
  };

  const handleAdvanceStage = async (prospect: ProspectRow) => {
    const next = getNextStage(prospect.pipeline_stage);
    if (!next) return;
    const r = await fetch(`/api/prospects/${prospect.id}/stage`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stage: next }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Failed to advance" }));
      toast(err.detail, "error");
      return;
    }
    toast(`Advanced ${prospect.company_name} to next stage`);
    fetchRows({ stage: filterStage || undefined, source: filterSource || undefined });
  };

  const handleBoardStageChange = async (prospectId: string, newStage: string) => {
    const r = await fetch(`/api/prospects/${prospectId}/stage`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stage: newStage }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Stage transition failed" }));
      toast(err.detail, "error");
      return;
    }
    const data = await r.json();
    const prospect = rows.find((p) => p.id === prospectId);
    if (data.promoted_client) {
      setPromotedResult({ client: data.promoted_client, project: data.promoted_project });
    } else {
      toast(`Moved ${prospect?.company_name ?? "prospect"} to ${STAGE_LABELS[newStage] ?? newStage}`);
    }
    fetchRows({ stage: filterStage || undefined, source: filterSource || undefined });
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErr(null);
    const body: Record<string, unknown> = { company_name: formName.trim(), pipeline_stage: formStage };
    if (formValue) body.pipeline_value = parseFloat(formValue);
    if (formSource.trim()) body.source = formSource.trim();
    if (formNotes.trim()) body.notes = formNotes.trim();
    const r = await fetch("/api/prospects", {
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
    resetForm();
    toast(`Created prospect ${formName.trim()}`);
    fetchRows({ stage: filterStage || undefined, source: filterSource || undefined });
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showEdit) return;
    setFormErr(null);
    const body: Record<string, unknown> = {};
    if (formName.trim()) body.company_name = formName.trim();
    if (formStage) body.pipeline_stage = formStage;
    if (formValue) body.pipeline_value = parseFloat(formValue);
    else body.pipeline_value = null;
    if (formSource.trim()) body.source = formSource.trim();
    else body.source = null;
    if (formNotes.trim()) body.notes = formNotes.trim();
    else body.notes = null;
    const r = await fetch(`/api/prospects/${showEdit.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Update failed" }));
      setFormErr(err.detail);
      return;
    }
    setShowEdit(null);
    resetForm();
    toast(`Updated prospect ${formName.trim()}`);
    fetchRows({ stage: filterStage || undefined, source: filterSource || undefined });
  };

  const handleDelete = async () => {
    if (!showDelete) return;
    const name = showDelete.company_name;
    const r = await apiRequest(`/api/prospects/${showDelete.id}`, { method: "DELETE" });
    if (!r.ok) { toast(r.error, "error"); return; }
    setShowDelete(null);
    toast(`Deleted prospect ${name}`);
    fetchRows({ stage: filterStage || undefined, source: filterSource || undefined });
  };

  const resetForm = () => {
    setFormName("");
    setFormStage("target");
    setFormValue("");
    setFormSource("");
    setFormNotes("");
    setFormErr(null);
  };

  const openEdit = (row: ProspectRow) => {
    setShowEdit(row);
    setFormName(row.company_name);
    setFormStage(row.pipeline_stage);
    setFormValue(row.pipeline_value ? String(row.pipeline_value) : "");
    setFormSource(row.source ?? "");
    setFormNotes(row.notes ?? "");
    setFormErr(null);
  };

  const columns: Column<ProspectRow>[] = [
    {
      key: "company_name",
      label: "Company",
      sortable: true,
      render: (r) => <span style={{ fontWeight: 600 }}>{r.company_name}</span>,
    },
    {
      key: "pipeline_stage",
      label: "Stage",
      sortable: true,
      render: (r) => <Badge variant={stageBadgeVariant(r.pipeline_stage)}>{STAGE_LABELS[r.pipeline_stage] ?? r.pipeline_stage}</Badge>,
    },
    {
      key: "pipeline_value",
      label: "Value",
      sortable: true,
      sortValue: (r) => r.pipeline_value,
      render: (r) => <span style={{ fontFamily: "ui-monospace, monospace", color: "var(--muted)" }}>{formatCurrency(r.pipeline_value)}</span>,
    },
    {
      key: "source",
      label: "Source",
      sortable: true,
      render: (r) => r.source ? <span className="muted text-sm">{r.source}</span> : <span className="muted text-sm">—</span>,
    },
    {
      key: "next_action",
      label: "Next action",
      sortable: true,
      render: (r) => r.next_action ? <span className="text-sm">{r.next_action}</span> : <span className="muted text-sm">—</span>,
    },
    {
      key: "last_interaction",
      label: "Last interaction",
      sortable: true,
      sortValue: (r) => r.last_interaction,
      render: (r) => <span className="muted text-sm">{formatDate(r.last_interaction)}</span>,
    },
    {
      key: "actions",
      label: "",
      style: { width: "40px", textAlign: "right" },
      render: (r) => (
        <DropdownMenu
          trigger={
            <button
              type="button"
              aria-label="Row actions"
              style={{
                background: "none",
                border: "none",
                color: "var(--muted)",
                cursor: "pointer",
                fontSize: "1.1rem",
                padding: "0.2rem 0.4rem",
                borderRadius: "var(--radius-sm)",
                fontFamily: "inherit",
              }}
            >
              ⋮
            </button>
          }
        >
          {!TERMINAL_STAGES.has(r.pipeline_stage) ? (
            <DropdownItem onClick={() => handleAdvanceStage(r)}>
              Advance to {STAGE_LABELS[getNextStage(r.pipeline_stage) ?? ""] ?? getNextStage(r.pipeline_stage)}
            </DropdownItem>
          ) : null}
          {r.pipeline_stage === "won" && !r.client_id ? (
            <DropdownItem onClick={() => handlePromote(r)}>
              Convert to client
            </DropdownItem>
          ) : TERMINAL_STAGES.has(r.pipeline_stage) ? (
            <DropdownItem disabled>Stage is terminal</DropdownItem>
          ) : null}
          <DropdownItem onClick={() => openEdit(r)}>Edit</DropdownItem>
          <DropdownItem onClick={() => { setShowDelete(r); }} danger>Delete</DropdownItem>
        </DropdownMenu>
      ),
    },
  ];

  return (
    <div className="page-inner">
      <header className="page-header">
        <div className="page-header__text">
          <span className="pill">CRM</span>
          <h1>Prospects</h1>
          <p className="muted page-header__lead">Manage your sales pipeline</p>
        </div>
        <div className="page-header__actions">
          <button className="btn btn-primary" onClick={() => { resetForm(); setShowCreate(true); }}>
            New prospect
          </button>
        </div>
      </header>

      {pipelineStats && pipelineStats.length > 0 ? (
        <div style={{ marginBottom: "1.5rem" }}>
          <div className="stat-card-row" style={{ marginBottom: "0.75rem" }}>
            <div className="stat-card">
              <span className="text-sm muted">Total pipeline value</span>
              <span className="stat-value">${pipelineTotal.toLocaleString()}</span>
            </div>
            <div className="stat-card">
              <span className="text-sm muted">Active prospects</span>
              <span className="stat-value">{pipelineStats.filter(s => s.stage !== "won" && s.stage !== "lost").reduce((a, s) => a + s.count, 0)}</span>
            </div>
            <div className="stat-card">
              <span className="text-sm muted">Won</span>
              <span className="stat-value" style={{ color: "var(--success)" }}>{pipelineStats.find(s => s.stage === "won")?.count ?? 0}</span>
            </div>
            <div className="stat-card">
              <span className="text-sm muted">Lost</span>
              <span className="stat-value" style={{ color: "var(--danger)" }}>{pipelineStats.find(s => s.stage === "lost")?.count ?? 0}</span>
            </div>
          </div>
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
            <div style={{ flex: 1, background: "var(--surface-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: "1rem" }}>
              <span className="text-sm muted" style={{ marginBottom: "0.5rem", display: "block" }}>Pipeline by stage</span>
              <PipelineFunnel data={pipelineStats} metric="count" />
            </div>
            <div style={{ flex: 1, background: "var(--surface-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: "1rem" }}>
              <span className="text-sm muted" style={{ marginBottom: "0.5rem", display: "block" }}>Pipeline value by stage</span>
              <PipelineFunnel data={pipelineStats} metric="value" />
            </div>
          </div>
        </div>
      ) : null}

      <section className="page-body" aria-label="Prospect list">
        {error ? (
          <div
            style={{
              padding: "0.75rem 1rem",
              background: "rgb(251 113 133 / 10%)",
              border: "1px solid rgb(251 113 133 / 30%)",
              borderRadius: "var(--radius)",
              marginBottom: "1rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ color: "var(--danger)", fontSize: "0.9rem" }}>{error}</span>
            <button className="btn btn-sm btn-secondary" onClick={() => fetchRows()}>Retry</button>
          </div>
        ) : null}

        <div className="filter-bar"
          style={{
            display: "flex",
            gap: "0.75rem",
            flexWrap: "wrap",
            alignItems: "center",
            marginBottom: "1rem",
          }}
        >
          <input
            className="input"
            placeholder="Search by company name…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ maxWidth: "260px", fontSize: "0.88rem" }}
            aria-label="Search prospects"
          />
          <select
            className="input"
            value={filterStage}
            onChange={(e) => setFilterStage(e.target.value)}
            aria-label="Filter by stage"
            style={{ maxWidth: "160px", fontSize: "0.88rem" }}
          >
            <option value="">All stages</option>
            {PIPELINE_STAGES.map((s) => (
              <option key={s} value={s}>{STAGE_LABELS[s] ?? s}</option>
            ))}
          </select>
          <select
            className="input"
            value={filterSource}
            onChange={(e) => setFilterSource(e.target.value)}
            aria-label="Filter by source"
            style={{ maxWidth: "160px", fontSize: "0.88rem" }}
          >
            <option value="">All sources</option>
            {Array.from(new Set(rows.map((r) => r.source).filter(Boolean))).map((s) => (
              <option key={s} value={s!}>{s}</option>
            ))}
          </select>
          {(filterStage || filterSource) ? (
            <Chip variant="accent" onRemove={() => { setFilterStage(""); setFilterSource(""); }}>
              {filterStage ? `Stage: ${STAGE_LABELS[filterStage]}` : ""}
              {filterStage && filterSource ? " · " : ""}
              {filterSource ? `Source: ${filterSource}` : ""}
            </Chip>
          ) : null}
          <button className="btn btn-sm btn-secondary" style={{ marginLeft: "auto" }} onClick={() => download("/api/reports/pipeline", "pipeline-report.xlsx")} title="Export to Excel">
            Export
          </button>
        </div>

        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem" }}>
          <button
            type="button"
            className={`btn btn-sm ${view === "board" ? "btn-primary" : "btn-ghost"}`}
            onClick={() => setView("board")}
          >
            Board
          </button>
          <button
            type="button"
            className={`btn btn-sm ${view === "table" ? "btn-primary" : "btn-ghost"}`}
            onClick={() => setView("table")}
          >
            Table
          </button>
        </div>

        {view === "board" ? (
          <ProspectBoard
            key={`board-${filtered.length}-${(filtered[0]?.id ?? "none").slice(0, 8)}`}
            prospects={filtered}
            canEdit={true}
            onStageChange={handleBoardStageChange}
          />
        ) : (
          <DataTable
            columns={columns}
            rows={filtered}
            loading={loading}
            onRowClick={(r) => router.push(`/prospects/${r.id}`)}
            emptyMessage={
              filterStage || filterSource
                ? "No prospects match these filters."
                : "No prospects yet. Create your first prospect to start tracking leads."
            }
          />
        )}
      </section>

      <Dialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="New prospect"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" form="prospect-form" className="btn btn-primary">Create</button>
          </>
        }
      >
        <ProspectForm
          formName={formName}
          formStage={formStage}
          formValue={formValue}
          formSource={formSource}
          formNotes={formNotes}
          formErr={formErr}
          onSubmit={handleCreate}
          onNameChange={setFormName}
          onStageChange={setFormStage}
          onValueChange={setFormValue}
          onSourceChange={setFormSource}
          onNotesChange={setFormNotes}
        />
      </Dialog>

      <Dialog
        open={showEdit !== null}
        onClose={() => setShowEdit(null)}
        title="Edit prospect"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setShowEdit(null)}>Cancel</button>
            <button type="submit" form="prospect-form" className="btn btn-primary">Save</button>
          </>
        }
      >
        <ProspectForm
          formName={formName}
          formStage={formStage}
          formValue={formValue}
          formSource={formSource}
          formNotes={formNotes}
          formErr={formErr}
          onSubmit={handleEdit}
          onNameChange={setFormName}
          onStageChange={setFormStage}
          onValueChange={setFormValue}
          onSourceChange={setFormSource}
          onNotesChange={setFormNotes}
        />
      </Dialog>

      <Dialog
        open={showDelete !== null}
        onClose={() => setShowDelete(null)}
        title="Delete prospect"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setShowDelete(null)}>Cancel</button>
            <button type="button" className="btn btn-primary" style={{ background: "var(--danger)", color: "var(--text)", boxShadow: "none" }} onClick={handleDelete}>
              Delete
            </button>
          </>
        }
      >
        <p className="text-sm">Are you sure you want to delete <strong>{showDelete?.company_name}</strong>? This action cannot be undone.</p>
      </Dialog>

      <Dialog
        open={promotedResult !== null}
        onClose={() => setPromotedResult(null)}
        title="Prospect converted to client"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setPromotedResult(null)}>
              Stay on prospects
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => { router.push(`/clients/${promotedResult?.client.id}`); setPromotedResult(null); }}
            >
              View client
            </button>
            {promotedResult?.project ? (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => { router.push(`/projects/${promotedResult.project.id}`); setPromotedResult(null); }}
              >
                View project
              </button>
            ) : null}
          </>
        }
      >
        <p className="text-sm">
          <strong>{promotedResult?.client.name}</strong> has been converted to a client.
        </p>
        {promotedResult?.project ? (
          <p className="text-sm muted" style={{ marginTop: "0.5rem" }}>
            An onboarding project &ldquo;{promotedResult.project.name}&rdquo; has been created with starter tasks.
          </p>
        ) : null}
      </Dialog>
    </div>
  );
}

function ProspectForm({
  formName, formStage, formValue, formSource, formNotes, formErr,
  onSubmit, onNameChange, onStageChange, onValueChange, onSourceChange, onNotesChange,
}: {
  formName: string; formStage: string; formValue: string; formSource: string; formNotes: string; formErr: string | null;
  onSubmit: (e: React.FormEvent) => void;
  onNameChange: (v: string) => void; onStageChange: (v: string) => void; onValueChange: (v: string) => void;
  onSourceChange: (v: string) => void; onNotesChange: (v: string) => void;
}) {
  return (
    <form id="prospect-form" onSubmit={onSubmit} className="stack" style={{ gap: "0.65rem" }}>
      <label className="field">
        <span className="label">Company name *</span>
        <input className="input" value={formName} onChange={(e) => onNameChange(e.target.value)} required placeholder="Acme Corp" />
      </label>
      <label className="field">
        <span className="label">Pipeline stage</span>
        <select className="input" value={formStage} onChange={(e) => onStageChange(e.target.value)}>
          {PIPELINE_STAGES.map((s) => (
            <option key={s} value={s}>{STAGE_LABELS[s] ?? s}</option>
          ))}
        </select>
      </label>
      <label className="field">
        <span className="label">Value (USD)</span>
        <input className="input" type="number" min="0" step="0.01" value={formValue} onChange={(e) => onValueChange(e.target.value)} placeholder="10000" />
      </label>
      <label className="field">
        <span className="label">Source</span>
        <input className="input" value={formSource} onChange={(e) => onSourceChange(e.target.value)} placeholder="Referral, website, cold call…" />
      </label>
      <label className="field">
        <span className="label">Notes</span>
        <MarkdownEditor value={formNotes} onChange={onNotesChange} rows={3} />
      </label>
      {formErr ? <p id="prospect-form-err" className="err text-sm" role="alert">{formErr}</p> : null}
    </form>
  );
}
