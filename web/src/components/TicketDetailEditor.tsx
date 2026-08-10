"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { MarkdownBody } from "@/components/MarkdownBody";
import { MarkdownEditor } from "@/components/MarkdownEditor";
import { usePendingImages } from "@/shared/client/use-pending-images";
import { toast } from "@/components/Toast";

const TICKET_STATUSES = ["open", "in_progress", "waiting_customer", "resolved", "closed"];
const PRIORITIES = ["low", "normal", "high", "critical"];

type TicketOut = {
  id: string;
  project_id: string;
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
  const { pending, addFiles, remove, clear } = usePendingImages();
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(ticket.title);
  const [description, setDescription] = useState(ticket.description ?? "");
  const [status, setStatus] = useState(ticket.status);
  const [priority, setPriority] = useState(ticket.priority);
  const [queueSlug, setQueueSlug] = useState(ticket.queue_slug);
  const [requesterEmail, setRequesterEmail] = useState(ticket.requester_email ?? "");
  const [busy, setBusy] = useState(false);

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
            <MarkdownBody text={ticket.description} />
          ) : (
            <p className="muted text-sm">No description.</p>
          )}
        </div>
      </div>
    );
  }

  async function handleSave() {
    setBusy(true);
    try {
      let descVal = description.trim() || null;
      if (pending.length) {
        const uploadedIds: string[] = [];
        for (const p of pending) {
          const fd = new FormData();
          fd.append("file", p.file);
          const ur = await fetch(`/api/projects/${ticket.project_id}/tickets/${ticket.id}/attachments`, {
            method: "POST",
            body: fd,
          });
          const ut = await ur.text();
          if (!ur.ok) {
            try { const j = JSON.parse(ut) as { detail?: string }; throw new Error(j.detail ?? ut); }
            catch (e) {
              if (e instanceof Error && e.message !== ut) throw e;
              throw new Error(ut || `Upload failed (${ur.status})`);
            }
          }
          const row = JSON.parse(ut) as { id: string };
          uploadedIds.push(row.id);
        }
        const mdLines = uploadedIds.map((aid, i) => {
          const f = pending[i]?.file;
          if (f?.type.startsWith("image/")) {
            return `![${f.name.replace(/]/g, "")}](/api/attachments/${aid})`;
          }
          return `[${(f?.name ?? "attachment").replace(/]/g, "")}](/api/attachments/${aid})`;
        });
        const md = mdLines.join("\n");
        descVal = descVal ? `${descVal}\n\n${md}` : md;
        clear();
      }
      const body: Record<string, unknown> = {};
      if (title.trim() !== ticket.title) body.title = title.trim();
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
          toast(j.detail ?? text, "error");
        } catch {
          toast(text || `Error ${r.status}`, "error");
        }
        setBusy(false);
        return;
      }
      setEditing(false);
      toast("Ticket saved");
      router.refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Upload failed", "error");
    }
    setBusy(false);
  }

  function handleCancel() {
    setTitle(ticket.title);
    setDescription(ticket.description ?? "");
    setStatus(ticket.status);
    setPriority(ticket.priority);
    setQueueSlug(ticket.queue_slug);
    setRequesterEmail(ticket.requester_email ?? "");
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
          <MarkdownEditor
            value={description}
            onChange={setDescription}
            rows={5}
            placeholder="Describe the issue…"
            onPasteFiles={(files) => addFiles(files)}
            onDropFiles={(files) => addFiles(files)}
          />
        </label>
        <div className="stack" style={{ gap: "0.35rem" }}>
          <span className="text-sm muted">Attachments — images, PDF, or plain text (optional)</span>
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
          {pending.length > 0 ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "flex-start" }}>
              {pending.map((p) => (
                <div key={p.key} style={{ position: "relative" }}>
                {p.url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={p.url} alt="" style={{ width: 72, height: 72, objectFit: "cover", borderRadius: 6, border: "1px solid var(--border)" }} />
                ) : (
                    <div className="text-sm muted" style={{ width: 120, minHeight: 72, padding: "0.35rem", borderRadius: 6, border: "1px solid var(--border)", wordBreak: "break-all" }} title={p.file.name}>
                      {p.file.name}
                    </div>
                  )}
                  <button type="button" className="btn btn-ghost text-sm" style={{ position: "absolute", top: -6, right: -6, padding: "0 0.35rem", minHeight: 0 }} onClick={() => remove(p.key)} aria-label="Remove attachment">×</button>
                </div>
              ))}
            </div>
          ) : null}
        </div>
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
      </div>
    </div>
  );
}
