"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { clipboardUploadableFiles, usePendingImages } from "./use-pending-images";

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
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!canEdit) {
    return <p className="muted text-sm">Viewers cannot create tickets.</p>;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
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
        setMsg(j.detail ?? text);
      } catch {
        setMsg(text || `Error ${r.status}`);
      }
      return;
    }
    let created: { id: string };
    try {
      created = JSON.parse(text) as { id: string };
    } catch {
      setBusy(false);
      setMsg("Invalid response from server");
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
          setMsg(j.detail ?? ut);
        } catch {
          setMsg(ut || `Upload failed (${ur.status})`);
        }
        return;
      }
      try {
        const row = JSON.parse(ut) as { id: string };
        uploadedIds.push(row.id);
      } catch {
        setBusy(false);
        setMsg("Invalid upload response");
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
        setMsg(pt || "Ticket created but linking images to description failed");
        return;
      }
    }
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
      onDragOver={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
      onDrop={(e) => {
        e.preventDefault();
        e.stopPropagation();
        addFiles(Array.from(e.dataTransfer.files));
      }}
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
        <textarea
          className="input"
          rows={4}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          onPaste={(e) => {
            const files = clipboardUploadableFiles(e.nativeEvent);
            if (files.length) {
              e.preventDefault();
              addFiles(files);
            }
          }}
          placeholder="What is broken or requested? Steps, expected vs actual, links…"
        />
      </label>
      <div className="stack" style={{ gap: "0.35rem" }}>
        <span className="text-sm muted">Attachments (images, PDF, plain text — paste, drag-and-drop, or pick)</span>
        <input
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp,application/pdf,text/plain"
          multiple
          className="text-sm"
          onChange={(e) => {
            const list = e.target.files;
            if (list?.length) addFiles(Array.from(list));
            e.target.value = "";
          }}
        />
        <PendingThumbnails pending={pending} onRemove={remove} />
      </div>
      <div>
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? "Saving…" : "Open ticket"}
        </button>
      </div>
      {msg ? <p className="err text-sm">{msg}</p> : null}
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

  async function setStatus(id: string, status: string) {
    setBusy(id);
    await fetch(`/api/tickets/${id}/transition`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    setBusy(null);
    router.refresh();
  }

  async function remove(id: string) {
    if (!confirm("Delete this ticket?")) return;
    setBusy(id);
    await fetch(`/api/tickets/${id}`, { method: "DELETE" });
    setBusy(null);
    router.refresh();
  }

  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
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
          <tr key={t.id} style={{ borderBottom: "1px solid var(--border)" }}>
            <td className="text-sm" style={{ padding: "0.35rem 0", whiteSpace: "nowrap" }}>
              <StaleAge row={t} />
            </td>
            <td className="muted text-sm" style={{ padding: "0.35rem 0", fontFamily: "var(--font-mono, monospace)", fontSize: "0.8rem" }}>
              {t.ref || "—"}
            </td>
            <td style={{ padding: "0.35rem 0" }}>
              <Link href={`/projects/${projectId}/tickets/${t.id}`}>{t.title}</Link>
              {t.description ? (
                <div className="muted text-sm" style={{ marginTop: "0.2rem", maxWidth: "36rem", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {t.description}
                </div>
              ) : null}
            </td>
            <td>
              <span className="pill">{t.queue_slug}</span>
            </td>
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
              ) : (
                t.status
              )}
            </td>
            <td>{t.priority}</td>
            {canEdit ? (
              <td>
                <Link href={`/projects/${projectId}/tickets/${t.id}`} className="btn btn-ghost text-sm">
                  Open
                </Link>
              </td>
            ) : null}
            {canDelete ? (
              <td>
                <button
                  type="button"
                  className="btn btn-ghost text-sm"
                  disabled={busy === t.id}
                  onClick={() => remove(t.id)}
                >
                  Delete
                </button>
              </td>
            ) : null}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
