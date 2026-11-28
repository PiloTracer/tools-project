"use client";

import { useState } from "react";

import { useDownload } from "@/components/useDownload";

const REPORTS = [
  {
    id: "pipeline",
    title: "Pipeline Report",
    description: "All prospects with stage, value, source, dates, and notes. Filter by stage or source.",
    url: "/api/reports/pipeline",
    filename: "pipeline-report.xlsx",
    icon: "\u{1F4CA}",
  },
  {
    id: "clients",
    title: "Clients Report",
    description: "All clients with slug, industry, contacts, and metadata.",
    url: "/api/reports/clients",
    filename: "clients-report.xlsx",
    icon: "\u{1F3E2}",
  },
] as const;

export default function ReportsPage() {
  const download = useDownload();
  const [dimension, setDimension] = useState("pipeline_stage");
  const [dataset, setDataset] = useState<"prospects" | "clients">("prospects");
  const [measure, setMeasure] = useState<"count" | "pipeline_value">("count");
  const [rows, setRows] = useState<{ key: string; value: number }[]>([]);
  const [queryError, setQueryError] = useState<string | null>(null);

  return (
    <div className="page-inner">
      <header className="page-header">
        <div className="page-header__text">
          <span className="pill">Analytics</span>
          <h1>Reports</h1>
          <p className="muted page-header__lead">
            Export project data to Excel spreadsheets for offline analysis.
          </p>
        </div>
      </header>

      <section className="page-body">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
            gap: "1rem",
          }}
        >
          {REPORTS.map((r) => (
            <div
              key={r.id}
              className="card"
              style={{
                padding: "1.5rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
              }}
            >
              <span style={{ fontSize: "2rem" }}>{r.icon}</span>
              <h3 style={{ margin: 0 }}>{r.title}</h3>
              <p className="muted text-sm" style={{ margin: 0 }}>
                {r.description}
              </p>
              <button
                className="btn btn-primary"
                style={{ marginTop: "auto", alignSelf: "flex-start" }}
                onClick={() => download(r.url, r.filename)}
              >
                Download Excel
              </button>
            </div>
          ))}
        </div>

        <form
          className="card"
          style={{ marginTop: "1.5rem", padding: "1.5rem", maxWidth: 520 }}
          onSubmit={async (e) => {
            e.preventDefault();
            setQueryError(null);
            const r = await fetch("/api/reports/query", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                dataset,
                dimension: dataset === "clients" && dimension === "pipeline_stage" ? "industry" : dimension,
                measure: dataset === "clients" ? "count" : measure,
              }),
            });
            if (!r.ok) {
              setQueryError("That report is not available");
              return;
            }
            const data = (await r.json()) as { rows: { key: string; value: number }[] };
            setRows(data.rows ?? []);
          }}
        >
          <h3 style={{ marginTop: 0 }}>Grouped report</h3>
          <label className="field">
            <span className="label">Records</span>
            <select className="input" value={dataset} onChange={(e) => setDataset(e.target.value as "prospects" | "clients")}>
              <option value="prospects">Prospects</option>
              <option value="clients">Clients</option>
            </select>
          </label>
          <label className="field">
            <span className="label">Group by</span>
            <select className="input" value={dimension} onChange={(e) => setDimension(e.target.value)}>
              {dataset === "prospects" ? <option value="pipeline_stage">Stage</option> : null}
              <option value="source">Fuente</option>
              <option value="industry">Giro</option>
              <option value="zone">Zona</option>
            </select>
          </label>
          {dataset === "prospects" ? (
            <label className="field">
              <span className="label">Measure</span>
              <select className="input" value={measure} onChange={(e) => setMeasure(e.target.value as "count" | "pipeline_value")}>
                <option value="count">Count</option>
                <option value="pipeline_value">Pipeline value</option>
              </select>
            </label>
          ) : null}
          <button className="btn btn-primary" type="submit">Run</button>
          {queryError ? <p className="err text-sm">{queryError}</p> : null}
          <ul>
            {rows.map((row) => (
              <li key={row.key}>{row.key}: {row.value}</li>
            ))}
          </ul>
        </form>

        <div className="card" style={{ marginTop: "1.5rem", padding: "1.5rem" }}>
          <h3 style={{ marginTop: 0 }}>Project-level reports</h3>
          <p className="muted text-sm">
            Task and ticket exports are available from each project&apos;s overview page under the
            &ldquo;Project stats&rdquo; section.
          </p>
        </div>
      </section>
    </div>
  );
}
