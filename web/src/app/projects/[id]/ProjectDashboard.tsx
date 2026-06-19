"use client";

import { useEffect, useState } from "react";
import { DonutChart, type DonutSlice } from "@/components/DonutChart";
import { useDownload } from "@/components/useDownload";

export function ProjectDashboard({ projectId, projectSlug }: { projectId: string; projectSlug: string }) {
  const [taskSlices, setTaskSlices] = useState<DonutSlice[]>([]);
  const [ticketSlices, setTicketSlices] = useState<DonutSlice[]>([]);
  const [taskTotal, setTaskTotal] = useState(0);
  const [ticketTotal, setTicketTotal] = useState(0);
  const download = useDownload();

  useEffect(() => {
    Promise.all([
      fetch(`/api/projects/${projectId}/tasks`).then(r => r.ok ? r.json() : { items: [] }),
      fetch(`/api/projects/${projectId}/tickets`).then(r => r.ok ? r.json() : { items: [] }),
    ]).then(([tasksRes, ticketsRes]) => {
      const tasks = tasksRes.items ?? [];
      const tickets = ticketsRes.items ?? [];
      setTaskTotal(tasks.length);
      setTicketTotal(tickets.length);

      const taskStatusCounts: Record<string, number> = {};
      tasks.forEach((t: { status: string }) => { taskStatusCounts[t.status] = (taskStatusCounts[t.status] || 0) + 1; });
      setTaskSlices(Object.entries(taskStatusCounts).map(([name, value]) => ({ name, value })));

      const ticketStatusCounts: Record<string, number> = {};
      tickets.forEach((t: { status: string }) => { ticketStatusCounts[t.status] = (ticketStatusCounts[t.status] || 0) + 1; });
      setTicketSlices(Object.entries(ticketStatusCounts).map(([name, value]) => ({ name, value })));
    }).catch(() => {});
  }, [projectId]);

  return (
    <div className="card wide stack">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span className="pill" style={{ alignSelf: "flex-start" }}>Project stats</span>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button className="btn btn-sm btn-secondary" onClick={() => download(`/api/reports/projects/${projectId}/tasks`, `${projectSlug}-tasks.xlsx`)}>
            Export tasks
          </button>
          <button className="btn btn-sm btn-secondary" onClick={() => download(`/api/reports/projects/${projectId}/tickets`, `${projectSlug}-tickets.xlsx`)}>
            Export tickets
          </button>
        </div>
      </div>
      <div className="stat-card-row">
        <div className="stat-card">
          <span className="text-sm muted">Total tasks</span>
          <span className="stat-value">{taskTotal}</span>
        </div>
        <div className="stat-card">
          <span className="text-sm muted">Total tickets</span>
          <span className="stat-value">{ticketTotal}</span>
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
        <div>
          <span className="text-sm muted" style={{ marginBottom: "0.5rem", display: "block" }}>Tasks by status</span>
          {taskSlices.length > 0 ? <DonutChart data={taskSlices} height={180} innerRadius={35} outerRadius={65} /> : <p className="muted text-sm">No tasks</p>}
        </div>
        <div>
          <span className="text-sm muted" style={{ marginBottom: "0.5rem", display: "block" }}>Tickets by status</span>
          {ticketSlices.length > 0 ? <DonutChart data={ticketSlices} height={180} innerRadius={35} outerRadius={65} /> : <p className="muted text-sm">No tickets</p>}
        </div>
      </div>
    </div>
  );
}
