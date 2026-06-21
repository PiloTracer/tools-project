"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import { Badge, stageBadgeVariant } from "@/components/Badge";
import { Dialog } from "@/components/Dialog";
import { DropdownMenu, DropdownItem } from "@/components/DropdownMenu";
import { toast } from "@/components/Toast";
import { MarkdownEditor } from "@/components/MarkdownEditor";

const PIPELINE_STAGES = [
  "target", "connected", "engaged", "call_scheduled", "call_done",
  "proposal_sent", "negotiating", "won", "lost",
];

const STAGE_LABELS: Record<string, string> = {
  target: "Target", connected: "Connected", engaged: "Engaged",
  call_scheduled: "Call scheduled", call_done: "Call done",
  proposal_sent: "Proposal sent", negotiating: "Negotiating",
  won: "Won", lost: "Lost",
};

const TERMINAL_STAGES = new Set(["won", "lost"]);

type ProspectDetail = {
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
  created_by: string;
  created_at: string;
  updated_at: string;
};

function formatCurrency(v: number | null) {
  if (v == null) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(v);
}

function formatDate(d: string | null) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

export default function ProspectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [prospect, setProspect] = useState<ProspectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDelete, setShowDelete] = useState(false);

  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editStage, setEditStage] = useState("");
  const [editValue, setEditValue] = useState("");
  const [editSource, setEditSource] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [editErr, setEditErr] = useState<string | null>(null);

  const fetchProspect = async () => {
    setLoading(true);
    try {
      const r = await fetch(`/api/prospects/${id}`);
      if (r.status === 404) { router.push("/prospects"); return; }
      if (!r.ok) throw new Error(`Failed to load (${r.status})`);
      const data = await r.json() as ProspectDetail;
      setProspect(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchProspect();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleStageTransition = async (stage: string) => {
    const r = await fetch(`/api/prospects/${id}/stage`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stage }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Transition failed" }));
      toast(err.detail, "error");
      return;
    }
    toast(prospect ? `Moved to ${STAGE_LABELS[stage] ?? stage}` : "Stage updated");
    fetchProspect();
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setEditErr(null);
    const body: Record<string, unknown> = {};
    if (editName.trim()) body.company_name = editName.trim();
    if (editStage) body.pipeline_stage = editStage;
    if (editValue) body.pipeline_value = parseFloat(editValue);
    else body.pipeline_value = null;
    if (editSource.trim()) body.source = editSource.trim();
    else body.source = null;
    if (editNotes.trim()) body.notes = editNotes.trim();
    else body.notes = null;
    const r = await fetch(`/api/prospects/${id}`, {
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
    toast("Prospect updated");
    fetchProspect();
  };

  const handleDelete = async () => {
    await fetch(`/api/prospects/${id}`, { method: "DELETE" });
    toast("Prospect deleted");
    router.push("/prospects");
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

  if (error || !prospect) {
    return (
      <div className="page-inner">
        <p className="err">{error ?? "Not found"}</p>
        <Link href="/prospects">← Prospects</Link>
      </div>
    );
  }

  const canAdvance = !TERMINAL_STAGES.has(prospect.pipeline_stage);
  const stageIdx = PIPELINE_STAGES.indexOf(prospect.pipeline_stage);
  const nextStage = canAdvance && stageIdx < PIPELINE_STAGES.length - 1 ? PIPELINE_STAGES[stageIdx + 1] : null;

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/prospects" className="muted text-sm">← Prospects</Link>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem", marginTop: "0.25rem" }}>
          <div>
            <h1 style={{ margin: "0.35rem 0 0.25rem" }}>{prospect.company_name}</h1>
            <Badge variant={stageBadgeVariant(prospect.pipeline_stage)}>
              {STAGE_LABELS[prospect.pipeline_stage] ?? prospect.pipeline_stage}
            </Badge>
          </div>
          <DropdownMenu
            trigger={
              <button type="button" aria-label="Actions" className="btn btn-secondary btn-sm">
                Actions ▾
              </button>
            }
          >
            <DropdownItem onClick={() => { setEditing(true); setEditName(prospect.company_name); setEditStage(prospect.pipeline_stage); setEditValue(prospect.pipeline_value ? String(prospect.pipeline_value) : ""); setEditSource(prospect.source ?? ""); setEditNotes(prospect.notes ?? ""); setEditErr(null); }}>
              Edit
            </DropdownItem>
            {nextStage ? (
              <DropdownItem onClick={() => handleStageTransition(nextStage)}>
                Advance to {STAGE_LABELS[nextStage]}
              </DropdownItem>
            ) : null}
            {prospect.pipeline_stage === "negotiating" ? (
              <DropdownItem onClick={() => handleStageTransition("won")}>
                Mark as won
              </DropdownItem>
            ) : null}
            {!TERMINAL_STAGES.has(prospect.pipeline_stage) ? (
              <DropdownItem onClick={() => handleStageTransition("lost")} danger>
                Mark as lost
              </DropdownItem>
            ) : null}
            <DropdownItem onClick={() => setShowDelete(true)} danger>Delete</DropdownItem>
          </DropdownMenu>
        </div>
      </div>

      <div className="card wide" style={{ maxWidth: "700px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem" }}>
          <div>
            <span className="text-sm muted" style={{ display: "block", marginBottom: "0.15rem" }}>Value</span>
            <span style={{ fontSize: "1.15rem", fontWeight: 700 }}>{formatCurrency(prospect.pipeline_value)}</span>
          </div>
          <div>
            <span className="text-sm muted" style={{ display: "block", marginBottom: "0.15rem" }}>Source</span>
            <span>{prospect.source ?? "—"}</span>
          </div>
          <div>
            <span className="text-sm muted" style={{ display: "block", marginBottom: "0.15rem" }}>First contact</span>
            <span>{formatDate(prospect.first_contact_date)}</span>
          </div>
          <div>
            <span className="text-sm muted" style={{ display: "block", marginBottom: "0.15rem" }}>Last interaction</span>
            <span>{formatDate(prospect.last_interaction)}</span>
          </div>
          <div>
            <span className="text-sm muted" style={{ display: "block", marginBottom: "0.15rem" }}>Next action</span>
            <span>{prospect.next_action ?? "—"}</span>
          </div>
          <div>
            <span className="text-sm muted" style={{ display: "block", marginBottom: "0.15rem" }}>Created</span>
            <span>{formatDate(prospect.created_at)}</span>
          </div>
        </div>
      </div>

      {prospect.notes ? (
        <div className="card" style={{ maxWidth: "700px" }}>
          <h2 style={{ marginBottom: "0.5rem" }}>Notes</h2>
          <p className="text-sm" style={{ whiteSpace: "pre-wrap", margin: 0 }}>{prospect.notes}</p>
        </div>
      ) : null}

      {canAdvance ? (
        <div className="card" style={{ maxWidth: "700px" }}>
          <h2 style={{ marginBottom: "0.5rem" }}>Pipeline progress</h2>
          <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap", alignItems: "center" }}>
            {PIPELINE_STAGES.slice(0, -2).map((s) => {
              const idx = PIPELINE_STAGES.indexOf(s);
              const cur = PIPELINE_STAGES.indexOf(prospect.pipeline_stage);
              const done = idx <= cur;
              return (
                <span
                  key={s}
                  style={{
                    padding: "0.25rem 0.5rem",
                    fontSize: "0.75rem",
                    borderRadius: "var(--radius-sm)",
                    background: done ? "rgb(56 189 248 / 15%)" : "var(--surface)",
                    color: done ? "var(--accent)" : "var(--muted)",
                    border: `1px solid ${done ? "rgb(56 189 248 / 35%)" : "var(--border)"}`,
                    fontWeight: done ? 600 : 400,
                  }}
                >
                  {STAGE_LABELS[s]}
                </span>
              );
            })}
          </div>
          {nextStage ? (
            <button className="btn btn-primary" style={{ marginTop: "0.75rem" }} onClick={() => handleStageTransition(nextStage)}>
              Advance to {STAGE_LABELS[nextStage]}
            </button>
          ) : null}
        </div>
      ) : null}

      <Dialog
        open={editing}
        onClose={() => setEditing(false)}
        title="Edit prospect"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setEditing(false)}>Cancel</button>
            <button type="submit" form="edit-form" className="btn btn-primary">Save</button>
          </>
        }
      >
        <form id="edit-form" onSubmit={handleSave} className="stack" style={{ gap: "0.65rem" }}>
          <label className="field">
            <span className="label">Company name</span>
            <input className="input" value={editName} onChange={(e) => setEditName(e.target.value)} required />
          </label>
          <label className="field">
            <span className="label">Pipeline stage</span>
            <select className="input" value={editStage} onChange={(e) => setEditStage(e.target.value)}>
              {PIPELINE_STAGES.map((s) => (
                <option key={s} value={s}>{STAGE_LABELS[s] ?? s}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span className="label">Value (USD)</span>
            <input className="input" type="number" min="0" step="0.01" value={editValue} onChange={(e) => setEditValue(e.target.value)} />
          </label>
          <label className="field">
            <span className="label">Source</span>
            <input className="input" value={editSource} onChange={(e) => setEditSource(e.target.value)} />
          </label>
          <label className="field">
            <span className="label">Notes</span>
            <MarkdownEditor value={editNotes} onChange={setEditNotes} rows={3} />
          </label>
          {editErr ? <p id="edit-form-err" className="err text-sm" role="alert">{editErr}</p> : null}
        </form>
      </Dialog>

      <Dialog
        open={showDelete}
        onClose={() => setShowDelete(false)}
        title="Delete prospect"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setShowDelete(false)}>Cancel</button>
            <button type="button" className="btn btn-primary" style={{ background: "var(--danger)", color: "var(--text)", boxShadow: "none" }} onClick={handleDelete}>Delete</button>
          </>
        }
      >
        <p className="text-sm">Are you sure you want to delete <strong>{prospect.company_name}</strong>? This action cannot be undone.</p>
      </Dialog>
    </div>
  );
}
