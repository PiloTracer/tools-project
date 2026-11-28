"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Item = {
  id: string;
  title: string;
  status: string;
  due_at: string | null;
  project_id: string;
  project_name: string;
  recurrence: string | null;
};

type SavedView = { label: string; query: string };

export default function CalendarPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [views, setViews] = useState<Record<string, SavedView>>({});
  const [name, setName] = useState("");
  const [filter, setFilter] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      const [cal, me] = await Promise.all([fetch("/api/planning/calendar"), fetch("/api/auth/me")]);
      if (!cal.ok) {
        setError("Could not load the calendar");
        return;
      }
      const data = (await cal.json()) as { items: Item[] };
      setItems(data.items ?? []);
      if (me.ok) {
        const body = (await me.json()) as { ui_preferences?: { saved_views?: Record<string, SavedView> } };
        setViews(body.ui_preferences?.saved_views ?? {});
      }
    })();
  }, []);

  async function saveView(e: React.FormEvent) {
    e.preventDefault();
    const key = name.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 40);
    if (!key) return;
    const r = await fetch("/api/auth/me/preferences", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ saved_views: { [key]: { label: name.trim(), query: filter.trim() } } }),
    });
    if (r.ok) {
      const body = (await r.json()) as { ui_preferences?: { saved_views?: Record<string, SavedView> } };
      setViews(body.ui_preferences?.saved_views ?? {});
      setName("");
    }
  }

  const groups = new Map<string, Item[]>();
  const visible = filter.trim()
    ? items.filter((item) => item.title.toLowerCase().includes(filter.trim().toLowerCase()))
    : items;
  for (const item of visible) {
    const day = item.due_at ? item.due_at.slice(0, 10) : "No date";
    const list = groups.get(day) ?? [];
    list.push(item);
    groups.set(day, list);
  }

  return (
    <div className="page-inner">
      <header className="page-header">
        <div className="page-header__text">
          <span className="pill">Planning</span>
          <h1>Calendar</h1>
          <p className="muted page-header__lead">Tasks you can see, grouped by due date.</p>
        </div>
      </header>
      {error ? <p className="err">{error}</p> : null}
      <form onSubmit={saveView} className="card" style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", maxWidth: 720, flexWrap: "wrap" }}>
        <input className="input" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter titles" />
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Name this view" />
        <button className="btn btn-secondary" type="submit">Save view</button>
      </form>
      <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
        {Object.entries(views).map(([key, view]) => (
          <button key={key} type="button" className="btn btn-sm btn-secondary" onClick={() => setFilter(view.query)}>
            {view.label}
          </button>
        ))}
      </div>
      <div className="stack" style={{ gap: "1rem", marginTop: "1rem" }}>
        {Array.from(groups.entries()).map(([day, rows]) => (
          <section key={day}>
            <h2 style={{ fontSize: "0.95rem" }}>{day}</h2>
            {rows.map((row) => (
              <div key={row.id} className="text-sm" style={{ marginTop: "0.25rem" }}>
                <Link href={`/projects/${row.project_id}/tasks/${row.id}`}>{row.title}</Link>
                <span className="muted"> · {row.project_name} · {row.status}{row.recurrence ? ` · ${row.recurrence}` : ""}</span>
              </div>
            ))}
          </section>
        ))}
        {visible.length === 0 && !error ? <p className="muted text-sm">No dated tasks yet.</p> : null}
      </div>
    </div>
  );
}
