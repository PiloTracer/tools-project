"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "@/components/Toast";
import { Dialog } from "@/components/Dialog";

type KeyRow = {
  id: string;
  user_id: string;
  key_prefix: string;
  label: string | null;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
};

type KeySecret = KeyRow & { plaintext: string };

export function ApiKeysPanel({ initialKeys }: { initialKeys: KeyRow[] }) {
  const router = useRouter();
  const [keys, setKeys] = useState<KeyRow[]>(initialKeys);
  const [creating, setCreating] = useState(false);
  const [newLabel, setNewLabel] = useState("");
  const [secret, setSecret] = useState<KeySecret | null>(null);
  const [revokeId, setRevokeId] = useState<string | null>(null);

  async function refreshKeys() {
    const r = await fetch("/api/me/api-keys", { cache: "no-store" });
    if (r.ok) {
      const data = await r.json();
      setKeys(data.items ?? []);
    }
    router.refresh();
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const body: Record<string, string> = {};
    const trimmed = newLabel.trim();
    if (trimmed) body.label = trimmed;

    const r = await fetch("/api/me/api-keys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const t = await r.text();
      try {
        toast(JSON.parse(t).detail ?? t, "error");
      } catch {
        toast(t || "Failed to create key", "error");
      }
      return;
    }
    const created: KeySecret = await r.json();
    setSecret(created);
    setCreating(false);
    setNewLabel("");
    await refreshKeys();
  }

  async function handleRevoke() {
    if (!revokeId) return;
    const r = await fetch(`/api/me/api-keys/${encodeURIComponent(revokeId)}`, {
      method: "DELETE",
    });
    if (!r.ok) {
      toast("Failed to revoke key", "error");
      return;
    }
    toast("Key revoked");
    setRevokeId(null);
    await refreshKeys();
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text).then(
      () => toast("Copied to clipboard"),
      () => toast("Copy failed", "error")
    );
  }

  function formatDate(iso: string | null) {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  return (
    <div className="stack-lg" style={{ maxWidth: "48rem" }}>
      {/* Secret display — shown once after creation */}
      {secret && (
        <div
          className="card wide stack"
          style={{
            gap: "0.5rem",
            border: "1px solid var(--accent-success)",
          }}
        >
          <h3 style={{ margin: 0, color: "var(--accent-success)" }}>
            Key created — copy it now
          </h3>
          <p className="text-sm">
            This is the only time the full key is shown. If you lose it, you
            will need to create a new one.
          </p>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <code
              className="input"
              style={{
                flex: 1,
                fontFamily: "var(--font-mono, monospace)",
                fontSize: "0.8125rem",
                padding: "0.5rem 0.75rem",
                userSelect: "all",
                wordBreak: "break-all",
              }}
            >
              {secret.plaintext}
            </code>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => copyToClipboard(secret.plaintext)}
            >
              Copy
            </button>
          </div>
          <p className="text-sm muted">
            Label: {secret.label || "—"} · Prefix: {secret.key_prefix}
          </p>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => setSecret(null)}
          >
            Close
          </button>
        </div>
      )}

      {/* Key list */}
      <div className="card wide stack" style={{ gap: "0.5rem" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h2 style={{ margin: 0 }}>Your keys</h2>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setCreating(true)}
          >
            + New key
          </button>
        </div>

        {keys.length === 0 ? (
          <p className="text-sm muted" style={{ marginTop: "1rem" }}>
            No API keys yet. Create one to let coding agents query your projects.
          </p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr
                className="text-sm muted"
                style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}
              >
                <th style={{ padding: "0.5rem 0" }}>Prefix</th>
                <th style={{ padding: "0.5rem 0" }}>Label</th>
                <th style={{ padding: "0.5rem 0" }}>Created</th>
                <th style={{ padding: "0.5rem 0" }}>Last used</th>
                <th style={{ padding: "0.5rem 0" }} />
              </tr>
            </thead>
            <tbody>
              {keys.map((k) => (
                <tr
                  key={k.id}
                  style={{ borderBottom: "1px solid var(--border)" }}
                >
                  <td style={{ padding: "0.5rem 0" }}>
                    <code
                      style={{
                        fontFamily: "var(--font-mono, monospace)",
                        fontSize: "0.8125rem",
                      }}
                    >
                      {k.key_prefix}...
                    </code>
                  </td>
                  <td style={{ padding: "0.5rem 0" }}>{k.label || "—"}</td>
                  <td style={{ padding: "0.5rem 0" }}>
                    {formatDate(k.created_at)}
                  </td>
                  <td style={{ padding: "0.5rem 0" }}>
                    <span className="text-sm muted">
                      {formatDate(k.last_used_at)}
                    </span>
                  </td>
                  <td style={{ padding: "0.5rem 0", textAlign: "right" }}>
                    <button
                      type="button"
                      className="btn btn-ghost"
                      style={{ color: "var(--accent-danger)" }}
                      onClick={() => setRevokeId(k.id)}
                    >
                      Revoke
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create dialog */}
      <Dialog
        open={creating}
        onClose={() => setCreating(false)}
        title="Create API key"
      >
        <form
          onSubmit={handleCreate}
          className="stack"
          style={{ gap: "0.75rem" }}
        >
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span className="text-sm muted">Label (optional)</span>
            <input
              className="input"
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
              placeholder="e.g. My laptop, CI/CD"
              maxLength={100}
            />
          </label>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button type="submit" className="btn btn-primary">
              Create
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setCreating(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      </Dialog>

      {/* Revoke confirmation */}
      <Dialog
        open={revokeId !== null}
        onClose={() => setRevokeId(null)}
        title="Revoke API key"
        actions={
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setRevokeId(null)}
            >
              Cancel
            </button>
            <button type="button" className="btn btn-primary" onClick={handleRevoke}>
              Revoke
            </button>
          </div>
        }
      >
        <p className="text-sm">
          This key will stop working immediately. Any agent using it will need a
          new key. This cannot be undone.
        </p>
      </Dialog>
    </div>
  );
}
