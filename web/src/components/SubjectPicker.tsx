"use client";

import { useEffect, useRef, useState } from "react";

type SubjectRow = {
  id: string;
  ref: string | null;
  title: string;
  kind: "task" | "ticket";
};

export function SubjectPicker({
  projectId,
  onSelect,
  onClose,
}: {
  projectId: string;
  onSelect: (subjectType: string, subjectId: string, label: string) => void;
  onClose: () => void;
}) {
  const [query, setQuery] = useState("");
  const [tasks, setTasks] = useState<SubjectRow[]>([]);
  const [tickets, setTickets] = useState<SubjectRow[]>([]);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    if (!query.trim()) {
      const t = setTimeout(() => { setTasks([]); setTickets([]); }, 0);
      return () => clearTimeout(t);
    }
    const timer = setTimeout(async () => {
      setBusy(true);
      try {
        const q = encodeURIComponent(query);
        const [taskRes, ticketRes] = await Promise.all([
          fetch(`/api/projects/${projectId}/tasks?q=${q}&limit=10`),
          fetch(`/api/projects/${projectId}/tickets?q=${q}&limit=10`),
        ]);
        if (taskRes.ok) {
          const d = (await taskRes.json()) as { items: SubjectRow[] };
          setTasks(d.items.map((i) => ({ ...i, kind: "task" as const })));
        }
        if (ticketRes.ok) {
          const d = (await ticketRes.json()) as { items: SubjectRow[] };
          setTickets(d.items.map((i) => ({ ...i, kind: "ticket" as const })));
        }
      } catch {
        /* ignore */
      }
      setBusy(false);
    }, 250);
    return () => clearTimeout(timer);
  }, [query, projectId]);

  const hasResults = tasks.length > 0 || tickets.length > 0;

  return (
    <div
      style={{
        border: "1px solid var(--border)",
        borderRadius: "0.4rem",
        background: "var(--surface)",
        padding: "0.5rem",
        maxWidth: "28rem",
      }}
    >
      <div style={{ display: "flex", gap: "0.4rem", alignItems: "center", marginBottom: "0.4rem" }}>
        <input
          ref={inputRef}
          className="input"
          type="text"
          placeholder="Search tasks or tickets by title or ref…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ flex: 1, fontSize: "0.85rem" }}
        />
        <button type="button" className="btn btn-ghost text-sm" onClick={onClose}>
          ✕
        </button>
      </div>
      {busy ? (
        <p className="muted text-sm">Searching…</p>
      ) : query.trim() && !hasResults ? (
        <p className="muted text-sm">No tasks or tickets found.</p>
      ) : null}
      {tasks.length > 0 ? (
        <div style={{ marginBottom: tickets.length > 0 ? "0.5rem" : 0 }}>
          <p className="muted text-sm" style={{ margin: "0 0 0.25rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Tasks
          </p>
          <ul style={{ listStyle: "none", margin: 0, padding: 0, maxHeight: "10rem", overflowY: "auto" }}>
            {tasks.map((t) => (
              <li key={t.id}>
                <button
                  type="button"
                  className="btn btn-ghost text-sm"
                  style={{ display: "block", width: "100%", textAlign: "left", padding: "0.35rem 0.4rem", borderBottom: "1px solid var(--border)" }}
                  onClick={() => onSelect("task", t.id, `${t.ref ?? "task"}: ${t.title}`)}
                >
                  <span style={{ fontWeight: 600 }}>{t.ref ?? "task"}</span>
                  <span className="muted" style={{ marginLeft: "0.4rem", fontSize: "0.8rem" }}>
                    {t.title.length > 60 ? t.title.slice(0, 60) + "…" : t.title}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {tickets.length > 0 ? (
        <div>
          <p className="muted text-sm" style={{ margin: "0 0 0.25rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Tickets
          </p>
          <ul style={{ listStyle: "none", margin: 0, padding: 0, maxHeight: "10rem", overflowY: "auto" }}>
            {tickets.map((t) => (
              <li key={t.id}>
                <button
                  type="button"
                  className="btn btn-ghost text-sm"
                  style={{ display: "block", width: "100%", textAlign: "left", padding: "0.35rem 0.4rem", borderBottom: "1px solid var(--border)" }}
                  onClick={() => onSelect("ticket", t.id, `${t.ref ?? "ticket"}: ${t.title}`)}
                >
                  <span style={{ fontWeight: 600 }}>{t.ref ?? "ticket"}</span>
                  <span className="muted" style={{ marginLeft: "0.4rem", fontSize: "0.8rem" }}>
                    {t.title.length > 60 ? t.title.slice(0, 60) + "…" : t.title}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
