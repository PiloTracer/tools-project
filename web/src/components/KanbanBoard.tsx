"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { CopyRefButton } from "@/components/CopyRefButton";

export type KanbanItem = {
  id: string;
  ref: string | null;
  title: string;
  status: string;
  priority: string;
  due_at?: string | null;
};

const TASK_COLUMNS = [
  { key: "todo", label: "Todo", color: "var(--muted)" },
  { key: "in_progress", label: "In Progress", color: "var(--accent)" },
  { key: "blocked", label: "Blocked", color: "var(--danger)" },
  { key: "done", label: "Done", color: "var(--success)" },
  { key: "cancelled", label: "Cancelled", color: "var(--muted)" },
];

const TICKET_COLUMNS = [
  { key: "open", label: "Open", color: "var(--muted)" },
  { key: "in_progress", label: "In Progress", color: "var(--accent)" },
  { key: "waiting_customer", label: "Waiting", color: "var(--warning, #b90)" },
  { key: "resolved", label: "Resolved", color: "var(--success)" },
  { key: "closed", label: "Closed", color: "var(--muted)" },
];

export function KanbanBoard({
  projectId,
  items,
  canEdit,
  onStatusChange,
  kind = "task",
  linkPath,
}: {
  projectId: string;
  items: KanbanItem[];
  canEdit: boolean;
  onStatusChange: (itemId: string, newStatus: string) => void;
  kind?: "task" | "ticket";
  linkPath?: (item: KanbanItem) => string;
}) {
  const [dragOverCol, setDragOverCol] = useState<string | null>(null);

  const cols = kind === "ticket" ? TICKET_COLUMNS : TASK_COLUMNS;

  const columns = useMemo(() => {
    const map: Record<string, KanbanItem[]> = {};
    for (const col of cols) {
      map[col.key] = [];
    }
    const fallback = cols[0]?.key || "todo";
    for (const t of items) {
      if (map[t.status]) {
        map[t.status].push(t);
      } else {
        map[fallback].push(t);
      }
    }
    return map;
  }, [items, cols]);

  function onDragStart(e: React.DragEvent, taskId: string) {
    e.dataTransfer.setData("text/plain", taskId);
    e.dataTransfer.effectAllowed = "move";
  }

  function onDragOver(e: React.DragEvent, colKey: string) {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDragOverCol(colKey);
  }

  function onDragLeave() {
    setDragOverCol(null);
  }

  function onDrop(e: React.DragEvent, colKey: string) {
    e.preventDefault();
    const taskId = e.dataTransfer.getData("text/plain");
    onStatusChange(taskId, colKey);
    setDragOverCol(null);
  }

  return (
    <div
      className="kanban-board"
      style={{
        display: "flex",
        gap: "0.75rem",
        overflowX: "auto",
        paddingBottom: "0.5rem",
        minHeight: 320,
      }}
    >
      {cols.map((col) => (
        <div
          key={col.key}
          className="kanban-col"
          onDragOver={(e) => canEdit && onDragOver(e, col.key)}
          onDragLeave={onDragLeave}
          onDrop={(e) => canEdit && onDrop(e, col.key)}
          style={{
            flex: "1 1 0",
            minWidth: 180,
            maxWidth: 320,
            background:
              dragOverCol === col.key
                ? "rgba(56, 189, 248, 0.08)"
                : "var(--bg-elevated, #121a2e)",
            borderRadius: "var(--radius, 10px)",
            border: `1px solid ${
              dragOverCol === col.key ? "var(--accent)" : "var(--border)"
            }`,
            padding: "0.65rem",
            transition: "background 0.15s, border-color 0.15s",
          }}
        >
          <div
            className="kanban-col-header"
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "0.5rem",
              paddingBottom: "0.35rem",
              borderBottom: "1px solid var(--border)",
            }}
          >
            <span
              className="text-sm"
              style={{ fontWeight: 600, color: col.color }}
            >
              {col.label}
            </span>
            <span className="pill pill-muted" style={{ fontSize: "0.65rem" }}>
              {(columns[col.key] || []).length}
            </span>
          </div>
          <div className="kanban-col-items stack" style={{ gap: "0.5rem" }}>
            {(columns[col.key] || []).map((t) => (
              <div
                key={t.id}
                className="card kanban-card"
                draggable={canEdit}
                onDragStart={(e) => onDragStart(e, t.id)}
                style={{
                  padding: "0.55rem 0.7rem",
                  cursor: canEdit ? "grab" : "default",
                  border: "1px solid var(--border)",
                  transition: "box-shadow 0.15s",
                }}
              >
                <div
                  className="text-sm"
                  style={{
                    fontFamily: "var(--font-mono, monospace)",
                    fontSize: "0.65rem",
                    color: "var(--muted)",
                  }}
                >
                  {t.ref || "—"}
                  {t.ref ? <CopyRefButton code={t.ref} /> : null}
                </div>
                <div
                  style={{
                    fontWeight: 500,
                    marginTop: "0.2rem",
                    wordBreak: "break-word",
                  }}
                >
                  <Link href={linkPath ? linkPath(t) : `/projects/${projectId}/tasks/${t.id}`} style={{ color: "inherit", textDecoration: "none" }}>
                    {t.title}
                  </Link>
                </div>
                <div
                  className="text-sm muted"
                  style={{
                    display: "flex",
                    gap: "0.4rem",
                    marginTop: "0.35rem",
                    flexWrap: "wrap",
                  }}
                >
                  <span className="pill" style={{ fontSize: "0.6rem" }}>
                    {t.priority}
                  </span>
                  {t.due_at ? (
                    <span style={{ fontSize: "0.65rem" }}>
                      {new Date(t.due_at).toLocaleDateString()}
                    </span>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
