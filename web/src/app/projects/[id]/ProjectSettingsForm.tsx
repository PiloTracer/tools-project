"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function ProjectSettingsForm({
  projectId,
  initialName,
  initialDescription,
  initialStatus,
  initialProjectKey,
  canEdit,
}: {
  projectId: string;
  initialName: string;
  initialDescription: string;
  initialStatus: string;
  initialProjectKey: string;
  canEdit: boolean;
}) {
  const router = useRouter();
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription);
  const [status, setStatus] = useState(initialStatus);
  const [projectKey, setProjectKey] = useState(initialProjectKey);
  const [msg, setMsg] = useState<string | null>(null);

  if (!canEdit) {
    return (
      <p className="muted text-sm">
        Only owners and maintainers can change project settings (archive, key, name).
      </p>
    );
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    const body = {
      name: name.trim(),
      description: description.trim() || null,
      status,
      project_key: projectKey.trim() || null,
    };
    const r = await fetch(`/api/projects/${projectId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const text = await r.text();
    if (!r.ok) {
      try {
        const j = JSON.parse(text) as { detail?: string };
        setMsg(j.detail ?? text);
      } catch {
        setMsg(text || `Error ${r.status}`);
      }
      return;
    }
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="stack" style={{ gap: "0.65rem", maxWidth: "36rem" }}>
      <h2 style={{ margin: 0 }}>Settings</h2>
      <label className="stack" style={{ gap: "0.25rem" }}>
        <span className="text-sm muted">Name</span>
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
      </label>
      <label className="stack" style={{ gap: "0.25rem" }}>
        <span className="text-sm muted">Description</span>
        <textarea
          className="input"
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </label>
      <label className="stack" style={{ gap: "0.25rem" }}>
        <span className="text-sm muted">Status</span>
        <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="active">active</option>
          <option value="archived">archived</option>
        </select>
      </label>
      <label className="stack" style={{ gap: "0.25rem" }}>
        <span className="text-sm muted">Project key (optional display ref)</span>
        <input
          className="input"
          value={projectKey}
          onChange={(e) => setProjectKey(e.target.value)}
          placeholder="e.g. PRJ-A"
          pattern="[A-Za-z0-9_-]*"
        />
      </label>
      <button type="submit" className="btn btn-primary">
        Save settings
      </button>
      {msg ? <p className="err text-sm">{msg}</p> : null}
    </form>
  );
}
