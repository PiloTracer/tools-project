"use client";

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
