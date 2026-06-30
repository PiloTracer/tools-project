"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { MarkdownEditor } from "@/components/MarkdownEditor";
import { usePendingImages } from "@/shared/client/use-pending-images";

export function NewProjectForm() {
  const router = useRouter();
  const { pending: filePending, addFiles, remove, clear: clearFiles } = usePendingImages();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
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
        setBusy(false);
        return;
      }
      const created = (await r.json()) as { id: string };

      let descVal = description.trim() || null;
      if (filePending.length) {
        const uploadedIds: string[] = [];
        for (const p of filePending) {
          const fd = new FormData();
          fd.append("file", p.file);
          const ur = await fetch(`/api/projects/${created.id}/attachments`, {
            method: "POST",
            body: fd,
          });
          const ut = await ur.text();
          if (!ur.ok) {
            setBusy(false);
            try { const j = JSON.parse(ut) as { detail?: string }; setError(j.detail ?? ut); }
            catch { setError(ut || `Upload failed (${ur.status})`); }
            return;
          }
          let row: { id: string };
          try {
            row = JSON.parse(ut) as { id: string };
          } catch {
            setError("Unexpected response from upload");
            return;
          }
          uploadedIds.push(row.id);
        }
        const mdLines = uploadedIds.map((aid, i) => {
          const f = filePending[i]?.file;
          if (f?.type.startsWith("image/")) {
            return `![${f.name.replace(/]/g, "")}](/api/attachments/${aid})`;
          }
          return `[${(f?.name ?? "attachment").replace(/]/g, "")}](/api/attachments/${aid})`;
        });
        const md = mdLines.join("\n");
        descVal = descVal ? `${descVal}\n\n${md}` : md;
        clearFiles();

        const pr = await fetch(`/api/projects/${created.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ description: descVal }),
        });
        if (!pr.ok) {
          setBusy(false);
          setError("Project created but attaching files failed");
          return;
        }
      }

      router.replace(`/projects/${created.id}`);
      router.refresh();
    } catch {
      setError("Network error");
      setBusy(false);
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
        <MarkdownEditor
          value={description}
          onChange={setDescription}
          rows={4}
          placeholder="What this project is for…"
          onPasteFiles={(files) => addFiles(files)}
          onDropFiles={(files) => addFiles(files)}
        />
      </label>
      <div className="stack" style={{ gap: "0.35rem" }}>
        <span className="text-sm muted">Attachments — images, PDF, or plain text (optional)</span>
        <label className="btn btn-ghost text-sm" style={{ cursor: "pointer", display: "inline-flex", alignItems: "center", gap: "0.35rem" }}>
          <input
            type="file"
            accept="image/png,image/jpeg,image/gif,image/webp,application/pdf,text/plain,text/csv,.csv,.xls,.xlsx,.ppt,.pptx,.doc,.docx,.odt,.ods,.odp"
            multiple
            style={{ display: "none" }}
            onChange={(e) => {
              const list = e.target.files;
              if (list?.length) addFiles(Array.from(list));
              e.target.value = "";
            }}
          />
          Browse files…
        </label>
        {filePending.length > 0 ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "flex-start" }}>
            {filePending.map((p) => (
              <div key={p.key} style={{ position: "relative" }}>
                {p.url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={p.url} alt="" style={{ width: 72, height: 72, objectFit: "cover", borderRadius: 6, border: "1px solid var(--border)" }} />
                ) : (
                  <div className="text-sm muted" style={{ width: 120, minHeight: 72, padding: "0.35rem", borderRadius: 6, border: "1px solid var(--border)", wordBreak: "break-all" }} title={p.file.name}>
                    {p.file.name}
                  </div>
                )}
                <button type="button" className="btn btn-ghost text-sm" style={{ position: "absolute", top: -6, right: -6, padding: "0 0.35rem", minHeight: 0 }} onClick={() => remove(p.key)} aria-label="Remove attachment">×</button>
              </div>
            ))}
          </div>
        ) : null}
      </div>
      <p className="stack" style={{ marginTop: "1rem" }}>
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? "Creating…" : "Create project"}
        </button>
      </p>
    </form>
  );
}
