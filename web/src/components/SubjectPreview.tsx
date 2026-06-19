"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Dialog } from "@/components/Dialog";

type SubjectDetail = {
  id: string;
  ref: string | null;
  title: string;
  status: string;
  priority: string;
  description: string | null;
};

export function SubjectPreview({
  projectId,
  subjectType,
  subjectId,
  onClose,
}: {
  projectId: string;
  subjectType: string;
  subjectId: string;
  onClose: () => void;
}) {
  const [data, setData] = useState<SubjectDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const endpoint = subjectType === "task" ? `/api/tasks/${subjectId}` : `/api/tickets/${subjectId}`;
    fetch(endpoint)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((j) => setData(j as SubjectDetail))
      .catch((e) => setErr(e.message));
  }, [subjectType, subjectId]);

  const title = data ? `${data.ref ?? subjectType}: ${data.title}` : subjectType;
  const href = subjectType === "task"
    ? `/projects/${projectId}/tasks/${subjectId}`
    : `/projects/${projectId}/tickets/${subjectId}`;

  return (
    <Dialog open title={title} onClose={onClose}>
      {err ? (
        <p className="err text-sm">{err}</p>
      ) : !data ? (
        <p className="muted text-sm">Loading…</p>
      ) : (
        <div className="stack" style={{ gap: "0.6rem" }}>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <span className="pill">{data.status}</span>
            <span className="pill pill-muted">{data.priority}</span>
          </div>
          {data.description ? (
            <p style={{ margin: 0, whiteSpace: "pre-wrap", fontSize: "0.9rem", lineHeight: 1.5 }}>
              {data.description.length > 300 ? data.description.slice(0, 300) + "…" : data.description}
            </p>
          ) : (
            <p className="muted text-sm">No description.</p>
          )}
          <div style={{ marginTop: "0.5rem" }}>
            <Link
              href={href}
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
