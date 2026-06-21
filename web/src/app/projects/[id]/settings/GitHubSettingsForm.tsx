"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { toast } from "@/components/Toast";

type LinkRow = {
  id: string;
  owner: string;
  repo: string;
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
                {l.owner}/{l.repo}
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
    const r = await fetch(
      `/api/projects/${projectId}/github/links?link_id=${linkId}`,
      { method: "DELETE" },
    );
    if (!r.ok) {
      const text = await r.text();
      try {
        const j = JSON.parse(text) as { detail?: string };
        toast(j.detail ?? text, "error");
      } catch {
        toast(text || `Error ${r.status}`, "error");
      }
      return;
    }
    setLinks((prev) => prev.filter((l) => l.id !== linkId));
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
                </td>
                <td suppressHydrationWarning>
                  {l.last_synced_at
                    ? new Date(l.last_synced_at).toLocaleString()
                    : "—"}
                </td>
                <td>
                  <button
                    className="btn btn-ghost"
                    style={{ color: "var(--danger, #c33)", fontSize: "0.85rem" }}
                    onClick={() => handleRemove(l.id)}
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
    </div>
  );
}
