"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { MarkdownEditor } from "@/components/MarkdownEditor";
import { usePendingImages } from "@/shared/client/use-pending-images";
import { toast } from "@/components/Toast";

export function ProjectSettingsForm({
  projectId,
  initialName,
  initialDescription,
  initialStatus,
  initialProjectKey,
  initialRegistryEnabled,
  initialAutoPrefix,
  canEdit,
}: {
  projectId: string;
  initialName: string;
  initialDescription: string;
  initialStatus: string;
  initialProjectKey: string;
  initialRegistryEnabled: boolean;
  initialAutoPrefix: boolean;
  canEdit: boolean;
}) {
  const router = useRouter();
  const { pending, addFiles, remove, clear } = usePendingImages();
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription);
  const [status, setStatus] = useState(initialStatus);
  const [projectKey, setProjectKey] = useState(initialProjectKey);
  const [registryEnabled, setRegistryEnabled] = useState(initialRegistryEnabled);
  const [autoPrefix, setAutoPrefix] = useState(initialAutoPrefix);
  if (!canEdit) {
    return (
      <p className="muted text-sm">
        Only owners and maintainers can change project settings (archive, key, name).
      </p>
    );
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();

    let descVal = description.trim() || null;
    if (pending.length) {
      const uploadedIds: string[] = [];
      for (const p of pending) {
        const fd = new FormData();
        fd.append("file", p.file);
        const ur = await fetch(`/api/projects/${projectId}/attachments`, {
          method: "POST",
          body: fd,
        });
        const ut = await ur.text();
        if (!ur.ok) {
          try { const j = JSON.parse(ut) as { detail?: string }; toast(j.detail ?? ut, "error"); }
          catch { toast(ut || `Upload failed (${ur.status})`, "error"); }
          return;
        }
        let row: { id: string };
        try {
          row = JSON.parse(ut) as { id: string };
        } catch {
          toast("Unexpected response from upload", "error");
          return;
        }
        uploadedIds.push(row.id);
      }
      const mdLines = uploadedIds.map((aid, i) => {
        const f = pending[i]?.file;
        if (f?.type.startsWith("image/")) {
          return `![${f.name.replace(/]/g, "")}](/api/attachments/${aid})`;
        }
        return `[${(f?.name ?? "attachment").replace(/]/g, "")}](/api/attachments/${aid})`;
      });
      const md = mdLines.join("\n");
      descVal = descVal ? `${descVal}\n\n${md}` : md;
      clear();
    }

    const body = {
      name: name.trim(),
      description: descVal,
      status,
      project_key: projectKey.trim() || null,
      github_task_registry_enabled: registryEnabled,
      auto_prefix_enabled: autoPrefix,
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
        toast(j.detail ?? text, "error");
      } catch {
        toast(text || `Error ${r.status}`, "error");
      }
      return;
    }
    toast("Settings saved");
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
        <MarkdownEditor
          value={description}
          onChange={setDescription}
          rows={3}
          placeholder="Project description, goals, context…"
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
        {pending.length > 0 ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "flex-start" }}>
            {pending.map((p) => (
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
      <label className="stack" style={{ gap: "0.25rem" }}>
        <span className="text-sm muted">Status</span>
        <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="active">active</option>
          <option value="archived">archived</option>
        </select>
      </label>
      <label className="stack" style={{ gap: "0.25rem" }}>
        <span className="text-sm muted">Project key (display ref for tasks/tickets)</span>
        <input
          className="input"
          value={projectKey}
          onChange={(e) => setProjectKey(e.target.value)}
          placeholder="e.g. PROJ"
          pattern="[A-Za-z0-9_-]*"
        />
      </label>

      <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "0.5rem 0" }} />

      <h3 style={{ margin: 0 }}>Commit Association</h3>
      <p className="text-sm muted" style={{ margin: 0 }}>
        When enabled, tasks and tickets get auto-generated refs (e.g. PROJ-123) and
        commits matching those refs are automatically linked.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", padding: "0.5rem 0" }}>
        <label
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.6rem",
            cursor: "pointer",
            padding: "0.5rem 0.65rem",
            border: "1px solid var(--border)",
            borderRadius: "0.4rem",
            background: registryEnabled ? "var(--surface-hover)" : "transparent",
          }}
        >
          <input
            type="checkbox"
            checked={registryEnabled}
            onChange={(e) => setRegistryEnabled(e.target.checked)}
            style={{ width: "1.1rem", height: "1.1rem", cursor: "pointer", flexShrink: 0 }}
          />
          <div className="stack" style={{ gap: "0.15rem" }}>
            <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>GitHub task registry</span>
            <span className="text-sm muted">
              Push task/ticket refs to linked GitHub repo so the AI can discover them
            </span>
          </div>
        </label>

        <label
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.6rem",
            cursor: "pointer",
            padding: "0.5rem 0.65rem",
            border: "1px solid var(--border)",
            borderRadius: "0.4rem",
            background: autoPrefix ? "var(--surface-hover)" : "transparent",
          }}
        >
          <input
            type="checkbox"
            checked={autoPrefix}
            onChange={(e) => setAutoPrefix(e.target.checked)}
            style={{ width: "1.1rem", height: "1.1rem", cursor: "pointer", flexShrink: 0 }}
          />
          <div className="stack" style={{ gap: "0.15rem" }}>
            <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>Auto-prefix task/ticket refs</span>
            <span className="text-sm muted">
              Automatically assign refs (e.g. PROJ-123) to new tasks and tickets
            </span>
          </div>
        </label>
      </div>

      <button type="submit" className="btn btn-primary">
        Save settings
      </button>
    </form>
  );
}
