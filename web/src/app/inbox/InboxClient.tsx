"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { MarkdownEditor } from "@/components/MarkdownEditor";
import { toast } from "@/components/Toast";

type InboxItem = {
  id: string;
  body_md: string;
  triaged_to_type: string | null;
  triaged_to_id: string | null;
  created_at: string;
};

type ProjectItem = {
  id: string;
  name: string;
};

export function InboxClient({
  initialItems,
  projects,
}: {
  initialItems: InboxItem[];
  projects: ProjectItem[];
}) {
  const router = useRouter();
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [busyItem, setBusyItem] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const c = body.trim();
    if (!c) return;
    setBusy(true);
    try {
      const r = await fetch("/api/inbox", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body_md: c }),
      });
      if (!r.ok) {
        const t = await r.text();
        try {
          const j = JSON.parse(t) as { detail?: string };
          toast(j.detail ?? t, "error");
        } catch {
          toast(t, "error");
        }
        return;
      }
      setBody("");
      toast("Captured");
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  async function triage(itemId: string, into: "task" | "ticket", projectId: string) {
    setBusyItem(itemId);
    const r = await fetch(`/api/inbox/${itemId}/triage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ into, project_id: projectId }),
    });
    setBusyItem(null);
    if (r.ok) {
      toast("Triaged");
      router.refresh();
    } else {
      const t = await r.text();
      try {
        toast(JSON.parse(t).detail ?? t, "error");
      } catch {
        toast(t || "Triage failed", "error");
      }
    }
  }

  async function removeItem(itemId: string) {
    setBusyItem(itemId);
    await fetch(`/api/inbox/${itemId}`, { method: "DELETE" });
    setBusyItem(null);
    router.refresh();
  }

  return (
    <>
      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Capture</h2>
        <form onSubmit={onSubmit} className="stack" style={{ gap: "0.5rem" }}>
          <MarkdownEditor
            value={body}
            onChange={setBody}
            rows={3}
            placeholder="Jot down a thought, idea, or task…"
          />
          <div>
            <button type="submit" className="btn btn-primary" disabled={busy || !body.trim()}>
              {busy ? "Saving…" : "Capture"}
            </button>
          </div>
        </form>
      </div>

      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Pending ({initialItems.length})</h2>
        {initialItems.length === 0 ? (
          <p className="muted text-sm">Inbox empty. Type something above to start.</p>
        ) : (
          <ul className="stack" style={{ listStyle: "none", padding: 0, gap: "0.75rem" }}>
            {initialItems.map((item) => (
              <li key={item.id} className="card" style={{ padding: "0.75rem 1rem" }}>
                <div className="text-sm muted" style={{ marginBottom: "0.35rem" }} suppressHydrationWarning>
                  {new Date(item.created_at).toLocaleString()}
                </div>
                <p style={{ whiteSpace: "pre-wrap", margin: "0 0 0.5rem" }}>{item.body_md}</p>
                {item.triaged_to_type ? (
                  <span className="pill pill-ok" style={{ fontSize: "0.65rem" }}>
                    Triaged as {item.triaged_to_type}
                  </span>
                ) : (
                  <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
                    <select
                      className="input text-sm"
                      style={{ padding: "0.2rem 0.35rem", minHeight: 0 }}
                      id={`triage-prj-${item.id}`}
                    >
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      className="btn btn-primary text-sm"
                      style={{ padding: "0.25rem 0.65rem" }}
                      disabled={busyItem === item.id}
                      onClick={() =>
                        triage(
                          item.id,
                          "task",
                          (document.getElementById(`triage-prj-${item.id}`) as HTMLSelectElement).value,
                        )
                      }
                    >
                      → Task
                    </button>
                    <button
                      type="button"
                      className="btn text-sm"
                      style={{ padding: "0.25rem 0.65rem", background: "var(--accent)", color: "var(--on-accent, #fff)" }}
                      disabled={busyItem === item.id}
                      onClick={() =>
                        triage(
                          item.id,
                          "ticket",
                          (document.getElementById(`triage-prj-${item.id}`) as HTMLSelectElement).value,
                        )
                      }
                    >
                      → Ticket
                    </button>
                    <button
                      type="button"
                      className="btn btn-ghost text-sm"
                      disabled={busyItem === item.id}
                      onClick={() => removeItem(item.id)}
                    >
                      Delete
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}
