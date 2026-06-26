"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { CopyRefButton } from "@/components/CopyRefButton";
import { KanbanBoard } from "@/components/KanbanBoard";

import { Dialog } from "@/components/Dialog";
import { MarkdownEditor } from "@/components/MarkdownEditor";
import { usePendingImages } from "@/shared/client/use-pending-images";
import { toast } from "@/components/Toast";
import { apiRequest } from "@/shared/client/api";

export type TicketQueueRow = {
  id: string;
  ref: string | null;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  queue_slug: string;
  requester_email: string | null;
  created_at: string;
};

function ageLabel(iso: string): string {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "—";
  const diff = Date.now() - t;
  const d = Math.floor(diff / 86400000);
  if (d >= 1) return `${d}d`;
  const h = Math.floor(diff / 3600000);
  if (h >= 1) return `${h}h`;
  const m = Math.max(0, Math.floor(diff / 60000));
  return `${m}m`;
}

const TERMINAL_TICKET_STATUSES = new Set(["resolved", "closed"]);
// Plan §13 success metric: flag any ticket > 14d without movement; warn at 7d.
const STALE_DAYS_WARN = 7;
const STALE_DAYS_BAD = 14;

function ageDays(iso: string): number {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return 0;
  return Math.floor((Date.now() - t) / 86400000);
}

type Staleness = "fresh" | "warn" | "stale";

function ticketStaleness(row: TicketQueueRow): Staleness {
  if (TERMINAL_TICKET_STATUSES.has(row.status)) return "fresh";
  const d = ageDays(row.created_at);
  if (d >= STALE_DAYS_BAD) return "stale";
  if (d >= STALE_DAYS_WARN) return "warn";
  return "fresh";
}

function StaleAge({ row }: { row: TicketQueueRow }) {
  const s = ticketStaleness(row);
  const color =
    s === "stale"
      ? "var(--accent-bad, #c0392b)"
      : s === "warn"
        ? "var(--accent-warn, #c98300)"
        : undefined;
  const title =
    s === "stale"
      ? `No movement for ${ageDays(row.created_at)}d (>${STALE_DAYS_BAD}d) — escalate or update`
      : s === "warn"
        ? `Open for ${ageDays(row.created_at)}d (>${STALE_DAYS_WARN}d) — review soon`
        : "Within fresh window";
  return (
    <span
      title={title}
      style={{
        color,
        fontWeight: s === "stale" ? 600 : undefined,
        whiteSpace: "nowrap",
      }}
    >
      {ageLabel(row.created_at)}
      {s === "stale" ? " ●" : s === "warn" ? " ○" : ""}
    </span>
  );
}

