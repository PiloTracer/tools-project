"use client";

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

export function CommitCard({ meta, projectId }: { meta: CommitMeta; projectId?: string }) {
  const [showFull, setShowFull] = useState(false);
  const [linkedRefs, setLinkedRefs] = useState<LinkedRef[] | null>(null);
  const [linkedDetails, setLinkedDetails] = useState<Record<string, { ref: string | null; title: string; status: string }>>({});
  const [showLinked, setShowLinked] = useState(false);
  const [linkedBusy, setLinkedBusy] = useState(false);
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
        const details: Record<string, { ref: string | null; title: string; status: string }> = {};
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
                const j = await resp.json() as { ref?: string | null; title: string; status: string };
                details[r.subject_id] = { ref: j.ref ?? null, title: j.title, status: j.status };
              }
            } catch { /* ignore */ }
          }),
        ).then(() => setLinkedDetails(details));
      })
      .finally(() => setLinkedBusy(false));
  }, [showLinked, projectId, meta.commit_id, linkedRefs]);

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
              const href = projectId
                ? r.subject_type === "task"
                  ? `/projects/${projectId}/tasks/${r.subject_id}`
                  : r.subject_type === "ticket"
                    ? `/projects/${projectId}/tickets/${r.subject_id}`
                    : "#"
                : "#";
              return (
                <li key={r.id} style={{ padding: "0.4rem 0", borderBottom: "1px solid var(--border)" }}>
                  <a
                    href={href}
                    style={{ textDecoration: "none", color: "inherit" }}
                    target="_blank"
                    rel="noopener noreferrer"
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
                      <span className="muted text-sm">Loading…</span>
                    )}
                  </a>
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