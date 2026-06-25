"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { CopyRefButton } from "@/components/CopyRefButton";
import { KanbanBoard } from "@/components/KanbanBoard";
import { AssigneePicker } from "@/components/AssigneePicker";
import { Dialog } from "@/components/Dialog";
import { toast } from "@/components/Toast";
import { apiRequest } from "@/shared/client/api";

export type TaskRow = {
  id: string;
  ref: string | null;
  title: string;
  status: string;
  priority: string;
  assignee_id: string | null;
  due_at: string | null;
  is_todo: boolean;
};

export function NewTaskForm({
  projectId,
  canEdit,
  components,
}: {
  projectId: string;
  canEdit: boolean;
  components: { id: string; name: string }[];
}) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [status, setStatus] = useState("todo");
  const [priority, setPriority] = useState("normal");
  const [componentId, setComponentId] = useState("");
  if (!canEdit) {
    return <p className="muted text-sm">Viewers cannot create tasks.</p>;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const body: Record<string, unknown> = {
      title: title.trim(),
      status,
      priority,
      is_todo: false,
    };
    if (componentId) {
      body.component_id = componentId;
    }
    const r = await fetch(`/api/projects/${projectId}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const text = await r.text();
    if (!r.ok) {
      try {
        const j = JSON.parse(text) as { detail?: string };
        toast(j.detail ?? text, "error");
      } catch {
        toast(text || `Error ${r.status}`, "error");
      }
      return;
    }
    toast("Task created");
    setTitle("");
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="stack" style={{ gap: "0.65rem", maxWidth: "42rem" }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "flex-end" }}>
        <label className="stack" style={{ flex: "2 1 200px", gap: "0.25rem" }}>
          <span className="text-sm muted">Title</span>
          <input
            className="input"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </label>
        <label className="stack" style={{ gap: "0.25rem" }}>
          <span className="text-sm muted">Status</span>
          <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="todo">todo</option>
            <option value="in_progress">in_progress</option>
            <option value="blocked">blocked</option>
            <option value="done">done</option>
            <option value="cancelled">cancelled</option>
          </select>
        </label>
        <label className="stack" style={{ gap: "0.25rem" }}>
          <span className="text-sm muted">Priority</span>
          <select className="input" value={priority} onChange={(e) => setPriority(e.target.value)}>
            <option value="low">low</option>
            <option value="normal">normal</option>
            <option value="high">high</option>
            <option value="urgent">urgent</option>
          </select>
        </label>
        <label className="stack" style={{ gap: "0.25rem" }}>
          <span className="text-sm muted">Component</span>
          <select
            className="input"
            value={componentId}
            onChange={(e) => setComponentId(e.target.value)}
          >
            <option value="">—</option>
            {components.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="btn btn-primary">
          Add task
        </button>
      </div>
    </form>
  );
}

export function TaskTable({
  projectId,
  tasks,
  canEdit,
  members,
}: {
  projectId: string;
  tasks: TaskRow[];
  canEdit: boolean;
  members: { user_id: string; email: string; role: string }[];
}) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<"ref" | "title" | "status" | "priority" | "due_at" | "assignee_id">("title");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [lastClickedId, setLastClickedId] = useState<string | null>(null);
  const [batchAction, setBatchAction] = useState<"status" | "priority" | "assignee" | null>(null);
  const [batchValue, setBatchValue] = useState("");
  const [showBatchDelete, setShowBatchDelete] = useState(false);
  const [batchBusy, setBatchBusy] = useState(false);

  const sorted = useMemo(() => {
    const out = [...tasks];
    const mul = sortDir === "asc" ? 1 : -1;
    out.sort((a, b) => {
      if (sortKey === "due_at") {
        const da = a.due_at ? new Date(a.due_at).getTime() : 0;
        const db = b.due_at ? new Date(b.due_at).getTime() : 0;
        return (da - db) * mul;
      }
      const va = (a[sortKey] ?? "").toString().toLowerCase();
      const vb = (b[sortKey] ?? "").toString().toLowerCase();
      return va.localeCompare(vb) * mul;
    });
    return out;
  }, [tasks, sortKey, sortDir]);

  function toggleSort(key: typeof sortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  function thLabel(key: typeof sortKey, label: string) {
    const active = sortKey === key;
    const arrow = active ? (sortDir === "asc" ? " ▲" : " ▼") : "";
    return (
      <th style={{ padding: "0.5rem 0" }}>
        <button
          type="button"
          className="btn btn-ghost text-sm"
          style={{ padding: 0, fontWeight: 600, color: "var(--text)" }}
          onClick={() => toggleSort(key)}
        >
          {label}{arrow}
        </button>
      </th>
    );
  }

  async function removeTask(taskId: string) {
    setBusy(taskId);
    const r = await apiRequest(`/api/tasks/${taskId}`, { method: "DELETE" });
    setBusy(null);
    if (!r.ok) { toast(r.error, "error"); return; }
    setDeleteId(null);
    setSelectedIds((prev) => { const next = new Set(prev); next.delete(taskId); return next; });
    router.refresh();
  }

  async function setStatus(taskId: string, next: string) {
    setBusy(taskId);
    const r = await apiRequest(`/api/tasks/${taskId}/transition`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: next }),
    });
    setBusy(null);
    if (!r.ok) { toast(r.error, "error"); return; }
    router.refresh();
  }

  async function updateTask(taskId: string, patch: Record<string, unknown>) {
    setBusy(taskId);
    const r = await apiRequest(`/api/tasks/${taskId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    });
    setBusy(null);
    if (!r.ok) { toast(r.error, "error"); return; }
    router.refresh();
  }

  function memberLabel(uid: string | null) {
    if (!uid) return "—";
    const m = members.find((m) => m.user_id === uid);
    return m ? m.email : `${uid.slice(0, 8)}…`;
  }

  function toggleSelect(id: string, shiftKey: boolean) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (shiftKey && lastClickedId) {
        const idx1 = sorted.findIndex((t) => t.id === lastClickedId);
        const idx2 = sorted.findIndex((t) => t.id === id);
        if (idx1 !== -1 && idx2 !== -1) {
          const [start, end] = idx1 < idx2 ? [idx1, idx2] : [idx2, idx1];
          for (let i = start; i <= end; i++) {
            next.add(sorted[i].id);
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
    if (selectedIds.size === sorted.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(sorted.map((t) => t.id)));
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
    const r = await apiRequest(`/api/tasks/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: Array.from(selectedIds), status: batchValue }),
    });
    setBatchBusy(false);
    if (!r.ok) { toast(r.error, "error"); return; }
    toast(`Updated ${selectedIds.size} tasks`);
    clearSelection();
    router.refresh();
  }

  async function executeBatchPriority() {
    if (selectedIds.size === 0 || !batchValue) return;
    setBatchBusy(true);
    const r = await apiRequest(`/api/tasks/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: Array.from(selectedIds), priority: batchValue }),
    });
    setBatchBusy(false);
    if (!r.ok) { toast(r.error, "error"); return; }
    toast(`Updated ${selectedIds.size} tasks`);
    clearSelection();
    router.refresh();
  }

  async function executeBatchAssignee() {
    if (selectedIds.size === 0) return;
    const uid = batchValue || null;
    setBatchBusy(true);
    const r = await apiRequest(`/api/tasks/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: Array.from(selectedIds), assignee_id: uid }),
    });
    setBatchBusy(false);
    if (!r.ok) { toast(r.error, "error"); return; }
    toast(`Updated ${selectedIds.size} tasks`);
    clearSelection();
    router.refresh();
  }

  async function executeBatchDelete() {
    if (selectedIds.size === 0) return;
    setBatchBusy(true);
    let ok = true;
    for (const id of selectedIds) {
      const r = await apiRequest(`/api/tasks/${id}`, { method: "DELETE" });
      if (!r.ok) { toast(r.error, "error"); ok = false; break; }
    }
    setBatchBusy(false);
    if (ok) {
      toast(`Deleted ${selectedIds.size} tasks`);
      setShowBatchDelete(false);
      clearSelection();
      router.refresh();
    }
  }

  return (
    <div style={{ overflowX: "auto" }}>
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
            style={{ padding: "0.25rem", minHeight: 0, maxWidth: 120 }}
            value={batchAction === "status" ? batchValue : ""}
            onChange={(e) => { setBatchAction("status"); setBatchValue(e.target.value); }}
            disabled={batchBusy}
          >
            <option value="">Set status…</option>
            <option value="todo">todo</option>
            <option value="in_progress">in_progress</option>
            <option value="blocked">blocked</option>
            <option value="done">done</option>
            <option value="cancelled">cancelled</option>
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
            <option value="urgent">urgent</option>
          </select>

          <div style={{ position: "relative", display: "inline-block" }}>
            <select
              className="input text-sm"
              style={{ padding: "0.25rem", minHeight: 0, maxWidth: 140 }}
              value={batchAction === "assignee" ? batchValue : ""}
              onChange={(e) => { setBatchAction("assignee"); setBatchValue(e.target.value); }}
              disabled={batchBusy}
            >
              <option value="">Assign to…</option>
              <option value="">— Unassigned</option>
              {members.map((m) => (
                <option key={m.user_id} value={m.user_id}>{m.email}</option>
              ))}
            </select>
          </div>

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
          {batchAction === "assignee" ? (
            <button type="button" className="btn btn-sm btn-primary" disabled={batchBusy} onClick={executeBatchAssignee}>
              {batchBusy ? "…" : "Apply"}
            </button>
          ) : null}
        </div>
      ) : null}

      <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "560px" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
            {canEdit ? (
              <th style={{ padding: "0.5rem 0", width: "2rem" }}>
                <input
                  type="checkbox"
                  checked={selectedIds.size === sorted.length && sorted.length > 0}
                  onChange={selectAll}
                  style={{ cursor: "pointer" }}
                />
              </th>
            ) : null}
            {thLabel("ref", "Ref")}
            {thLabel("title", "Title")}
            {thLabel("status", "Status")}
            {thLabel("priority", "Priority")}
            {thLabel("due_at", "Due")}
            {thLabel("assignee_id", "Assignee")}
            {canEdit ? <th /> : null}
          </tr>
        </thead>
        <tbody>
          {sorted.map((t) => (
            <tr
              key={t.id}
              style={{
                borderBottom: "1px solid var(--border)",
                background: selectedIds.has(t.id) ? "var(--surface-elevated)" : undefined,
              }}
            >
              {canEdit ? (
                <td style={{ padding: "0.4rem 0" }}>
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
              <td className="muted text-sm" style={{ padding: "0.4rem 0", fontFamily: "var(--font-mono, monospace)", fontSize: "0.8rem", whiteSpace: "nowrap" }}>
                {t.ref || "—"}
                {t.ref ? <CopyRefButton ref={t.ref} /> : null}
              </td>
              <td style={{ padding: "0.4rem 0" }}>
                <Link href={`/projects/${projectId}/tasks/${t.id}`} style={{ fontWeight: 600 }}>
                  {t.title}
                </Link>
              </td>
              <td>
                {canEdit ? (
                  <select
                    className="input text-sm"
                    style={{ padding: "0.25rem 0.35rem", minHeight: 0 }}
                    value={t.status}
                    disabled={busy === t.id}
                    onChange={(e) => setStatus(t.id, e.target.value)}
                  >
                    <option value="todo">todo</option>
                    <option value="in_progress">in_progress</option>
                    <option value="blocked">blocked</option>
                    <option value="done">done</option>
                    <option value="cancelled">cancelled</option>
                  </select>
                ) : (
                  <span className="pill">{t.status}</span>
                )}
              </td>
              <td>
                {canEdit ? (
                  <select
                    className="input text-sm"
                    style={{ padding: "0.15rem 0.25rem", minHeight: 0, fontSize: "0.8rem" }}
                    value={t.priority}
                    disabled={busy === t.id}
                    onChange={(e) => updateTask(t.id, { priority: e.target.value })}
                  >
                    <option value="low">low</option>
                    <option value="normal">normal</option>
                    <option value="high">high</option>
                    <option value="urgent">urgent</option>
                  </select>
                ) : (
                  <span>{t.priority}</span>
                )}
              </td>
              <td>
                {canEdit ? (
                  <input
                    type="date"
                    className="input text-sm"
                    style={{ padding: "0.15rem 0.25rem", minHeight: 0, fontSize: "0.8rem", maxWidth: "140px" }}
                    value={t.due_at ? new Date(t.due_at).toISOString().slice(0, 10) : ""}
                    disabled={busy === t.id}
                    onChange={(e) => updateTask(t.id, { due_at: e.target.value ? new Date(e.target.value).toISOString() : null })}
                  />
                ) : (
                  <span className="muted text-sm">{t.due_at ? new Date(t.due_at).toLocaleDateString() : "—"}</span>
                )}
              </td>
              <td>
                {canEdit ? (
                  <AssigneePicker
                    members={members}
                    value={t.assignee_id}
                    onChange={(uid) => updateTask(t.id, { assignee_id: uid })}
                    disabled={busy === t.id}
                    compact
                  />
                ) : (
                  <span className="muted text-sm" title={t.assignee_id ?? ""}>{memberLabel(t.assignee_id)}</span>
                )}
              </td>
              {canEdit ? (
                <td>
                  <button
                    type="button"
                    className="btn btn-ghost text-sm"
                    disabled={busy === t.id}
                    onClick={() => setDeleteId(t.id)}
                  >
                    Delete
                  </button>
                </td>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>

      <Dialog open={deleteId !== null} onClose={() => setDeleteId(null)} title="Delete task"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setDeleteId(null)}>Cancel</button>
            <button type="button" className="btn btn-primary" style={{ background: "var(--danger)", color: "var(--text)", boxShadow: "none" }} onClick={() => deleteId && removeTask(deleteId)}>Delete</button>
          </>
        }
      >
        <p className="text-sm">Delete this task? This action cannot be undone.</p>
      </Dialog>

      <Dialog open={showBatchDelete} onClose={() => !batchBusy && setShowBatchDelete(false)} title={`Delete ${selectedIds.size} tasks`}
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setShowBatchDelete(false)} disabled={batchBusy}>Cancel</button>
            <button type="button" className="btn btn-primary" style={{ background: "var(--danger)", color: "var(--text)", boxShadow: "none" }} disabled={batchBusy} onClick={executeBatchDelete}>Delete {selectedIds.size}</button>
          </>
        }
      >
        <p className="text-sm">Delete {selectedIds.size} selected tasks? This action cannot be undone.</p>
      </Dialog>
    </div>
  );
}

export function TasksView({
  projectId,
  tasks,
  canEdit,
  members,
}: {
  projectId: string;
  tasks: TaskRow[];
  canEdit: boolean;
  members: { user_id: string; email: string; role: string }[];
}) {
  const router = useRouter();
  const [view, setView] = useState<"board" | "table">("board");

  async function onStatusChange(taskId: string, newStatus: string) {
    const r = await apiRequest(`/api/tasks/${taskId}/transition`, {
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
          tasks={tasks}
          canEdit={canEdit}
          onStatusChange={onStatusChange}
        />
      ) : (
        <TaskTable projectId={projectId} tasks={tasks} canEdit={canEdit} members={members} />
      )}
    </div>
  );
}
