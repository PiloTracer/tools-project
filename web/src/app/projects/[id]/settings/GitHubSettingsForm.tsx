"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Dialog } from "@/components/Dialog";
import { SyncNowButton } from "@/components/SyncNowButton";
import { SyncStatusBadge } from "@/components/SyncStatusBadge";
import { toast } from "@/components/Toast";
import { apiRequest } from "@/shared/client/api";

type LinkRow = {
  id: string;
  owner: string;
  repo: string;
  sync_status: string;
  last_error: string | null;
  last_error_at: string | null;
  error_count: number;
  last_synced_at: string | null;
};

export function GitHubSettingsForm({
  projectId,
  links: initialLinks,
  canEdit,
}: {
  projectId: string;
  links: LinkRow[];
  canEdit: boolean;
}) {
  const router = useRouter();
  const [links, setLinks] = useState<LinkRow[]>(initialLinks);
  const [repoUrl, setRepoUrl] = useState("");
  const [pat, setPat] = useState("");
  const [removeLinkId, setRemoveLinkId] = useState<string | null>(null);

  if (!canEdit) {
    return (
      <div>
        <h2 style={{ marginTop: 0 }}>GitHub Repositories</h2>
        <p className="muted text-sm">
          Only owners and maintainers can manage GitHub repository links.
        </p>
        {links.length > 0 && (
          <ul style={{ marginTop: "0.5rem" }}>
            {links.map((l) => (
              <li key={l.id}>
                {l.owner}/{l.repo} <SyncStatusBadge status={l.sync_status} error={l.last_error} errorCount={l.error_count} />
                {l.last_error && <span className="muted text-sm" style={{ marginLeft: "0.35rem" }}>— {l.last_error}</span>}
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    const body = {
      github_repo_url: repoUrl.trim(),
      github_token: pat.trim(),
    };
    const r = await fetch(`/api/projects/${projectId}/github/links`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const text = await r.text();
    if (!r.ok) {
      try {
        const j = JSON.parse(text) as { detail?: string };
        toast(j.detail ?? text, "error");
      } catch {
        toast(text || `Error ${r.status}`, "error");
      }
      return;
    }
    let newLink: LinkRow | null = null;
    try {
      newLink = JSON.parse(text) as LinkRow;
    } catch { /* ignore */ }
    setRepoUrl("");
    setPat("");
    if (newLink) {
      setLinks((prev) => [newLink!, ...prev]);
    }
    toast("Repository linked");
    router.refresh();
  }

  async function handleRemove(linkId: string) {
    const r = await apiRequest(
      `/api/projects/${projectId}/github/links?link_id=${linkId}`,
      { method: "DELETE" },
    );
    if (!r.ok) { toast(r.error, "error"); return; }
    setLinks((prev) => prev.filter((l) => l.id !== linkId));
    setRemoveLinkId(null);
    toast("Repository removed");
    router.refresh();
  }

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>GitHub Repositories</h2>

      {links.length > 0 ? (
        <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "1rem" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
              <th style={{ padding: "0.5rem 0" }}>Repository</th>
              <th>Status</th>
              <th>Last synced</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {links.map((l) => (
              <tr key={l.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: "0.35rem 0" }}>
                  <a
                    href={`https://github.com/${l.owner}/${l.repo}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {l.owner}/{l.repo}
                  </a>
                  {l.last_error ? (
                    <div style={{ fontSize: "0.72rem", color: "var(--danger)", marginTop: "0.15rem" }}>
                      {l.last_error.length > 100 ? l.last_error.slice(0, 100) + "…" : l.last_error}
                    </div>
                  ) : null}
                </td>
                <td><SyncStatusBadge status={l.sync_status} error={l.last_error} errorCount={l.error_count} /></td>
                <td suppressHydrationWarning>
                  {l.last_synced_at
                    ? new Date(l.last_synced_at).toLocaleString()
                    : "—"}
                </td>
                <td style={{ display: "flex", gap: "0.3rem", alignItems: "center" }}>
                  <SyncNowButton projectId={projectId} linkId={l.id} />
                  <button
                    className="btn btn-ghost"
                    style={{ color: "var(--danger, #c33)", fontSize: "0.72rem" }}
                    onClick={() => setRemoveLinkId(l.id)}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="muted text-sm">No repositories linked yet.</p>
      )}

      <form
        onSubmit={handleAdd}
        className="stack"
        style={{ gap: "0.65rem", maxWidth: "36rem" }}
      >
        <label className="stack" style={{ gap: "0.25rem" }}>
          <span className="text-sm muted">GitHub repo URL</span>
          <input
            className="input"
            required
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
          />
        </label>
        <label className="stack" style={{ gap: "0.25rem" }}>
          <span className="text-sm muted">
            Personal Access Token (classic, with repo scope)
          </span>
          <input
            className="input"
            type="password"
            required
            value={pat}
            onChange={(e) => setPat(e.target.value)}
            placeholder="ghp_…"
          />
        </label>
        <button type="submit" className="btn btn-primary">
          Link repository
        </button>
      </form>

      <Dialog
        open={removeLinkId !== null}
        onClose={() => setRemoveLinkId(null)}
        title="Remove repository"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setRemoveLinkId(null)}>Cancel</button>
            <button
              type="button"
              className="btn btn-primary"
              style={{ background: "var(--danger)", color: "var(--text)", boxShadow: "none" }}
              onClick={() => removeLinkId && handleRemove(removeLinkId)}
            >
              Remove
            </button>
          </>
        }
      >
        <p className="text-sm">Remove this GitHub repository link? Commit data will no longer sync.</p>
      </Dialog>
    </div>
  );
}
