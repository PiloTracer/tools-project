"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function NewComponentForm({
  projectId,
  canEdit,
}: {
  projectId: string;
  canEdit: boolean;
}) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  if (!canEdit) {
    return <p className="muted text-sm">Viewers cannot create components.</p>;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    const r = await fetch(`/api/projects/${projectId}/components`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name.trim(),
        description: description.trim() || null,
      }),
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
    setName("");
    setDescription("");
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="stack" style={{ gap: "0.65rem", maxWidth: "36rem" }}>
      <label className="stack" style={{ gap: "0.25rem" }}>
        <span className="text-sm muted">Name</span>
        <input
          className="input"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
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
      <button type="submit" className="btn btn-primary">
        Create component
      </button>
      {msg ? <p className="err text-sm">{msg}</p> : null}
    </form>
  );
}
