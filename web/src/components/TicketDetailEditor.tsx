"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const TICKET_STATUSES = ["open", "in_progress", "waiting_customer", "resolved", "closed"];
const PRIORITIES = ["low", "normal", "high", "critical"];

type TicketOut = {
  id: string;
  ref: string | null;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  queue_slug: string;
  requester_email: string | null;
  created_at: string;
  updated_at: string;
};

export function TicketDetailEditor({
  ticket,
  canEdit,
}: {
  ticket: TicketOut;
  canEdit: boolean;
}) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(ticket.title);
  const [description, setDescription] = useState(ticket.description ?? "");
  const [status, setStatus] = useState(ticket.status);
  const [priority, setPriority] = useState(ticket.priority);
  const [queueSlug, setQueueSlug] = useState(ticket.queue_slug);
  const [requesterEmail, setRequesterEmail] = useState(ticket.requester_email ?? "");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  if (!editing) {
    return (
      <div className="card wide stack">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <h2 style={{ marginTop: 0, flex: 1 }}>Case</h2>
          {canEdit ? (
            <button
              type="button"
              className="btn btn-secondary text-sm"
              onClick={() => setEditing(true)}
              style={{ padding: "0.3rem 0.65rem" }}
            >
              Edit
            </button>
          ) : null}
        </div>
        <dl
          className="stack text-sm"
          style={{
            margin: 0,
            display: "grid",
            gridTemplateColumns: "auto 1fr",
            gap: "0.35rem 1rem",
            alignItems: "baseline",
          }}
        >
          <dt className="muted">Status</dt>
          <dd style={{ margin: 0 }}>
            <span className="pill">{ticket.status}</span>
          </dd>
          <dt className="muted">Priority</dt>
          <dd style={{ margin: 0 }}>{ticket.priority}</dd>
          <dt className="muted">Queue</dt>
          <dd style={{ margin: 0 }}>
            <span className="pill">{ticket.queue_slug}</span>
          </dd>
          {ticket.requester_email ? (
            <>
              <dt className="muted">Requester</dt>
              <dd style={{ margin: 0 }}>{ticket.requester_email}</dd>
            </>
          ) : null}
          <dt className="muted">Opened</dt>
          <dd suppressHydrationWarning style={{ margin: 0 }}>{new Date(ticket.created_at).toLocaleString()}</dd>
          <dt className="muted">Updated</dt>
          <dd suppressHydrationWarning style={{ margin: 0 }}>{new Date(ticket.updated_at).toLocaleString()}</dd>
        </dl>
        <div>
          <h3 className="text-sm muted" style={{ margin: "0.75rem 0 0.35rem" }}>
            Description
          </h3>
          {ticket.description ? (
            <p style={{ whiteSpace: "pre-wrap", margin: 0 }}>{ticket.description}</p>
          ) : (
            <p className="muted text-sm">No description.</p>
          )}
        </div>
      </div>
    );
  }

  async function handleSave() {
    setBusy(true);
    setMsg(null);
    const body: Record<string, unknown> = {};
    if (title.trim() !== ticket.title) body.title = title.trim();
    const descVal = description.trim() || null;
    if (descVal !== ticket.description) body.description = descVal;
    if (status !== ticket.status) body.status = status;
    if (priority !== ticket.priority) body.priority = priority;
    if (queueSlug.trim() !== ticket.queue_slug) body.queue_slug = queueSlug.trim();
    const emailVal = requesterEmail.trim() || null;
    if (emailVal !== ticket.requester_email) body.requester_email = emailVal;

    if (Object.keys(body).length === 0) {
      setEditing(false);
      setBusy(false);
      return;
    }

    const r = await fetch(`/api/tickets/${ticket.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const text = await r.text();
      try {
        const j = JSON.parse(text) as { detail?: string };
        setMsg(j.detail ?? text);
      } catch {
        setMsg(text || `Error ${r.status}`);
      }
      setBusy(false);
      return;
    }
    setEditing(false);
    setBusy(false);
    router.refresh();
  }

  function handleCancel() {
    setTitle(ticket.title);
    setDescription(ticket.description ?? "");
    setStatus(ticket.status);
    setPriority(ticket.priority);
    setQueueSlug(ticket.queue_slug);
    setRequesterEmail(ticket.requester_email ?? "");
    setMsg(null);
    setEditing(false);
  }

  return (
    <div className="card wide stack">
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <h2 style={{ marginTop: 0, flex: 1 }}>Case</h2>
      </div>
      <div className="stack" style={{ gap: "0.6rem" }}>
        <label className="field">
          <span className="label">Title</span>
          <input
            className="input"
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.6rem" }}>
          <label className="field">
            <span className="label">Status</span>
            <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
              {TICKET_STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span className="label">Priority</span>
            <select className="input" value={priority} onChange={(e) => setPriority(e.target.value)}>
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </label>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.6rem" }}>
          <label className="field">
            <span className="label">Queue</span>
            <input
              className="input"
              type="text"
              value={queueSlug}
              onChange={(e) => setQueueSlug(e.target.value)}
            />
          </label>
          <label className="field">
            <span className="label">Requester email</span>
            <input
              className="input"
              type="email"
              value={requesterEmail}
              onChange={(e) => setRequesterEmail(e.target.value)}
            />
          </label>
        </div>
        <label className="field">
          <span className="label">Description</span>
          <textarea
            className="input"
            rows={5}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <button
            type="button"
            className="btn btn-primary text-sm"
            disabled={busy || !title.trim()}
            onClick={handleSave}
          >
            {busy ? "Saving…" : "Save"}
          </button>
          <button
            type="button"
            className="btn btn-ghost text-sm"
            onClick={handleCancel}
          >
            Cancel
          </button>
        </div>
        {msg ? <p className="err text-sm">{msg}</p> : null}
      </div>
    </div>
  );
}
