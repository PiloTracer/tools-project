import Link from "next/link";

import { PipelineFunnel } from "@/components/PipelineFunnel";
import type { PipelineStageRow } from "@/components/PipelineFunnel";

type PipelineData = {
  by_stage: PipelineStageRow[];
  total_value: number;
  won_value: number;
  lost_value: number;
  conversion_rate: number | null;
  needs_attention_count: number;
};

export async function DashboardCrm() {
  const base = process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300";
  let pipeline: PipelineData | null = null;

  try {
    const r = await fetch(`${base}/v1/stats/pipeline`, { cache: "no-store" });
    if (r.ok) {
      const json = (await r.json()) as PipelineData;
      pipeline = json;
    }
  } catch {
    /* API unreachable */
  }

  if (!pipeline) {
    return (
      <div className="dashboard-tile" style={{ gridColumn: "1 / -1" }}>
        <h2>CRM Pipeline</h2>
        <p className="muted text-sm">Pipeline data unavailable.</p>
      </div>
    );
  }

  const nonTerminal = pipeline.by_stage.filter((s) => s.stage !== "won" && s.stage !== "lost");
  const hasData = nonTerminal.some((s) => s.count > 0);
  if (!hasData) {
    return (
      <div className="dashboard-tile" style={{ gridColumn: "1 / -1" }}>
        <div className="dashboard-tile-head">
          <div>
            <h2>CRM Pipeline</h2>
            <p className="muted text-sm dashboard-tile-tagline">No prospects yet — start building your pipeline.</p>
          </div>
        </div>
        <div className="dashboard-actions">
          <Link className="btn btn-primary" href="/prospects/new">
            New prospect
          </Link>
          <Link className="btn btn-secondary" href="/prospects">
            View pipeline
          </Link>
        </div>
      </div>
    );
  }

  const totalProspects = pipeline.by_stage.reduce((s, r) => s + r.count, 0);

  return (
    <div className="dashboard-tile" style={{ gridColumn: "1 / -1" }}>
      <div className="dashboard-tile-head">
        <div>
          <h2>CRM Pipeline</h2>
          <p className="muted text-sm dashboard-tile-tagline">Sales pipeline at a glance.</p>
        </div>
        <Link href="/prospects" className="pill pill-ok" style={{ flexShrink: 0 }}>
          {totalProspects} prospect{totalProspects === 1 ? "" : "s"}
        </Link>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: "0.6rem",
          marginBottom: "1rem",
        }}
      >
        <div className="stat-card">
          <span className="text-sm muted">Pipeline value</span>
          <span className="stat-value">${pipeline.total_value.toLocaleString()}</span>
        </div>
        <div className="stat-card">
          <span className="text-sm muted">Won</span>
          <span className="stat-value" style={{ color: "var(--accent-ok, #22c55e)" }}>
            ${pipeline.won_value.toLocaleString()}
          </span>
        </div>
        {pipeline.conversion_rate !== null ? (
          <div className="stat-card">
            <span className="text-sm muted">Conversion</span>
            <span className="stat-value">{(pipeline.conversion_rate * 100).toFixed(1)}%</span>
          </div>
        ) : null}
        <div className="stat-card">
          <span className="text-sm muted">Needs attention</span>
          <span className="stat-value" style={{ color: pipeline.needs_attention_count > 0 ? "var(--accent-warn, #eab308)" : undefined }}>
            {pipeline.needs_attention_count}
          </span>
        </div>
      </div>

      <div style={{ marginBottom: "0.75rem" }}>
        <p className="dashboard-section-label">Pipeline by stage</p>
        <PipelineFunnel data={pipeline.by_stage} metric="count" />
      </div>

      <div className="dashboard-actions" style={{ marginBottom: 0 }}>
        <Link className="btn btn-primary" href="/prospects/new">
          New prospect
        </Link>
        <Link className="btn btn-secondary" href="/prospects">
          View pipeline
        </Link>
      </div>
    </div>
  );
}
