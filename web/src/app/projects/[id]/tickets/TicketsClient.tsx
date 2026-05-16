"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type TicketRow = {
  id: string;
  ref: string | null;
  title: string;
  status: string;
  priority: string;
  queue_slug: string;
};

export function NewTicketForm({
  projectId,
  canEdit,
}: {
  projectId: string;
  canEdit: boolean;
}) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [queue, setQueue] = useState("default");
  const [requesterEmail, setRequesterEmail] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  if (!canEdit) {
    return <p className="muted text-sm">Viewers cannot create tickets.</p>;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    const body: Record<string, unknown> = {
      title: title.trim(),
      queue_slug: queue.trim() || "default",
    };
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
      try {
        const j = JSON.parse(text) as { detail?: string };
        setMsg(j.detail ?? text);
      } catch {
        setMsg(text || `Error ${r.status}`);
      }
      return;
    }
    setTitle("");
    setRequesterEmail("");
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="stack" style={{ gap: "0.5rem", maxWidth: "42rem" }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "flex-end" }}>
        <label className="stack" style={{ flex: "2 1 200px", gap: "0.25rem" }}>
          <span className="text-sm muted">Title</span>
          <input className="input" required value={title} onChange={(e) => setTitle(e.target.value)} />
        </label>
        <label className="stack" style={{ gap: "0.25rem" }}>
          <span className="text-sm muted">Queue</span>
          <input className="input" value={queue} onChange={(e) => setQueue(e.target.value)} />
        </label>
        <label className="stack" style={{ flex: "1 1 180px", gap: "0.25rem" }}>
          <span className="text-sm muted">Requester email</span>
          <input className="input" type="email" value={requesterEmail} onChange={(e) => setRequesterEmail(e.target.value)} placeholder="optional" />
        </label>
        <button type="submit" className="btn btn-primary">
          Open ticket
        </button>
      </div>
      {msg ? <p className="err text-sm">{msg}</p> : null}
    </form>
  );
}

export function TicketTable({
  tickets,
  canEdit,
  canDelete,
}: {
  tickets: TicketRow[];
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
            <td className="muted text-sm" style={{ padding: "0.35rem 0", fontFamily: "var(--font-mono, monospace)", fontSize: "0.8rem" }}>
              {t.ref || "—"}
            </td>
            <td style={{ padding: "0.35rem 0" }}>{t.title}</td>
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
            {canEdit ? <td /> : null}
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
