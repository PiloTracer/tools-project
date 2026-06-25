"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Dialog } from "@/components/Dialog";

type CommitMeta = {
  sha: string;
  owner: string;
  repo: string;
  html_url: string;
  message_preview: string;
  full_message?: string;
  commit_id?: string;
};

type LinkedRef = {
  id: string;
  subject_type: string;
  subject_id: string;
  created_at: string;
};

type SubjectDetail = {
  id: string;
  ref: string | null;
  title: string;
  status: string;
  priority: string;
  description: string | null;
};

export function CommitCard({ meta, projectId }: { meta: CommitMeta; projectId?: string }) {
  const [showFull, setShowFull] = useState(false);
  const [linkedRefs, setLinkedRefs] = useState<LinkedRef[] | null>(null);
  const [linkedDetails, setLinkedDetails] = useState<Record<string, SubjectDetail>>({});
  const [showLinked, setShowLinked] = useState(false);
  const [linkedBusy, setLinkedBusy] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState<{ type: string; id: string } | null>(null);
  const hasMore = !!(meta.full_message && meta.full_message.length > 100);

  useEffect(() => {
    if (!showLinked || !projectId || !meta.commit_id || linkedRefs) return;
    setLinkedBusy(true);
    fetch(`/api/projects/${projectId}/github/refs?github_commit_id=${meta.commit_id}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!d) return;
        const refs = (d as { items: LinkedRef[] }).items;
        setLinkedRefs(refs);
        const details: Record<string, SubjectDetail> = {};
        Promise.all(
          refs.map(async (r) => {
            const endpoint = r.subject_type === "task"
              ? `/api/tasks/${r.subject_id}`
              : r.subject_type === "ticket"
                ? `/api/tickets/${r.subject_id}`
                : null;
            if (!endpoint) return;
            try {
              const resp = await fetch(endpoint);
              if (resp.ok) {
                const j = await resp.json() as SubjectDetail;
                details[r.subject_id] = j;
              }
            } catch { /* ignore */ }
          }),
        ).then(() => setLinkedDetails(details));
      })
      .finally(() => setLinkedBusy(false));
  }, [showLinked, projectId, meta.commit_id, linkedRefs]);

  if (selectedSubject) {
    const d = linkedDetails[selectedSubject.id];
    const href = projectId
      ? selectedSubject.type === "task"
        ? `/projects/${projectId}/tasks/${selectedSubject.id}`
        : `/projects/${projectId}/tickets/${selectedSubject.id}`
      : "#";
    return (
      <Dialog
        open
        onClose={() => setSelectedSubject(null)}
        title={d ? `${d.ref ?? selectedSubject.type}: ${d.title}` : selectedSubject.type}
      >
        {!d ? (
          <p className="muted text-sm">Loading…</p>
        ) : (
          <div className="stack" style={{ gap: "0.6rem" }}>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <span className="pill">{d.status}</span>
              <span className="pill pill-muted">{d.priority}</span>
            </div>
            {d.description ? (
              <p style={{ margin: 0, whiteSpace: "pre-wrap", fontSize: "0.9rem", lineHeight: 1.5 }}>
                {d.description.length > 300 ? d.description.slice(0, 300) + "…" : d.description}
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

  return (
    <div style={{ margin: "0.35rem 0 0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
        <a
          href={meta.html_url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}
        >
          <code style={{ fontSize: "0.85rem" }}>{meta.sha.slice(0, 7)}</code>
        </a>
        <span className="muted" style={{ fontSize: "0.8rem" }}>
          {meta.owner}/{meta.repo}
        </span>
        {meta.commit_id && projectId ? (
          <button
            type="button"
            className="btn btn-ghost text-sm"
            style={{ padding: "0.1rem 0.4rem", fontSize: "0.7rem" }}
            onClick={() => setShowLinked(true)}
          >
            Linked
          </button>
        ) : null}
      </div>
      <div style={{ margin: "0.2rem 0 0", fontSize: "0.9rem" }}>
        <span style={{ whiteSpace: "pre-wrap" }}>
          {showFull && meta.full_message ? meta.full_message.split("\n")[0] : meta.message_preview}
        </span>
        {hasMore ? (
          <button
            type="button"
            onClick={() => setShowFull(!showFull)}
            style={{
              background: "none",
              border: "none",
              color: "var(--accent)",
              cursor: "pointer",
              fontSize: "0.75rem",
              padding: "0 0.25rem",
              fontFamily: "inherit",
              verticalAlign: "baseline",
            }}
          >
            {showFull ? "less" : "more"}
          </button>
        ) : null}
        {showFull && meta.full_message ? (
          <div style={{ whiteSpace: "pre-wrap", marginTop: "0.5rem" }}>
            {meta.full_message.split("\n").slice(1).join("\n").trim()}
          </div>
        ) : null}
      </div>

      <Dialog
        open={showLinked}
        onClose={() => setShowLinked(false)}
        title="Linked items"
      >
        {linkedBusy && !linkedRefs ? (
          <p className="muted text-sm">Loading…</p>
        ) : !linkedRefs || linkedRefs.length === 0 ? (
          <p className="muted text-sm">No linked tasks or tickets.</p>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {linkedRefs.map((r) => {
              const d = linkedDetails[r.subject_id];
              const label = d ? `${d.ref ?? d.title}` : "Loading…";
              return (
                <li key={r.id} style={{ padding: "0.4rem 0", borderBottom: "1px solid var(--border)" }}>
                  <button
                    type="button"
                    style={{
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      textAlign: "left",
                      width: "100%",
                      padding: 0,
                      fontFamily: "inherit",
                      color: "inherit",
                    }}
                    onClick={() => setSelectedSubject({ type: r.subject_type, id: r.subject_id })}
                  >
                    <span className="pill" style={{ fontSize: "0.65rem", marginRight: "0.35rem" }}>
                      {r.subject_type}
                    </span>
                    {d ? (
                      <>
                        <strong>{d.ref ?? d.title}</strong>
                        <span className="muted text-sm" style={{ marginLeft: "0.35rem" }}>· {d.status}</span>
                      </>
                    ) : (
                      <span className="muted text-sm">{label}</span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </Dialog>
    </div>
  );
}

export function extractCommitMeta(
  meta_json: Record<string, unknown> | null | undefined,
): CommitMeta | null {
  if (!meta_json) return null;
  const sha = meta_json.sha as string | undefined;
  const owner = meta_json.owner as string | undefined;
  const repo = meta_json.repo as string | undefined;
  const html_url = meta_json.html_url as string | undefined;
  const message_preview = meta_json.message_preview as string | undefined;
  if (!sha || !owner || !repo || !html_url) return null;
  return {
    sha,
    owner,
    repo,
    html_url,
    message_preview: message_preview ?? "",
    full_message: (meta_json.full_message as string) ?? undefined,
    commit_id: (meta_json.commit_id as string) ?? undefined,
  };
}