"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { toast } from "@/components/Toast";

export function ClientTaskCreateForm({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const t = title.trim();
    if (!t) return;
    setBusy(true);
    const r = await fetch(`/api/me/client/projects/${projectId}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: t, description: description.trim() || null }),
    });
    setBusy(false);
    if (r.ok) {
      setTitle("");
      setDescription("");
      toast("Task created");
      router.refresh();
    } else {
      const text = await r.text();
      try {
        const j = JSON.parse(text) as Record<string, unknown>;
        const d = j.detail;
        toast(Array.isArray(d) ? d.map((e: Record<string, unknown>) => e.msg ?? e.type).join("; ") : (typeof d === "string" ? d : text), "error");
      } catch {
        toast(text || `Error ${r.status}`, "error");
      }
    }
  }

  return (
    <section className="card stack">
      <h2 style={{ marginTop: 0 }}>Create task</h2>
      <form onSubmit={onSubmit} className="stack" style={{ gap: "0.5rem" }}>
        <input
          className="input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Task title"
          required
          autoComplete="off"
        />
        <textarea
          className="input"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description (optional)"
          rows={2}
          style={{ resize: "vertical" }}
        />
        <div>
          <button type="submit" className="btn btn-primary" disabled={busy || !title.trim()}>
            {busy ? "Creating…" : "Create task"}
          </button>
        </div>
      </form>
    </section>
  );
}
