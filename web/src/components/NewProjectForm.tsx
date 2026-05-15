"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function NewProjectForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      const body: { name: string; description?: string; slug?: string } = {
        name: name.trim(),
      };
      const d = description.trim();
      if (d) body.description = d;
      const s = slug.trim();
      if (s) body.slug = s;
      const r = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const j = (await r.json().catch(() => ({}))) as { detail?: string | unknown };
        const detail =
          typeof j.detail === "string"
            ? j.detail
            : r.status === 422
              ? "Check slug format (lowercase letters, numbers, hyphens only)."
              : `Save failed (${r.status})`;
        setError(detail);
        setPending(false);
        return;
      }
      const created = (await r.json()) as { id: string };
      router.replace(`/projects/${created.id}`);
      router.refresh();
    } catch {
      setError("Network error");
      setPending(false);
    }
  }

  return (
    <form className="stack" onSubmit={onSubmit}>
      {error ? (
        <p className="err" role="alert">
          {error}
        </p>
      ) : null}
      <label className="field">
        <span className="label">Name</span>
        <input
          className="input"
          name="name"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Customer portal redesign"
        />
      </label>
      <label className="field">
        <span className="label">Slug (optional)</span>
        <input
          className="input"
          name="slug"
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
          placeholder="portal-redesign"
          pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$"
        />
      </label>
      <label className="field">
        <span className="label">Description</span>
        <textarea
          className="input"
          name="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What this project is for…"
        />
      </label>
      <p className="stack" style={{ marginTop: "1rem" }}>
        <button type="submit" className="btn btn-primary" disabled={pending}>
          {pending ? "Creating…" : "Create project"}
        </button>
      </p>
    </form>
  );
}
