"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const TASK_STATUSES = ["todo", "in_progress", "blocked", "done", "cancelled"];
const PRIORITIES = ["low", "normal", "high", "critical"];

type TaskOut = {
  id: string;
  project_id: string;
  ref: string | null;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  assignee_id: string | null;
  due_at: string | null;
  created_at: string;
  updated_at: string;
};

export function TaskDetailEditor({
  task,
  canEdit,
}: {
  task: TaskOut;
  canEdit: boolean;
}) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description ?? "");
  const [status, setStatus] = useState(task.status);
  const [priority, setPriority] = useState(task.priority);
  const [dueAt, setDueAt] = useState(task.due_at ? task.due_at.slice(0, 16) : "");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  if (!editing) {
    return (
      <div className="card wide stack">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <h2 style={{ marginTop: 0, flex: 1 }}>Details</h2>
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
            <span className="pill">{task.status}</span>
          </dd>
          <dt className="muted">Priority</dt>
          <dd style={{ margin: 0 }}>{task.priority}</dd>
          {task.due_at ? (
            <>
              <dt className="muted">Due</dt>
              <dd suppressHydrationWarning style={{ margin: 0 }}>{new Date(task.due_at).toLocaleString()}</dd>
            </>
          ) : null}
          <dt className="muted">Created</dt>
          <dd suppressHydrationWarning style={{ margin: 0 }}>{new Date(task.created_at).toLocaleString()}</dd>
          <dt className="muted">Updated</dt>
          <dd suppressHydrationWarning style={{ margin: 0 }}>{new Date(task.updated_at).toLocaleString()}</dd>
        </dl>
        <div>
          <h3 className="text-sm muted" style={{ margin: "0.75rem 0 0.35rem" }}>
            Description
          </h3>
          {task.description ? (
            <p style={{ whiteSpace: "pre-wrap", margin: 0 }}>{task.description}</p>
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
    if (title.trim() !== task.title) body.title = title.trim();
    const descVal = description.trim() || null;
    if (descVal !== task.description) body.description = descVal;
    if (status !== task.status) body.status = status;
    if (priority !== task.priority) body.priority = priority;
    const dueVal = dueAt ? new Date(dueAt).toISOString() : null;
    if (dueVal !== task.due_at) body.due_at = dueVal;

    if (Object.keys(body).length === 0) {
      setEditing(false);
      setBusy(false);
      return;
    }

    const r = await fetch(`/api/tasks/${task.id}`, {
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
    setTitle(task.title);
    setDescription(task.description ?? "");
    setStatus(task.status);
    setPriority(task.priority);
    setDueAt(task.due_at ? task.due_at.slice(0, 16) : "");
    setMsg(null);
    setEditing(false);
  }

  return (
    <div className="card wide stack">
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <h2 style={{ marginTop: 0, flex: 1 }}>Details</h2>
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
              {TASK_STATUSES.map((s) => (
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
        <label className="field">
          <span className="label">Due date</span>
          <input
            className="input"
            type="datetime-local"
            value={dueAt}
            onChange={(e) => setDueAt(e.target.value)}
          />
        </label>
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
