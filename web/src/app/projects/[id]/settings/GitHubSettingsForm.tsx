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
  poll_interval_seconds: number;
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
  const [editingPoll, setEditingPoll] = useState<string | null>(null);
  const [pollValue, setPollValue] = useState("300");
  const [editingToken, setEditingToken] = useState<string | null>(null);
  const [tokenValue, setTokenValue] = useState("");

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

  async function handleUpdateToken(linkId: string) {
    if (!tokenValue.trim()) {
      toast("Token is required", "error");
      return;
    }
    const r = await fetch(`/api/projects/${projectId}/github/links?link_id=${linkId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ github_token: tokenValue.trim() }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Update failed" }));
      toast(err.detail, "error");
      return;
    }
    setEditingToken(null);
    setTokenValue("");
    toast("Token updated");
    router.refresh();
  }

  async function handleSavePoll(linkId: string) {
    const val = parseInt(pollValue, 10);
    if (isNaN(val) || val < 60 || val > 86400) {
      toast("Poll interval must be between 60 and 86400 seconds", "error");
      return;
    }
    const r = await apiRequest(
      `/api/projects/${projectId}/github/links?link_id=${linkId}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ poll_interval_seconds: val }),
      },
    );
    if (!r.ok) { toast(r.error, "error"); return; }
    setLinks((prev) =>
      prev.map((l) => (l.id === linkId ? { ...l, poll_interval_seconds: val } : l)),
    );
    setEditingPoll(null);
    toast("Poll interval updated");
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
              <th>Poll interval</th>
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
                <td>
                  {editingPoll === l.id ? (
                    <span style={{ display: "flex", gap: "0.2rem", alignItems: "center" }}>
                      <input
                        className="input"
                        type="number"
                        min={60}
                        max={86400}
                        value={pollValue}
                        onChange={(e) => setPollValue(e.target.value)}
                        style={{ width: "5rem", fontSize: "0.72rem", padding: "0.15rem 0.3rem" }}
                      />
                      <span className="text-sm muted">s</span>
                      <button
                        className="btn btn-ghost"
                        style={{ fontSize: "0.72rem" }}
                        onClick={() => handleSavePoll(l.id)}
                      >
                        Save
                      </button>
                      <button
                        className="btn btn-ghost"
                        style={{ fontSize: "0.72rem" }}
                        onClick={() => setEditingPoll(null)}
                      >
                        Cancel
                      </button>
                    </span>
                  ) : (
                    <span
                      style={{ cursor: "pointer", fontSize: "0.85rem" }}
                      onClick={() => {
                        setPollValue(String(l.poll_interval_seconds));
                        setEditingPoll(l.id);
                      }}
                      title="Click to edit poll interval"
                    >
                      {l.poll_interval_seconds}s
                    </span>
                  )}
                </td>
                <td suppressHydrationWarning>
                  {l.last_synced_at
                    ? new Date(l.last_synced_at).toLocaleString()
                    : "—"}
                </td>
                <td>
                  <div style={{ display: "flex", gap: "0.3rem", alignItems: "center", flexWrap: "wrap" }}>
                    <SyncNowButton projectId={projectId} linkId={l.id} />
                    {editingToken === l.id ? (
                      <span style={{ display: "flex", gap: "0.2rem", alignItems: "center" }}>
                        <input
                          className="input"
                          type="password"
                          value={tokenValue}
                          onChange={(e) => setTokenValue(e.target.value)}
                          placeholder="New PAT"
                          style={{ width: "10rem", fontSize: "0.72rem", padding: "0.15rem 0.3rem" }}
                        />
                        <button
                          className="btn btn-ghost"
                          style={{ fontSize: "0.72rem" }}
                          onClick={() => handleUpdateToken(l.id)}
                        >
                          Save
                        </button>
                        <button
                          className="btn btn-ghost"
                          style={{ fontSize: "0.72rem" }}
                          onClick={() => { setEditingToken(null); setTokenValue(""); }}
                        >
                          Cancel
                        </button>
                      </span>
                    ) : (
                      <button
                        className="btn btn-ghost"
                        style={{ fontSize: "0.72rem" }}
                        onClick={() => { setEditingToken(l.id); setTokenValue(""); }}
                      >
                        Update token
                      </button>
                    )}
                    <button
                      className="btn btn-ghost"
                      style={{ color: "var(--danger, #c33)", fontSize: "0.72rem" }}
                      onClick={() => setRemoveLinkId(l.id)}
                    >
                      Remove
                    </button>
                  </div>
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
