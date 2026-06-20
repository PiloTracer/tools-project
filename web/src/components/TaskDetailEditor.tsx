"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { MarkdownEditor } from "@/components/MarkdownEditor";
import { AssigneePicker } from "@/components/AssigneePicker";
import { usePendingImages } from "@/shared/client/use-pending-images";

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
  members,
}: {
  task: TaskOut;
  canEdit: boolean;
  members: { user_id: string; email: string; role: string }[];
}) {
  const router = useRouter();
  const { pending, addFiles, remove, clear } = usePendingImages();
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description ?? "");
  const [status, setStatus] = useState(task.status);
  const [priority, setPriority] = useState(task.priority);
  const [assigneeId, setAssigneeId] = useState(task.assignee_id ?? "");
  const [dueAt, setDueAt] = useState(task.due_at ? task.due_at.slice(0, 16) : "");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const assigneeLabel = (uid: string | null) => {
    if (!uid) return "—";
    const m = members.find((m) => m.user_id === uid);
    return m ? m.email : `${uid.slice(0, 8)}…`;
  };

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
          <dt className="muted">Assignee</dt>
          <dd style={{ margin: 0 }}>{assigneeLabel(task.assignee_id)}</dd>
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
    try {
      let descVal = description.trim() || null;
      if (pending.length) {
        const uploadedIds: string[] = [];
        for (const p of pending) {
          const fd = new FormData();
          fd.append("file", p.file);
          const ur = await fetch(`/api/projects/${task.project_id}/tasks/${task.id}/attachments`, {
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
      if (title.trim() !== task.title) body.title = title.trim();
      if (descVal !== task.description) body.description = descVal;
      if (status !== task.status) body.status = status;
      if (priority !== task.priority) body.priority = priority;
      const newAssignee = assigneeId || null;
      if (newAssignee !== task.assignee_id) body.assignee_id = newAssignee;
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
      router.refresh();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Upload failed");
    }
    setBusy(false);
  }

  function handleCancel() {
    setTitle(task.title);
    setDescription(task.description ?? "");
    setStatus(task.status);
    setPriority(task.priority);
    setAssigneeId(task.assignee_id ?? "");
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
          <span className="label">Assignee</span>
          <AssigneePicker
            members={members}
            value={assigneeId || null}
            onChange={(uid) => setAssigneeId(uid ?? "")}
          />
        </label>
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
          <MarkdownEditor
            value={description}
            onChange={setDescription}
            rows={5}
            placeholder="Describe the task…"
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
        {msg ? <p className="err text-sm">{msg}</p> : null}
      </div>
    </div>
  );
}
