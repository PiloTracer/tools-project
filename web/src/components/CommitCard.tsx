"use client";

import { useState } from "react";

type CommitMeta = {
  sha: string;
  owner: string;
  repo: string;
  html_url: string;
  message_preview: string;
  full_message?: string;
};

export function CommitCard({ meta }: { meta: CommitMeta }) {
  const [showFull, setShowFull] = useState(false);
  const hasMore = !!(meta.full_message && meta.full_message.length > 100);

  return (
    <div style={{ margin: "0.35rem 0 0" }}>
      <a
        href={meta.html_url}
        target="_blank"
        rel="noopener noreferrer"
        style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}
      >
        <code style={{ fontSize: "0.85rem" }}>{meta.sha.slice(0, 7)}</code>
      </a>
      <span className="muted" style={{ fontSize: "0.8rem", marginLeft: "0.5rem" }}>
        {meta.owner}/{meta.repo}
      </span>
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
    </div>
  );
}

export function extractCommitMeta(
  meta_json: Record<string, unknown> | null,
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
  };
}