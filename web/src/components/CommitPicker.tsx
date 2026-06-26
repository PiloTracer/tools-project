"use client";

import { useEffect, useRef, useState } from "react";

type CommitRow = {
  id: string;
  sha: string;
  short_sha: string;
  message_preview: string;
  html_url: string;
  committed_at: string;
  author_name: string | null;
  owner: string;
  repo: string;
};

export function CommitPicker({
  projectId,
  onSelect,
  onClose,
}: {
  projectId: string;
  onSelect: (markdown: string, meta: { commit_id: string; sha: string; owner: string; repo: string; html_url: string }) => void;
  onClose: () => void;
}) {
  // The meta object is now consumed by callers — they include it in the
  // activity payload so the backend creates a formal CommitSubjectRef row.
  const [query, setQuery] = useState("");
  const [commits, setCommits] = useState<CommitRow[]>([]);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    if (!query.trim()) {
      const t = setTimeout(() => setCommits([]), 0);
      return () => clearTimeout(t);
    }
    const timer = setTimeout(async () => {
      setBusy(true);
      try {
        const r = await fetch(
          `/api/projects/${projectId}/github/commits?q=${encodeURIComponent(query)}&limit=20`,
        );
        if (r.ok) {
          const data = (await r.json()) as { items: CommitRow[] };
          setCommits(data.items);
        }
      } catch {
        /* ignore */
      }
      setBusy(false);
    }, 250);
    return () => clearTimeout(timer);
  }, [query, projectId]);

  function pick(c: CommitRow) {
    const md = `[\`${c.short_sha}\`](${c.html_url})`;
    onSelect(md, {
      commit_id: c.id,
      sha: c.sha,
      owner: c.owner,
      repo: c.repo,
      html_url: c.html_url,
    });
  }

  return (
    <div
      style={{
        border: "1px solid var(--border)",
        borderRadius: "0.4rem",
        background: "var(--surface)",
        padding: "0.5rem",
        maxWidth: "28rem",
      }}
    >
      <div style={{ display: "flex", gap: "0.4rem", alignItems: "center", marginBottom: "0.4rem" }}>
        <input
          ref={inputRef}
          className="input"
          type="text"
          placeholder="Search commits by SHA or message…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ flex: 1, fontSize: "0.85rem" }}
        />
        <button type="button" className="btn btn-ghost text-sm" onClick={onClose}>
          ✕
        </button>
      </div>
      {busy ? (
        <p className="muted text-sm">Searching…</p>
      ) : commits.length === 0 && query.trim() ? (
        <p className="muted text-sm">No commits found.</p>
      ) : (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, maxHeight: "14rem", overflowY: "auto" }}>
          {commits.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                className="btn btn-ghost text-sm"
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  padding: "0.35rem 0.4rem",
                  borderBottom: "1px solid var(--border)",
                }}
                onClick={() => pick(c)}
              >
                <code style={{ fontSize: "0.8rem" }}>{c.short_sha}</code>
                <span className="muted" style={{ marginLeft: "0.4rem", fontSize: "0.75rem" }}>
                  {c.owner}/{c.repo}
                </span>
                <span style={{ marginLeft: "0.4rem", fontSize: "0.8rem" }}>
                  {c.message_preview.length > 60
                    ? c.message_preview.slice(0, 60) + "…"
                    : c.message_preview}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