function PendingThumbnails({
  pending,
  onRemove,
}: {
  pending: { key: string; url?: string; file: File }[];
  onRemove: (key: string) => void;
}) {
  if (!pending.length) return null;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "flex-start" }}>
      {pending.map((p) => (
        <div key={p.key} style={{ position: "relative" }}>
          {p.url ? (
            <>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={p.url} alt="" style={{ width: 72, height: 72, objectFit: "cover", borderRadius: 6, border: "1px solid var(--border)" }} />
            </>
          ) : (
            <div
              className="text-sm muted"
              style={{
                width: 120,
                minHeight: 72,
                padding: "0.35rem",
                borderRadius: 6,
                border: "1px solid var(--border)",
                wordBreak: "break-all",
              }}
              title={p.file.name}
            >
              {p.file.name}
            </div>
          )}
          <button
            type="button"
            className="btn btn-ghost text-sm"
            style={{ position: "absolute", top: -6, right: -6, padding: "0 0.35rem", minHeight: 0 }}
            onClick={() => onRemove(p.key)}
            aria-label="Remove attachment"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

export function NewTicketForm({
  projectId,
  canEdit,
}: {
  projectId: string;
  canEdit: boolean;
}) {
  const router = useRouter();
  const { pending, addFiles, remove, clear } = usePendingImages();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [queue, setQueue] = useState("default");
  const [requesterEmail, setRequesterEmail] = useState("");
  const [busy, setBusy] = useState(false);

  if (!canEdit) {
    return <p className="muted text-sm">Viewers cannot create tickets.</p>;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    const baseDesc = description.trim();
    const body: Record<string, unknown> = {
      title: title.trim(),
      queue_slug: queue.trim() || "default",
    };
    if (baseDesc) {
      body.description = baseDesc;
    }
    if (requesterEmail.trim()) {
      body.requester_email = requesterEmail.trim();
    }
    const r = await fetch(`/api/projects/${projectId}/tickets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const text = await r.text();
    if (!r.ok) {
      setBusy(false);
      try {
        const j = JSON.parse(text) as { detail?: string };
        toast(j.detail ?? text, "error");
      } catch {
        toast(text || `Error ${r.status}`, "error");
      }
      return;
    }
    let created: { id: string };
    try {
      created = JSON.parse(text) as { id: string };
    } catch {
      setBusy(false);
      toast("Invalid response from server", "error");
      return;
    }
    const uploadedIds: string[] = [];
    for (const p of pending) {
      const fd = new FormData();
      fd.append("file", p.file);
      const ur = await fetch(`/api/projects/${projectId}/tickets/${created.id}/attachments`, {
        method: "POST",
        body: fd,
      });
      const ut = await ur.text();
      if (!ur.ok) {
        setBusy(false);
        try {
          const j = JSON.parse(ut) as { detail?: string };
          toast(j.detail ?? ut, "error");
        } catch {
          toast(ut || `Upload failed (${ur.status})`, "error");
        }
        return;
      }
      try {
        const row = JSON.parse(ut) as { id: string };
        uploadedIds.push(row.id);
      } catch {
        setBusy(false);
        toast("Invalid upload response", "error");
        return;
      }
    }
    if (uploadedIds.length > 0) {
      const md = uploadedIds
        .map((aid, i) => {
          const f = pending[i]?.file;
          if (f?.type.startsWith("image/")) {
            return `![${f.name.replace(/]/g, "")}](/api/attachments/${aid})`;
          }
          return `[${(f?.name ?? "attachment").replace(/]/g, "")}](/api/attachments/${aid})`;
        })
        .join("\n");
      const combined = baseDesc ? `${baseDesc}\n\n${md}` : md;
      const pr = await fetch(`/api/tickets/${created.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: combined }),
      });
      if (!pr.ok) {
        const pt = await pr.text();
        setBusy(false);
        toast(pt || "Ticket created but linking images to description failed", "error");
        return;
      }
    }
    toast("Ticket created");
    setBusy(false);
    setTitle("");
    setDescription("");
    setRequesterEmail("");
    clear();
    router.refresh();
  }

  return (
    <form
      onSubmit={onSubmit}
      className="stack"
      style={{ gap: "0.65rem", maxWidth: "48rem" }}
    >
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "flex-end" }}>
        <label className="stack" style={{ flex: "2 1 220px", gap: "0.25rem" }}>
          <span className="text-sm muted">Title</span>
          <input className="input" required value={title} onChange={(e) => setTitle(e.target.value)} />
        </label>
        <label className="stack" style={{ gap: "0.25rem" }}>
          <span className="text-sm muted">Queue</span>
          <input className="input" value={queue} onChange={(e) => setQueue(e.target.value)} />
        </label>
        <label className="stack" style={{ flex: "1 1 200px", gap: "0.25rem" }}>
          <span className="text-sm muted">Requester email</span>
          <input
            className="input"
            type="email"
            value={requesterEmail}
            onChange={(e) => setRequesterEmail(e.target.value)}
            placeholder="optional (customer / reporter)"
          />
        </label>
      </div>
      <label className="stack" style={{ gap: "0.25rem" }}>
        <span className="text-sm muted">Description (issue details, repro, impact)</span>
        <MarkdownEditor
          value={description}
          onChange={setDescription}
          rows={4}
          placeholder="What is broken or requested? Steps, expected vs actual, links…"
          onPasteFiles={(files) => addFiles(files)}
          onDropFiles={(files) => addFiles(files)}
        />
      </label>
      <div className="stack" style={{ gap: "0.35rem" }}>
        <span className="text-sm muted">Attachments (images, PDF, plain text — paste, drag-and-drop, or pick)</span>
        <label className="btn btn-ghost text-sm" style={{ cursor: "pointer", display: "inline-flex", alignItems: "center", gap: "0.35rem" }}>
          <input
            type="file"
            accept="image/png,image/jpeg,image/gif,image/webp,application/pdf,text/plain,text/csv,.csv,.xls,.xlsx,.ppt,.pptx,.doc,.docx,.odt,.ods,.odp"
            multiple
            style={{ display: "none" }}
            onChange={(e) => {
              const list = e.target.files;
              if (list?.length) addFiles(Array.from(list));
              e.target.value = "";
            }}
          />
          Browse files…
        </label>
        <PendingThumbnails pending={pending} onRemove={remove} />
      </div>
      <div>
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? "Saving…" : "Open ticket"}
        </button>
      </div>
    </form>
  );
}

