"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Dep = { id: string; predecessor_id: string; successor_id: string };
type TaskHit = { id: string; title: string };

export function TaskLinks({ projectId, taskId }: { projectId: string; taskId: string }) {
  const [deps, setDeps] = useState<Dep[]>([]);
  const [names, setNames] = useState<Record<string, string>>({});

  useEffect(() => {
    void (async () => {
      const [dr, tr] = await Promise.all([
        fetch(`/api/projects/${projectId}/dependencies`),
        fetch(`/api/projects/${projectId}/tasks`),
      ]);
      if (dr.ok) {
        const body = (await dr.json()) as { items: Dep[] };
        setDeps(body.items ?? []);
      }
      if (tr.ok) {
        const body = (await tr.json()) as { items: TaskHit[] };
        const map: Record<string, string> = {};
        for (const task of body.items ?? []) map[task.id] = task.title;
        setNames(map);
      }
    })();
  }, [projectId]);

  const before = deps.filter((row) => row.successor_id === taskId);
  const after = deps.filter((row) => row.predecessor_id === taskId);
  if (before.length === 0 && after.length === 0) return null;

  function label(id: string) {
    return names[id] ?? id.slice(0, 8);
  }

  function links(rows: Dep[], idKey: "predecessor_id" | "successor_id") {
    return rows.map((row, index) => (
      <span key={row.id}>
        {index > 0 ? ", " : ""}
        <Link href={`/projects/${projectId}/tasks/${row[idKey]}`}>{label(row[idKey])}</Link>
      </span>
    ));
  }

  return (
    <section className="card" style={{ maxWidth: 700 }}>
      <h2 style={{ fontSize: "1rem", marginTop: 0 }}>Dependencies</h2>
      {before.length > 0 ? <p className="text-sm">Waits on {links(before, "predecessor_id")}</p> : null}
      {after.length > 0 ? <p className="text-sm">Blocks {links(after, "successor_id")}</p> : null}
    </section>
  );
}
