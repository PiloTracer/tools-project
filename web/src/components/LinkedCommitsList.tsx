"use client";

import { useEffect, useState } from "react";

type CommitBrief = {
  sha: string;
  short_sha: string;
  message_preview: string;
  html_url: string;
  author_name: string | null;
  committed_at: string;
  owner: string;
  repo: string;
};

type CommitRef = {
  id: string;
  subject_type: string;
  subject_id: string;
  subject_ref: string | null;
  subject_title: string | null;
  subject_status: string | null;
  commit: CommitBrief | null;
  created_at: string;
};

export function LinkedCommitsList({
  projectId,
  subjectType,
  subjectId,
}: {
  projectId: string;
  subjectType: "task" | "ticket";
  subjectId: string;
}) {
  const [refs, setRefs] = useState<CommitRef[] | null>(null);

  useEffect(() => {
    fetch(
      `/api/projects/${projectId}/github/refs?subject_type=${subjectType}&subject_id=${subjectId}`,
    )
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d) setRefs((d as { items: CommitRef[] }).items);
      })
      .catch(() => {});
  }, [projectId, subjectType, subjectId]);

  if (!refs || refs.length === 0) return null;

  return (
    <div className="card wide stack">
      <h2 style={{ marginTop: 0 }}>Linked Commits</h2>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {refs.map((r) => {
          const c = r.commit;
          if (!c) return null;
          return (
            <li
              key={r.id}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "0.5rem",
                padding: "0.5rem 0",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <a
                href={c.html_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  fontFamily: "var(--font-mono, monospace)",
                  fontSize: "0.8rem",
                  whiteSpace: "nowrap",
                  flexShrink: 0,
                }}
              >
                {c.short_sha}
              </a>
              <div style={{ flex: 1, minWidth: 0 }}>
                <span style={{ fontSize: "0.85rem" }}>
                  {c.message_preview}
                </span>
                <div className="text-sm muted" style={{ marginTop: "0.15rem" }}>
                  {c.owner}/{c.repo}
                  {c.author_name ? ` · ${c.author_name}` : ""}
                  {c.committed_at
                    ? ` · ${new Date(c.committed_at).toLocaleDateString()}`
                    : ""}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