export function TicketTable({
  projectId,
  tickets,
  canEdit,
  canDelete,
}: {
  projectId: string;
  tickets: TicketQueueRow[];
  canEdit: boolean;
  canDelete: boolean;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [lastClickedId, setLastClickedId] = useState<string | null>(null);
  const [batchAction, setBatchAction] = useState<"status" | "priority" | null>(null);
  const [batchValue, setBatchValue] = useState("");
  const [showBatchDelete, setShowBatchDelete] = useState(false);
  const [batchBusy, setBatchBusy] = useState(false);

  async function setStatus(id: string, status: string) {
    setBusy(id);
    const r = await apiRequest(`/api/tickets/${id}/transition`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    setBusy(null);
    if (!r.ok) { toast(r.error, "error"); return; }
    router.refresh();
  }

  async function remove(id: string) {
    setBusy(id);
    const r = await apiRequest(`/api/tickets/${id}`, { method: "DELETE" });
    setBusy(null);
    if (!r.ok) { toast(r.error, "error"); return; }
    setDeleteId(null);
    setSelectedIds((prev) => { const next = new Set(prev); next.delete(id); return next; });
    router.refresh();
  }

  function toggleSelect(id: string, shiftKey: boolean) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (shiftKey && lastClickedId) {
        const idx1 = tickets.findIndex((t) => t.id === lastClickedId);
        const idx2 = tickets.findIndex((t) => t.id === id);
        if (idx1 !== -1 && idx2 !== -1) {
          const [start, end] = idx1 < idx2 ? [idx1, idx2] : [idx2, idx1];
          for (let i = start; i <= end; i++) {
            next.add(tickets[i].id);
          }
        }
      } else if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
    setLastClickedId(id);
  }

  function selectAll() {
    if (selectedIds.size === tickets.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(tickets.map((t) => t.id)));
    }
  }

  function clearSelection() {
    setSelectedIds(new Set());
    setBatchAction(null);
    setBatchValue("");
  }

  async function executeBatchStatus() {
    if (selectedIds.size === 0 || !batchValue) return;
    setBatchBusy(true);
    const r = await apiRequest(`/api/tickets/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: Array.from(selectedIds), status: batchValue }),
    });
    setBatchBusy(false);
    if (!r.ok) { toast(r.error, "error"); return; }
    toast(`Updated ${selectedIds.size} tickets`);
    clearSelection();
    router.refresh();
  }

  async function executeBatchPriority() {
    if (selectedIds.size === 0 || !batchValue) return;
    setBatchBusy(true);
    const r = await apiRequest(`/api/tickets/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: Array.from(selectedIds), priority: batchValue }),
    });
    setBatchBusy(false);
    if (!r.ok) { toast(r.error, "error"); return; }
    toast(`Updated ${selectedIds.size} tickets`);
    clearSelection();
    router.refresh();
  }

  async function executeBatchDelete() {
    if (selectedIds.size === 0) return;
    setBatchBusy(true);
    let ok = true;
    for (const id of selectedIds) {
      const r = await apiRequest(`/api/tickets/${id}`, { method: "DELETE" });
      if (!r.ok) { toast(r.error, "error"); ok = false; break; }
    }
    setBatchBusy(false);
    if (ok) {
      toast(`Deleted ${selectedIds.size} tickets`);
      setShowBatchDelete(false);
      clearSelection();
      router.refresh();
    }
  }

  return (
    <>
      {selectedIds.size > 0 ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.5rem 0.75rem",
            marginBottom: "0.5rem",
            background: "var(--surface-elevated)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-sm)",
            flexWrap: "wrap",
          }}
        >
          <span className="text-sm" style={{ fontWeight: 600, marginRight: "0.5rem" }}>
            {selectedIds.size} selected
          </span>

          <select
            className="input text-sm"
            style={{ padding: "0.25rem", minHeight: 0, maxWidth: 140 }}
            value={batchAction === "status" ? batchValue : ""}
            onChange={(e) => { setBatchAction("status"); setBatchValue(e.target.value); }}
            disabled={batchBusy}
          >
            <option value="">Set status…</option>
            <option value="open">open</option>
            <option value="in_progress">in_progress</option>
            <option value="waiting_customer">waiting_customer</option>
            <option value="resolved">resolved</option>
            <option value="closed">closed</option>
          </select>

          <select
            className="input text-sm"
            style={{ padding: "0.25rem", minHeight: 0, maxWidth: 120 }}
            value={batchAction === "priority" ? batchValue : ""}
            onChange={(e) => { setBatchAction("priority"); setBatchValue(e.target.value); }}
            disabled={batchBusy}
          >
            <option value="">Set priority…</option>
            <option value="low">low</option>
            <option value="normal">normal</option>
            <option value="high">high</option>
            <option value="critical">critical</option>
          </select>

          <button
            type="button"
            className="btn btn-sm btn-ghost"
            style={{ color: "var(--danger)" }}
            disabled={batchBusy}
            onClick={() => setShowBatchDelete(true)}
          >
            Delete {selectedIds.size}
          </button>

          <button
            type="button"
            className="btn btn-sm btn-ghost"
            onClick={clearSelection}
            disabled={batchBusy}
          >
            Clear
          </button>

          {batchAction === "status" && batchValue ? (
            <button type="button" className="btn btn-sm btn-primary" disabled={batchBusy} onClick={executeBatchStatus}>
              {batchBusy ? "…" : "Apply"}
            </button>
          ) : null}
          {batchAction === "priority" && batchValue ? (
            <button type="button" className="btn btn-sm btn-primary" disabled={batchBusy} onClick={executeBatchPriority}>
              {batchBusy ? "…" : "Apply"}
            </button>
          ) : null}
        </div>
      ) : null}

      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
            {canEdit ? (
              <th style={{ padding: "0.5rem 0", width: "2rem" }}>
                <input
                  type="checkbox"
                  checked={selectedIds.size === tickets.length && tickets.length > 0}
                  onChange={selectAll}
                  style={{ cursor: "pointer" }}
                />
              </th>
            ) : null}
            <th style={{ padding: "0.5rem 0" }}>Age</th>
            <th style={{ padding: "0.5rem 0" }}>Ref</th>
            <th style={{ padding: "0.5rem 0" }}>Title</th>
            <th>Queue</th>
            <th>Status</th>
            <th>Priority</th>
            {canEdit ? <th /> : null}
            {canDelete ? <th /> : null}
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <tr
              key={t.id}
              style={{
                borderBottom: "1px solid var(--border)",
                background: selectedIds.has(t.id) ? "var(--surface-elevated)" : undefined,
              }}
            >
              {canEdit ? (
                <td style={{ padding: "0.35rem 0" }}>
                  <input
                    type="checkbox"
                    checked={selectedIds.has(t.id)}
                    onChange={() => {}}
                    onClick={(e) => {
                      const shift = (e.nativeEvent as MouseEvent).shiftKey;
                      toggleSelect(t.id, shift);
                    }}
                    style={{ cursor: "pointer" }}
                  />
                </td>
              ) : null}
              <td className="text-sm" style={{ padding: "0.35rem 0", whiteSpace: "nowrap" }}>
                <StaleAge row={t} />
              </td>
              <td className="muted text-sm" style={{ padding: "0.35rem 0", fontFamily: "var(--font-mono, monospace)", fontSize: "0.8rem", whiteSpace: "nowrap" }}>
                {t.ref || "—"}
                {t.ref ? <CopyRefButton code={t.ref} /> : null}
              </td>
              <td style={{ padding: "0.35rem 0" }}>
                <Link href={`/projects/${projectId}/tickets/${t.id}`}>{t.title}</Link>
                {t.description ? (
                  <div className="muted text-sm" style={{ marginTop: "0.2rem", maxWidth: "36rem", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {t.description}
                  </div>
                ) : null}
              </td>
              <td><span className="pill">{t.queue_slug}</span></td>
              <td>
                {canEdit ? (
                  <select
                    className="input text-sm"
                    style={{ padding: "0.25rem", minHeight: 0 }}
                    value={t.status}
                    disabled={busy === t.id}
                    onChange={(e) => setStatus(t.id, e.target.value)}
                  >
                    <option value="open">open</option>
                    <option value="in_progress">in_progress</option>
                    <option value="waiting_customer">waiting_customer</option>
                    <option value="resolved">resolved</option>
                    <option value="closed">closed</option>
                  </select>
                ) : t.status}
              </td>
              <td>{t.priority}</td>
              {canEdit ? (
                <td>
                  <Link href={`/projects/${projectId}/tickets/${t.id}`} className="btn btn-ghost text-sm">Open</Link>
                </td>
              ) : null}
              {canDelete ? (
                <td>
                  <button type="button" className="btn btn-ghost text-sm" disabled={busy === t.id} onClick={() => setDeleteId(t.id)}>Delete</button>
                </td>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>

      <Dialog open={deleteId !== null} onClose={() => setDeleteId(null)} title="Delete ticket"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setDeleteId(null)}>Cancel</button>
            <button type="button" className="btn btn-primary" style={{ background: "var(--danger)", color: "var(--text)", boxShadow: "none" }} onClick={() => deleteId && remove(deleteId)}>Delete</button>
          </>
        }
      >
        <p className="text-sm">Delete this ticket? This action cannot be undone.</p>
      </Dialog>

      <Dialog open={showBatchDelete} onClose={() => !batchBusy && setShowBatchDelete(false)} title={`Delete ${selectedIds.size} tickets`}
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setShowBatchDelete(false)} disabled={batchBusy}>Cancel</button>
            <button type="button" className="btn btn-primary" style={{ background: "var(--danger)", color: "var(--text)", boxShadow: "none" }} disabled={batchBusy} onClick={executeBatchDelete}>Delete {selectedIds.size}</button>
          </>
        }
      >
        <p className="text-sm">Delete {selectedIds.size} selected tickets? This action cannot be undone.</p>
      </Dialog>
    </>
  );
}

