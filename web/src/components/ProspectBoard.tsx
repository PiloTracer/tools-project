"use client";

import { useMemo, useState } from "react";

import { Badge, stageBadgeVariant } from "@/components/Badge";
import { ProspectPreview } from "@/components/ProspectPreview";

const PIPELINE_STAGES = [
  "target", "connected", "engaged", "call_scheduled", "call_done",
  "proposal_sent", "negotiating", "won", "lost",
];

const STAGE_LABELS: Record<string, string> = {
  target: "Target",
  connected: "Connected",
  engaged: "Engaged",
  call_scheduled: "Call scheduled",
  call_done: "Call done",
  proposal_sent: "Proposal sent",
  negotiating: "Negotiating",
  won: "Won",
  lost: "Lost",
};

const STAGE_COLORS: Record<string, string> = {
  target: "var(--accent)",
  connected: "var(--accent)",
  engaged: "var(--muted)",
  call_scheduled: "var(--muted)",
  call_done: "var(--muted)",
  proposal_sent: "var(--accent-warn, #c98300)",
  negotiating: "var(--accent-warn, #c98300)",
  won: "var(--success)",
  lost: "var(--danger)",
};

function formatCurrency(v: number | null) {
  if (v == null) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(v);
}

type ProspectRow = {
  id: string;
  company_name: string;
  pipeline_stage: string;
  pipeline_value: number | null;
  source: string | null;
  next_action: string | null;
  notes: string | null;
};

export function ProspectBoard({
  prospects,
  canEdit,
  onStageChange,
}: {
  prospects: ProspectRow[];
  canEdit: boolean;
  onStageChange: (prospectId: string, newStage: string) => void;
}) {
  const [dragOverCol, setDragOverCol] = useState<string | null>(null);
  const [previewId, setPreviewId] = useState<string | null>(null);

  const columns = useMemo(() => {
    const map: Record<string, ProspectRow[]> = {};
    for (const stage of PIPELINE_STAGES) {
      map[stage] = [];
    }
    const seen = new Set<string>();
    for (const p of prospects) {
      if (seen.has(p.id)) continue;
      seen.add(p.id);
      if (map[p.pipeline_stage]) {
        map[p.pipeline_stage].push(p);
      } else {
        map.target.push(p);
      }
    }
    return map;
  }, [prospects]);

  function onDragStart(e: React.DragEvent, prospectId: string) {
    e.dataTransfer.setData("text/plain", prospectId);
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
    const prospectId = e.dataTransfer.getData("text/plain");
    if (prospectId) onStageChange(prospectId, colKey);
    setDragOverCol(null);
  }

  return (
    <>
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
        {PIPELINE_STAGES.map((stage) => (
          <div
            key={stage}
            className="kanban-col"
            onDragOver={(e) => canEdit && onDragOver(e, stage)}
            onDragLeave={onDragLeave}
            onDrop={(e) => canEdit && onDrop(e, stage)}
            style={{
              flex: "1 1 0",
              minWidth: 180,
              maxWidth: 320,
              background:
                dragOverCol === stage
                  ? "rgba(56, 189, 248, 0.08)"
                  : "var(--bg-elevated, #121a2e)",
              borderRadius: "var(--radius, 10px)",
              border: `1px solid ${
                dragOverCol === stage ? "var(--accent)" : "var(--border)"
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
                style={{ fontWeight: 600, color: STAGE_COLORS[stage] ?? "var(--muted)" }}
              >
                {STAGE_LABELS[stage] ?? stage}
              </span>
              <span className="pill pill-muted" style={{ fontSize: "0.65rem" }}>
                {(columns[stage] || []).length}
              </span>
            </div>
            <div className="kanban-col-items stack" style={{ gap: "0.5rem" }}>
              {(columns[stage] || []).map((p) => (
                <div
                  key={p.id}
                  className="card kanban-card"
                  draggable={canEdit}
                  onDragStart={(e) => onDragStart(e, p.id)}
                  style={{
                    padding: "0.55rem 0.7rem",
                    cursor: canEdit ? "grab" : "pointer",
                    border: "1px solid var(--border)",
                    transition: "box-shadow 0.15s",
                  }}
                >
                  <div
                    style={{
                      fontWeight: 600,
                      wordBreak: "break-word",
                      cursor: "pointer",
                      color: "inherit",
                    }}
                    onClick={() => setPreviewId(p.id)}
                  >
                    {p.company_name}
                  </div>
                  <div
                    className="text-sm"
                    style={{
                      display: "flex",
                      gap: "0.4rem",
                      marginTop: "0.35rem",
                      flexWrap: "wrap",
                      alignItems: "center",
                    }}
                  >
                    <Badge variant={stageBadgeVariant(p.pipeline_stage)} style={{ fontSize: "0.6rem" }}>
                      {STAGE_LABELS[p.pipeline_stage] ?? p.pipeline_stage}
                    </Badge>
                    {p.pipeline_value != null ? (
                      <span style={{ fontFamily: "ui-monospace, monospace", fontSize: "0.65rem", color: "var(--muted)" }}>
                        {formatCurrency(p.pipeline_value)}
                      </span>
                    ) : null}
                  </div>
                  {p.source || p.next_action ? (
                    <div
                      className="muted text-sm"
                      style={{
                        marginTop: "0.3rem",
                        fontSize: "0.65rem",
                        lineHeight: 1.3,
                      }}
                    >
                      {p.source ? <span>{p.source}</span> : null}
                      {p.source && p.next_action ? <span> · </span> : null}
                      {p.next_action ? <span>{p.next_action}</span> : null}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <ProspectPreview
        prospectId={previewId}
        onClose={() => setPreviewId(null)}
      />
    </>
  );
}
