"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

import { ProjectSubNav } from "../ProjectSubNav";

type TaskRow = { id: string; title: string; status: string; due_at: string | null; created_at: string };
type Dep = { id: string; predecessor_id: string; successor_id: string };
type Profit = {
  hours: number;
  minutes: number;
  revenue_amount: number | null;
  hourly_cost: number | null;
  labor_cost: number | null;
  margin: number | null;
  currency: string;
};

export default function GanttPage() {
  const params = useParams();
  const id = params.id as string;
  const [tasks, setTasks] = useState<TaskRow[]>([]);
  const [deps, setDeps] = useState<Dep[]>([]);
  const [profit, setProfit] = useState<Profit | null>(null);
  const [pred, setPred] = useState("");
  const [succ, setSucc] = useState("");
  const [minutes, setMinutes] = useState("60");
  const [revenue, setRevenue] = useState("");
  const [hourly, setHourly] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    const [tr, dr, pr] = await Promise.all([
      fetch(`/api/projects/${id}/tasks`),
      fetch(`/api/projects/${id}/dependencies`),
      fetch(`/api/projects/${id}/profitability`),
    ]);
    if (tr.ok) {
      const body = (await tr.json()) as { items: TaskRow[] };
      setTasks(body.items ?? []);
    }
    if (dr.ok) {
      const body = (await dr.json()) as { items: Dep[] };
      setDeps(body.items ?? []);
    }
    if (pr.ok) setProfit((await pr.json()) as Profit);
  }

  useEffect(() => {
    void load();
  }, [id]);

  const spanStart = Date.now() - 7 * 86400000;
  const spanEnd = Date.now() + 21 * 86400000;

  function barStyle(task: TaskRow): { left: string; width: string } {
    const start = new Date(task.created_at).getTime();
    const end = task.due_at ? new Date(task.due_at).getTime() : start + 86400000;
    const left = Math.min(96, Math.max(0, ((Math.min(start, end) - spanStart) / (spanEnd - spanStart)) * 100));
    const right = Math.min(100, Math.max(left + 2, ((Math.max(start, end) - spanStart) / (spanEnd - spanStart)) * 100));
    return { left: `${left}%`, width: `${Math.max(2, right - left)}%` };
  }

  const names = Object.fromEntries(tasks.map((task) => [task.id, task.title]));

  return (
    <div className="page-inner stack-lg">
      <Link href={`/projects/${id}`} className="muted text-sm">← Project</Link>
      <ProjectSubNav projectId={id} current="gantt" />
      <h1>Timeline</h1>
      <p className="muted text-sm">Each bar runs from the day the task was created to its due date. Linking tasks does not move those dates.</p>
      <div className="stack" style={{ gap: "0.45rem" }}>
        {tasks.map((task) => (
          <div key={task.id} style={{ display: "grid", gridTemplateColumns: "180px 1fr", gap: "0.5rem", alignItems: "center" }}>
            <Link href={`/projects/${id}/tasks/${task.id}`} className="text-sm">{task.title}</Link>
            <div style={{ position: "relative", height: 16, background: "var(--surface)", borderRadius: 4 }}>
              <div style={{ position: "absolute", top: 3, height: 10, background: "var(--accent)", borderRadius: 2, ...barStyle(task) }} />
            </div>
          </div>
        ))}
      </div>

      <section className="card" style={{ maxWidth: 640 }}>
        <h2 style={{ fontSize: "1rem" }}>Dependency</h2>
        <form
          className="stack"
          onSubmit={async (e) => {
            e.preventDefault();
            const r = await fetch(`/api/projects/${id}/dependencies`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ predecessor_id: pred, successor_id: succ }),
            });
            setMessage(r.ok ? "Link saved" : "Could not link those tasks");
            if (r.ok) void load();
          }}
        >
          <select className="input" value={pred} onChange={(e) => setPred(e.target.value)} required>
            <option value="">Predecessor</option>
            {tasks.map((task) => <option key={task.id} value={task.id}>{task.title}</option>)}
          </select>
          <select className="input" value={succ} onChange={(e) => setSucc(e.target.value)} required>
            <option value="">Successor</option>
            {tasks.map((task) => <option key={task.id} value={task.id}>{task.title}</option>)}
          </select>
          <button className="btn btn-secondary" type="submit">Link</button>
        </form>
        <ul>
          {deps.map((dep) => (
            <li key={dep.id} className="text-sm muted">
              {names[dep.predecessor_id] ?? dep.predecessor_id.slice(0, 8)} → {names[dep.successor_id] ?? dep.successor_id.slice(0, 8)}
            </li>
          ))}
        </ul>
      </section>

      <section className="card" style={{ maxWidth: 640 }}>
        <h2 style={{ fontSize: "1rem" }}>Time and margin</h2>
        {profit ? (
          <p className="text-sm">
            {profit.hours} h logged
            {profit.margin != null ? ` · margin ${profit.margin} ${profit.currency}` : ""}
            {profit.labor_cost != null ? ` · labor ${profit.labor_cost}` : ""}
          </p>
        ) : null}
        <form
          className="stack"
          onSubmit={async (e) => {
            e.preventDefault();
            const r = await fetch(`/api/projects/${id}/time-entries`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ minutes: Number(minutes), work_date: new Date().toISOString().slice(0, 10) }),
            });
            setMessage(r.ok ? "Time saved" : "Could not save time");
            if (r.ok) void load();
          }}
        >
          <label className="field"><span className="label">Minutes</span>
            <input className="input" value={minutes} onChange={(e) => setMinutes(e.target.value)} />
          </label>
          <button className="btn btn-secondary" type="submit">Log time</button>
        </form>
        <form
          className="stack"
          style={{ marginTop: "0.75rem" }}
          onSubmit={async (e) => {
            e.preventDefault();
            const r = await fetch(`/api/projects/${id}/budget`, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                revenue_amount: revenue ? Number(revenue) : null,
                hourly_cost: hourly ? Number(hourly) : null,
                currency: "USD",
              }),
            });
            setMessage(r.ok ? "Budget saved" : "Could not save the budget");
            if (r.ok) void load();
          }}
        >
          <label className="field"><span className="label">Revenue</span>
            <input className="input" value={revenue} onChange={(e) => setRevenue(e.target.value)} />
          </label>
          <label className="field"><span className="label">Hourly cost</span>
            <input className="input" value={hourly} onChange={(e) => setHourly(e.target.value)} />
          </label>
          <button className="btn btn-secondary" type="submit">Save budget</button>
        </form>
        {message ? <p className="text-sm">{message}</p> : null}
      </section>
    </div>
  );
}