export function TicketsView({
  projectId,
  tickets,
  canEdit,
  canDelete,
}: {
  projectId: string;
  tickets: TicketQueueRow[];
  canEdit: boolean;
  canDelete: boolean;
}) {
  const [view, setView] = useState<"board" | "table">("board");
  const router = useRouter();

  async function onStatusChange(ticketId: string, newStatus: string) {
    const r = await apiRequest(`/api/tickets/${ticketId}/transition`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });
    if (!r.ok) { toast(r.error, "error"); return; }
    router.refresh();
  }

  return (
    <div className="stack" style={{ gap: "0.75rem" }}>
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
        <span className="text-sm muted">View:</span>
        <button
          type="button"
          className={`btn ${view === "board" ? "btn-primary" : "btn-ghost"} text-sm`}
          onClick={() => setView("board")}
        >
          Board
        </button>
        <button
          type="button"
          className={`btn ${view === "table" ? "btn-primary" : "btn-ghost"} text-sm`}
          onClick={() => setView("table")}
        >
          Table
        </button>
      </div>
      {view === "board" ? (
        <KanbanBoard
          projectId={projectId}
          items={tickets}
          canEdit={canEdit}
          onStatusChange={onStatusChange}
          kind="ticket"
          linkPath={(t) => `/projects/${projectId}/tickets/${t.id}`}
        />
      ) : (
        <TicketTable projectId={projectId} tickets={tickets} canEdit={canEdit} canDelete={canDelete} />
      )}
    </div>
  );
}