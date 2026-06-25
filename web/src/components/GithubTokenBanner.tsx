"use client";

import { useEffect, useState } from "react";

import { useRouter } from "next/navigation";

type LinkHealth = {
  link_id: string;
  owner: string;
  repo: string;
  ok: boolean;
  error?: string;
  info?: string;
};

export function GithubTokenBanner({ projectId }: { projectId: string }) {
  const [links, setLinks] = useState<LinkHealth[] | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [checking, setChecking] = useState(false);
  const router = useRouter();

  async function check(refresh = false) {
    setChecking(true);
    try {
      const r = await fetch(
        `/api/projects/${projectId}/github/token-health${refresh ? "?refresh=true" : ""}`,
      );
      if (r.ok) {
        const d = await r.json() as { links: LinkHealth[] };
        setLinks(d.links);
      }
    } catch { /* ignore */ }
    setChecking(false);
  }

  useEffect(() => {
    let cancelled = false;
    setDismissed(false);
    check().then(() => { if (cancelled) return; });
    return () => { cancelled = true; };
  }, [projectId]);

  const badLinks = (links ?? []).filter((l) => !l.ok);
  if (!links || badLinks.length === 0 || dismissed || checking) return null;

  return (
    <div
      style={{
        padding: "0.5rem 1rem",
        background: "var(--surface-warn, #fff3cd)",
        borderBottom: "1px solid var(--border-warn, #f0c36d)",
        display: "flex",
        alignItems: "center",
        gap: "0.75rem",
        flexWrap: "wrap",
        fontSize: "0.85rem",
      }}
    >
      <span style={{ fontWeight: 600, whiteSpace: "nowrap" }}>⚠ GitHub token issue</span>
      <span>
        {badLinks.length === 1
          ? `${badLinks[0].owner}/${badLinks[0].repo}: ${badLinks[0].error ?? "invalid token"}`
          : `${badLinks.length} linked ${badLinks.length === 1 ? "repo has" : "repos have"} token issues`}
      </span>
      <div style={{ marginLeft: "auto", display: "flex", gap: "0.5rem" }}>
        <button
          type="button"
          className="btn btn-ghost text-sm"
          style={{ padding: "0.15rem 0.5rem" }}
          onClick={() => router.push(`/projects/${projectId}/settings`)}
        >
          Fix in settings
        </button>
        <button
          type="button"
          className="btn btn-ghost text-sm"
          style={{ padding: "0.15rem 0.5rem" }}
          onClick={() => check(true)}
          disabled={checking}
        >
          {checking ? "Checking…" : "Re-check"}
        </button>
        <button
          type="button"
          className="btn btn-ghost text-sm"
          style={{ padding: "0.15rem 0.5rem", color: "var(--muted)" }}
          onClick={() => setDismissed(true)}
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
