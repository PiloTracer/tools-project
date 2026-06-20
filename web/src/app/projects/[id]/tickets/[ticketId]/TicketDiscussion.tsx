"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { MarkdownEditor } from "@/components/MarkdownEditor";
import { usePendingImages } from "@/shared/client/use-pending-images";

async function _searchUsers(prefix: string): Promise<{ label: string; insert: string }[]> {
  const r = await fetch(`/api/me/users/search?q=${encodeURIComponent(prefix)}&limit=8`);
  if (!r.ok) return [];
  const rows = (await r.json()) as { email: string; display_name: string | null }[];
  return rows.map((u) => ({
    label: u.display_name ? `${u.display_name} <${u.email}>` : u.email,
    insert: u.email,
  }));
}

async function _searchRefs(prefix: string): Promise<{ label: string; insert: string }[]> {
  const r = await fetch(`/api/me/refs/search?q=${encodeURIComponent(prefix)}&limit=10`);
  if (!r.ok) return [];
  const rows = (await r.json()) as { ref: string | null; title: string; project_name: string; kind: string }[];
  return rows.map((row) => ({
    label: `${row.ref || row.kind} · ${row.title} (${row.project_name})`,
    insert: row.ref || row.title,
  }));
}

export type ActivityItem = {
  id: string;
  actor_email: string | null;
  body: string;
  created_at: string;
  parent_activity_id: string | null;
  meta_json?: Record<string, unknown> | null;
  is_internal?: boolean;
};

function attachmentIds(meta: Record<string, unknown> | null | undefined): string[] {
  if (meta == null) return [];
  const raw = meta.attachment_ids;
  if (!Array.isArray(raw)) return [];
  return raw.filter((x): x is string => typeof x === "string");
}

