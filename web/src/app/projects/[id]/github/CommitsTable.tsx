"use client";

import { useState } from "react";

import { DateDisplay } from "@/components/DateDisplay";

type CommitRow = {
  id: string;
  short_sha: string;
  message_preview: string;
  html_url: string;
  committed_at: string;
  author_name: string | null;
  owner: string;
  repo: string;
};

type CommitResponse = {
  items: CommitRow[];
  has_more: boolean;
  total: number | null;
};

export function CommitsTable({
  projectId,
  initialCommits,
  initialHasMore,
}: {
  projectId: string;
  initialCommits: CommitRow[];
  initialHasMore: boolean;
}) {
  const [commits, setCommits] = useState<CommitRow[]>(initialCommits);
  const [hasMore, setHasMore] = useState(initialHasMore);
  const [loading, setLoading] = useState(false);

  async function loadMore() {
    setLoading(true);
    try {
      const r = await fetch(`/api/projects/${projectId}/github/commits?limit=50&offset=${commits.length}`);
      if (!r.ok) return;
      const data = (await r.json()) as CommitResponse;
      setCommits((prev) => [...prev, ...data.items]);
      setHasMore(data.has_more);
    } finally {
      setLoading(false);
    }
  }

  if (commits.length === 0) {
    return <p className="muted text-sm">No commits found.</p>;
  }

  return (
    <div>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
            <th style={{ padding: "0.5rem 0" }}>SHA</th>
            <th>Message</th>
            <th>Author</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {commits.map((c) => (
            <tr key={c.id} style={{ borderBottom: "1px solid var(--border)" }}>
              <td style={{ padding: "0.35rem 0" }}>
                <a href={c.html_url} target="_blank" rel="noopener noreferrer">
                  <code>{c.short_sha}</code>
                </a>
              </td>
              <td>{c.message_preview}</td>
              <td>{c.author_name ?? "\u2014"}</td>
              <td><DateDisplay date={c.committed_at} /></td>
            </tr>
          ))}
        </tbody>
      </table>
      {hasMore && (
        <div style={{ marginTop: "1rem", textAlign: "center" }}>
          <button
            className="btn btn-ghost"
            disabled={loading}
            onClick={loadMore}
          >
            {loading ? "Loading\u2026" : "Load more commits"}
          </button>
        </div>
      )}
    </div>
  );
}
