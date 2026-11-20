"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { toast } from "@/components/Toast";
import { WorkTypeBadge } from "@/components/WorkTypeBadge";

export type WorkTypeRow = {
  id: string;
  key: string;
  name: string;
  description: string | null;
  is_default: boolean;
};

export function NewWorkTypeForm({
  projectId,
  canEdit,
}: {
  projectId: string;
  canEdit: boolean;
}) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  if (!canEdit) {
    return <p className="muted text-sm">Viewers cannot add work types.</p>;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const r = await fetch(`/api/projects/${projectId}/work-types`, {
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
        toast(j.detail ?? text, "error");
      } catch {
        toast(text || `Error ${r.status}`, "error");
      }
      return;
    }
    toast("Work type created");
    setName("");
    setDescription("");
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="stack" style={{ gap: "0.65rem", maxWidth: "36rem" }}>
      <label className="stack" style={{ gap: "0.25rem" }}>
        <span className="text-sm muted">Name</span>
        <input className="input" required value={name} onChange={(e) => setName(e.target.value)} />
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
        Add work type
      </button>
    </form>
  );
}

export function WorkTypeList({
  items,
  canDelete,
}: {
  items: WorkTypeRow[];
  canDelete: boolean;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);

  async function remove(row: WorkTypeRow) {
    setBusy(row.id);
    const r = await fetch(`/api/work-types/${row.id}`, { method: "DELETE" });
    setBusy(null);
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
    toast("Work type removed");
    router.refresh();
  }

  if (items.length === 0) {
    return <p className="muted">No work types yet.</p>;
  }

  return (
    <ul className="project-list">
      {items.map((row) => (
        <li key={row.id}>
          <div className="project-row" style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: 0, display: "flex", alignItems: "center", gap: "0.45rem" }}>
                <WorkTypeBadge workType={row} />
                {row.is_default ? <span className="pill pill-muted">default</span> : null}
              </h3>
              <p className="muted text-sm" style={{ margin: "0.25rem 0 0" }}>
                {row.key}
                {row.description ? ` — ${row.description}` : ""}
              </p>
            </div>
            {canDelete && !row.is_default ? (
              <button
                type="button"
                className="btn btn-ghost text-sm"
                disabled={busy === row.id}
                onClick={() => remove(row)}
              >
                Remove
              </button>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}