function PendingThumbnails({
  pending,
  onRemove,
}: {
  pending: { key: string; url?: string; file: File }[];
  onRemove: (key: string) => void;
}) {
  if (!pending.length) return null;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "flex-start" }}>
      {pending.map((p) => (
        <div key={p.key} style={{ position: "relative" }}>
          {p.url ? (
            <>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={p.url} alt="" style={{ width: 72, height: 72, objectFit: "cover", borderRadius: 6, border: "1px solid var(--border)" }} />
            </>
          ) : (
            <div
              className="text-sm muted"
              style={{
                width: 120,
                minHeight: 72,
                padding: "0.35rem",
                borderRadius: 6,
                border: "1px solid var(--border)",
                wordBreak: "break-all",
              }}
              title={p.file.name}
            >
              {p.file.name}
            </div>
          )}
          <button
            type="button"
            className="btn btn-ghost text-sm"
            style={{ position: "absolute", top: -6, right: -6, padding: "0 0.35rem", minHeight: 0 }}
            onClick={() => onRemove(p.key)}
            aria-label="Remove attachment"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

export function TicketDiscussion({
  projectId,
  ticketId,
  initialItems,
  canEdit,
}: {
  projectId: string;
  ticketId: string;
  initialItems: ActivityItem[];
  canEdit: boolean;
}) {
  const router = useRouter();
  const { pending, addFiles, remove, clear } = usePendingImages();
  const [body, setBody] = useState("");
  const [isInternal, setIsInternal] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [replyToId, setReplyToId] = useState<string | null>(null);

  function buildThreaded(): ActivityItem[] {
    const top: ActivityItem[] = [];
    const replies: Record<string, ActivityItem[]> = {};
    for (const a of initialItems) {
      if (a.parent_activity_id) {
        if (!replies[a.parent_activity_id]) replies[a.parent_activity_id] = [];
        replies[a.parent_activity_id].push(a);
      } else {
        top.push(a);
      }
    }
    return top;
  }

  function getReplies(parentId: string): ActivityItem[] {
    const map: Record<string, ActivityItem[]> = {};
    for (const a of initialItems) {
      if (a.parent_activity_id) {
        if (!map[a.parent_activity_id]) map[a.parent_activity_id] = [];
        map[a.parent_activity_id].push(a);
      }
    }
    return (map[parentId] || []).sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    );
  }

  async function uploadPending(): Promise<string[]> {
    const ids: string[] = [];
    for (const p of pending) {
      const fd = new FormData();
      fd.append("file", p.file);
      const ur = await fetch(`/api/projects/${projectId}/tickets/${ticketId}/attachments`, {
        method: "POST",
        body: fd,
      });
      const ut = await ur.text();
      if (!ur.ok) {
        try {
          const j = JSON.parse(ut) as { detail?: string };
          throw new Error(j.detail ?? ut);
        } catch (e) {
          if (e instanceof Error && e.message !== ut) throw e;
          throw new Error(ut || `Upload failed (${ur.status})`);
        }
      }
      const row = JSON.parse(ut) as { id: string };
      ids.push(row.id);
    }
    return ids;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const caption = body.trim();
    if (!caption && pending.length === 0) return;
    setMsg(null);
    setBusy(true);
    try {
      const uploadedIds = pending.length ? await uploadPending() : [];
      const payload: Record<string, unknown> = {
        subject_type: "ticket",
        subject_id: ticketId,
        kind: "comment",
        body: caption || (uploadedIds.length ? "(image)" : ""),
        is_internal: isInternal,
      };
      if (replyToId) {
        payload.parent_activity_id = replyToId;
      }
      if (uploadedIds.length) {
        payload.meta_json = { attachment_ids: uploadedIds };
      }
      const r = await fetch(`/api/projects/${projectId}/activities`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const t = await r.text();
      if (!r.ok) {
        try {
          const j = JSON.parse(t) as { detail?: string };
          setMsg(j.detail ?? t);
        } catch {
          setMsg(t || `Error ${r.status}`);
        }
        setBusy(false);
        return;
      }
      setBody("");
      setIsInternal(false);
      setReplyToId(null);
      clear();
      router.refresh();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Upload failed");
    }
    setBusy(false);
  }

  return (
    <div className="stack" style={{ gap: "1rem" }}>
      <p className="muted text-sm" style={{ margin: 0 }}>
        Comments are project <strong>activity</strong> entries. Paste or attach images below; they upload when you post.
      </p>
      {initialItems.length === 0 ? (
        <p className="muted text-sm">No comments yet.</p>
      ) : (
        <ul className="stack" style={{ listStyle: "none", margin: 0, padding: 0, gap: "0.75rem" }}>
          {buildThreaded().map((a) => {
            const ids = attachmentIds(a.meta_json);
            const internal = a.is_internal === true;
            const childReplies = getReplies(a.id);
            return (
              <li key={a.id}>
                <div
                  className="card"
                  style={{
                    padding: "0.65rem 0.85rem",
                    background: internal ? "var(--surface-warn, #fff8e1)" : undefined,
                    borderColor: internal ? "var(--border-warn, #f0c36d)" : undefined,
                  }}
                >
                  <div className="muted text-sm" style={{ marginBottom: "0.35rem", display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                    <span suppressHydrationWarning>
                      {(a.actor_email ?? "user") + " · " + new Date(a.created_at).toLocaleString()}
                    </span>
                    {internal ? (
                      <span
                        className="pill"
                        title="Internal note — not customer-visible"
                        style={{ background: "var(--accent-warn, #c98300)", color: "var(--on-accent, #fff)" }}
                      >
                        Internal
                      </span>
                    ) : (
                      <span className="pill pill-muted" title="Customer-visible (external) note">
                        External
                      </span>
                    )}
                  </div>
                  {a.body !== "(image)" ? <div style={{ whiteSpace: "pre-wrap" }}>{a.body}</div> : null}
                  {ids.length > 0 ? (
                    <div className="stack" style={{ gap: "0.5rem", marginTop: a.body !== "(image)" ? "0.5rem" : 0 }}>
                      {ids.map((id) => (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          key={id}
                          src={`/api/attachments/${id}`}
                          alt=""
                          style={{ maxWidth: "min(100%, 720px)", height: "auto", borderRadius: 8 }}
                        />
                      ))}
                    </div>
                  ) : null}
                  {canEdit ? (
                    <button
                      type="button"
                      className="btn btn-ghost text-sm"
                      style={{ marginTop: "0.4rem", padding: "0.15rem 0.5rem" }}
                      onClick={() => setReplyToId(replyToId === a.id ? null : a.id)}
                    >
                      {replyToId === a.id ? "Cancel reply" : "Reply"}
                    </button>
                  ) : null}
                </div>
                {childReplies.length > 0 ? (
                  <ul className="stack" style={{ listStyle: "none", padding: 0, margin: "0.5rem 0 0 1.5rem", gap: "0.5rem", borderLeft: "2px solid var(--border)", paddingLeft: "0.75rem" }}>
                    {childReplies.map((cr) => {
                      const cids = attachmentIds(cr.meta_json);
                      const cinternal = cr.is_internal === true;
                      return (
                        <li key={cr.id}>
                          <div
                            className="card"
                            style={{
                              padding: "0.55rem 0.75rem",
                              background: cinternal ? "var(--surface-warn, #fff8e1)" : undefined,
                              borderColor: cinternal ? "var(--border-warn, #f0c36d)" : undefined,
                            }}
                          >
                            <div className="muted text-sm" style={{ marginBottom: "0.25rem", display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                              <span suppressHydrationWarning>{(cr.actor_email ?? "user") + " · " + new Date(cr.created_at).toLocaleString()}</span>
                              {cinternal ? (
                                <span className="pill" style={{ fontSize: "0.6rem", background: "var(--accent-warn, #c98300)", color: "#fff" }}>
                                  Internal
                                </span>
                              ) : null}
                            </div>
                            {cr.body !== "(image)" ? <div style={{ whiteSpace: "pre-wrap" }}>{cr.body}</div> : null}
                            {cids.length > 0 ? (
                              <div className="stack" style={{ gap: "0.4rem", marginTop: "0.35rem" }}>
                                {cids.map((id) => (
                                  // eslint-disable-next-line @next/next/no-img-element
                                  <img key={id} src={`/api/attachments/${id}`} alt="" style={{ maxWidth: "min(100%, 600px)", height: "auto", borderRadius: 6 }} />
                                ))}
                              </div>
                            ) : null}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
      {canEdit ? (
        <form
          onSubmit={onSubmit}
          className="stack"
          style={{ gap: "0.5rem" }}
        >
          {replyToId ? (
            <p className="text-sm muted" style={{ margin: 0 }}>
              Replying to comment.{" "}
              <button type="button" className="btn btn-ghost text-sm" onClick={() => setReplyToId(null)}>
                Cancel
              </button>
            </p>
          ) : null}
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span className="text-sm muted">{replyToId ? "Reply" : "Add comment"}</span>
            <MarkdownEditor
              value={body}
              onChange={setBody}
              rows={4}
              placeholder="What happened, next steps, customer-facing summary…"
              onPasteFiles={(files) => addFiles(files)}
              onDropFiles={(files) => addFiles(files)}
              mentionSuggestions={_searchUsers}
              refSuggestions={_searchRefs}
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
            <PendingThumbnails pending={pending} onRemove={remove} />
          </div>
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
            <button type="submit" className="btn btn-primary" disabled={busy || (!body.trim() && pending.length === 0)}>
              {busy ? "Posting…" : isInternal ? "Post internal note" : "Post comment"}
            </button>
            <label
              className="text-sm"
              style={{ display: "inline-flex", gap: "0.4rem", alignItems: "center", cursor: "pointer" }}
              title="Internal notes are visible only to project members (not customer-visible)."
            >
              <input
                type="checkbox"
                checked={isInternal}
                onChange={(e) => setIsInternal(e.target.checked)}
              />
              Internal note (staff only)
            </label>
          </div>
          {msg ? <p className="err text-sm">{msg}</p> : null}
        </form>
      ) : (
        <p className="muted text-sm">Viewers cannot post comments.</p>
      )}
    </div>
  );
}
