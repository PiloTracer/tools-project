"use client";

import { useEffect, useState } from "react";

type Row = { assignee_id: string | null; name: string; open_tasks: number };

export default function WorkloadPage() {
  const [items, setItems] = useState<Row[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      const r = await fetch("/api/planning/workload");
      if (!r.ok) {
        setError("Could not load workload");
        return;
      }
      const data = (await r.json()) as { items: Row[] };
      setItems(data.items ?? []);
    })();
  }, []);

  const max = Math.max(1, ...items.map((row) => row.open_tasks));

  return (
    <div className="page-inner">
      <header className="page-header">
        <div className="page-header__text">
          <span className="pill">Planning</span>
          <h1>Workload</h1>
          <p className="muted page-header__lead">Open tasks by assignee on projects you belong to.</p>
        </div>
      </header>
      {error ? <p className="err">{error}</p> : null}
      <div className="stack" style={{ gap: "0.6rem", maxWidth: 640 }}>
        {items.map((row) => (
          <div key={row.assignee_id ?? "none"}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>{row.name}</span>
              <span className="muted text-sm">{row.open_tasks}</span>
            </div>
            <div style={{ height: 8, background: "var(--surface)", borderRadius: 99, marginTop: 4 }}>
              <div style={{ width: `${(row.open_tasks / max) * 100}%`, height: "100%", background: "var(--accent)", borderRadius: 99 }} />
            </div>
          </div>
        ))}
        {items.length === 0 && !error ? <p className="muted text-sm">No open tasks.</p> : null}
      </div>
    </div>
  );
}
