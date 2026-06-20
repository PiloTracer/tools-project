"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge, stageBadgeVariant } from "@/components/Badge";
import { Dialog } from "@/components/Dialog";

type ProspectDetail = {
  id: string;
  company_name: string;
  pipeline_stage: string;
  pipeline_value: number | null;
  source: string | null;
  first_contact_date: string | null;
  last_interaction: string | null;
  next_action: string | null;
  next_action_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

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

function formatCurrency(v: number | null) {
  if (v == null) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(v);
}

function formatDate(d: string | null) {
  if (!d) return "—";
  const dt = new Date(d);
  const now = new Date();
  const diff = now.getTime() - dt.getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return dt.toLocaleDateString();
}

export function ProspectPreview({
  prospectId,
  onClose,
}: {
  prospectId: string | null;
  onClose: () => void;
}) {
  const [data, setData] = useState<ProspectDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [prevId, setPrevId] = useState(prospectId);

  // Reset state when prospectId changes — adjust during render (avoids setState-in-effect cascade).
  if (prospectId !== prevId) {
    setPrevId(prospectId);
    setData(null);
    setErr(null);
  }

  useEffect(() => {
    if (!prospectId) return;
    let active = true;
    fetch(`/api/prospects/${prospectId}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((j) => {
        if (active) setData(j as ProspectDetail);
      })
      .catch((e) => {
        if (active) setErr(e.message);
      });
    return () => {
      active = false;
    };
  }, [prospectId]);

  if (!prospectId) return null;

  return (
    <Dialog open title={data?.company_name ?? "Prospect"} onClose={onClose}>
      {err ? (
        <p className="err text-sm">{err}</p>
      ) : !data ? (
        <p className="muted text-sm">Loading…</p>
      ) : (
        <div className="stack" style={{ gap: "0.75rem" }}>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <Badge variant={stageBadgeVariant(data.pipeline_stage)}>
              {STAGE_LABELS[data.pipeline_stage] ?? data.pipeline_stage}
            </Badge>
            {data.pipeline_value != null ? (
              <span className="pill pill-muted">{formatCurrency(data.pipeline_value)}</span>
            ) : null}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", fontSize: "0.85rem" }}>
            {data.source ? (
              <>
                <span className="muted">Source</span>
                <span>{data.source}</span>
              </>
            ) : null}
            <span className="muted">First contact</span>
            <span>{formatDate(data.first_contact_date)}</span>
            <span className="muted">Last interaction</span>
            <span>{formatDate(data.last_interaction)}</span>
            {data.next_action ? (
              <>
                <span className="muted">Next action</span>
                <span>{data.next_action}</span>
              </>
            ) : null}
            {data.next_action_date ? (
              <>
                <span className="muted">Next action date</span>
                <span>{formatDate(data.next_action_date)}</span>
              </>
            ) : null}
          </div>

          {data.notes ? (
            <div>
              <span className="text-sm muted" style={{ display: "block", marginBottom: "0.25rem" }}>Notes</span>
              <p style={{ margin: 0, whiteSpace: "pre-wrap", fontSize: "0.9rem", lineHeight: 1.5 }}>
                {data.notes.length > 300 ? data.notes.slice(0, 300) + "…" : data.notes}
              </p>
            </div>
          ) : null}

          <div style={{ marginTop: "0.5rem" }}>
            <Link
              href={`/prospects/${prospectId}`}
              className="btn btn-primary text-sm"
              style={{ display: "inline-flex", textDecoration: "none" }}
            >
              Expand →
            </Link>
          </div>
        </div>
      )}
    </Dialog>
  );
}
