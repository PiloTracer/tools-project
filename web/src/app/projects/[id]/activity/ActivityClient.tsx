"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { CommitCard, extractCommitMeta } from "@/components/CommitCard";
import { CommitPicker } from "@/components/CommitPicker";
import { MarkdownEditor } from "@/components/MarkdownEditor";
import { SubjectPicker } from "@/components/SubjectPicker";
import { SubjectPreview } from "@/components/SubjectPreview";
import { usePendingImages } from "@/shared/client/use-pending-images";
import { toast } from "@/components/Toast";

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

type ActivityRow = {
  id: string;
  actor_email: string | null;
  kind: string;
  body: string;
  subject_type: string;
  subject_id?: string;
  created_at: string;
  parent_activity_id?: string | null;
  is_internal?: boolean;
  meta_json?: Record<string, unknown> | null;
  subject_ref?: string | null;
  subject_title?: string | null;
};

export function ActivityComposer({
  projectId,
  canPost,
}: {
  projectId: string;
  canPost: boolean;
}) {
  const router = useRouter();
  const { pending, addFiles, remove, clear } = usePendingImages();
  const [subjectType, setSubjectType] = useState("project");
  const [subjectId, setSubjectId] = useState<string | null>(null);
  const [subjectLabel, setSubjectLabel] = useState<string | null>(null);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [showCommitPicker, setShowCommitPicker] = useState(false);
  const [showSubjectPicker, setShowSubjectPicker] = useState(false);
  const [commitMeta, setCommitMeta] = useState<{
    commit_id: string;
    sha: string;
    owner: string;
    repo: string;
    html_url: string;
  } | null>(null);

  if (!canPost) {
    return <p className="muted text-sm">Viewers cannot post activity.</p>;
  }

  function chooseSubject(kind: "project" | "task" | "ticket") {
    setSubjectType(kind);
    setSubjectId(null);
    setSubjectLabel(null);
    if (kind !== "project") {
      setShowSubjectPicker(true);
    }
  }

  async function uploadPending(): Promise<string[]> {
    const ids: string[] = [];
    for (const p of pending) {
      const fd = new FormData();
      fd.append("file", p.file);
      const ur = await fetch(`/api/projects/${projectId}/attachments`, {
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
    setBusy(true);
    try {
      const uploadedIds = pending.length ? await uploadPending() : [];
      let resolvedSubjectId = projectId;
      let resolvedSubjectType = "project";
      if (subjectType !== "project") {
        if (!subjectId) {
          toast("Select a task or ticket to link this post to.", "error");
          setBusy(false);
          return;
        }
        resolvedSubjectId = subjectId;
        resolvedSubjectType = subjectType;
      }
      const meta_json: Record<string, unknown> = {};
      if (uploadedIds.length) {
        meta_json.attachment_ids = uploadedIds;
      }
      if (commitMeta) {
        meta_json.github_ref = commitMeta;
      }
      const payload: Record<string, unknown> = {
        subject_type: resolvedSubjectType,
        subject_id: resolvedSubjectId,
        kind: "note",
        body: caption || (uploadedIds.length ? "(image)" : ""),
      };
      if (Object.keys(meta_json).length) {
        payload.meta_json = meta_json;
      }
      const r = await fetch(`/api/projects/${projectId}/activities`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const text = await r.text();
      if (!r.ok) {
        try {
          const j = JSON.parse(text) as { detail?: string };
          toast(j.detail ?? text, "error");
        } catch {
          toast(text || `Error ${r.status}`, "error");
        }
        setBusy(false);
        return;
      }
      setBody("");
      setSubjectType("project");
      setSubjectId(null);
      setSubjectLabel(null);
      clear();
      toast("Note posted");
      router.refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Upload failed", "error");
    }
    setBusy(false);
  }

  return (
    <form
      onSubmit={onSubmit}
      className="stack"
      style={{ gap: "0.65rem", maxWidth: "40rem" }}
    >
      <div className="stack" style={{ gap: "0.35rem" }}>
        <span className="text-sm muted">Subject</span>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <button
            type="button"
            className={subjectType === "project" ? "btn btn-secondary text-sm" : "btn btn-ghost text-sm"}
            onClick={() => chooseSubject("project")}
            style={{ padding: "0.35rem 0.65rem" }}
          >
            This project
          </button>
          <button
            type="button"
            className={subjectType === "task" ? "btn btn-secondary text-sm" : "btn btn-ghost text-sm"}
            onClick={() => chooseSubject("task")}
            style={{ padding: "0.35rem 0.65rem" }}
          >
            Link to task
          </button>
          <button
            type="button"
            className={subjectType === "ticket" ? "btn btn-secondary text-sm" : "btn btn-ghost text-sm"}
            onClick={() => chooseSubject("ticket")}
            style={{ padding: "0.35rem 0.65rem" }}
          >
            Link to ticket
          </button>
        </div>
      </div>
      {subjectType !== "project" && showSubjectPicker ? (
        <SubjectPicker
          projectId={projectId}
          onSelect={(kind, id, label) => {
            setSubjectType(kind);
            setSubjectId(id);
            setSubjectLabel(label);
            setShowSubjectPicker(false);
          }}
          onClose={() => {
            setShowSubjectPicker(false);
            setSubjectType("project");
          }}
        />
      ) : null}
      {subjectLabel ? (
        <p className="text-sm" style={{ color: "var(--accent)", margin: 0 }}>
          → Linked to {subjectLabel}
        </p>
      ) : null}
      <label className="stack" style={{ gap: "0.25rem" }}>
        <span className="text-sm muted">Message (use @you@example.com to mention)</span>
        <MarkdownEditor
          value={body}
          onChange={setBody}
          rows={4}
          placeholder="Type a message…"
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
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
        <button type="submit" className="btn btn-primary" disabled={busy || (!body.trim() && pending.length === 0)}>
          {busy ? "Posting…" : "Post"}
        </button>
        <button
          type="button"
          className="btn btn-ghost text-sm"
          onClick={() => setShowCommitPicker(!showCommitPicker)}
        >
          {showCommitPicker ? "Cancel" : "Cite commit"}
        </button>
      </div>
      {showCommitPicker ? (
        <CommitPicker
          projectId={projectId}
          onSelect={(md, meta) => {
            setBody((prev) => (prev ? prev + "\n" + md : md));
            setCommitMeta(meta);
            setShowCommitPicker(false);
          }}
          onClose={() => setShowCommitPicker(false)}
        />
      ) : null}
    </form>
  );
}

export function GithubBackfillSync({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [days, setDays] = useState(30);
  const [busy, setBusy] = useState(false);

  const handleSync = async () => {
    setBusy(true);
    const r = await fetch(`/api/projects/${projectId}/github/sync-backfill`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ since_days: days }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Sync failed" }));
      toast(err.detail, "error");
      setBusy(false);
      return;
    }
    const data = await r.json() as { results: { owner: string; repo: string; upserted?: number; error?: string }[] };
    const ok = data.results.filter((r) => r.upserted !== undefined);
    const fail = data.results.filter((r) => r.error);
    if (ok.length) {
      toast(`Synced ${ok.map((r) => `${r.owner}/${r.repo} (${r.upserted} commits)`).join(", ")}`, "success");
    }
    if (fail.length) {
      toast(`Failed: ${fail.map((r) => `${r.owner}/${r.repo}: ${r.error}`).join(", ")}`, "error");
    }
    setBusy(false);
    router.refresh();
  };

  return (
    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginTop: "0.5rem" }}>
      <label className="field" style={{ margin: 0, flexDirection: "row", alignItems: "center", gap: "0.35rem" }}>
        <span className="label text-sm" style={{ margin: 0 }}>Re-sync last</span>
        <input
          className="input"
          type="number"
          min={1}
          max={365}
          value={days}
          onChange={(e) => setDays(parseInt(e.target.value) || 30)}
          style={{ width: "60px", fontSize: "0.85rem", padding: "0.2rem 0.4rem" }}
          disabled={busy}
        />
        <span className="text-sm muted">days of GitHub commits</span>
      </label>
      <button
        className="btn btn-sm btn-secondary"
        onClick={handleSync}
        disabled={busy}
        style={{ whiteSpace: "nowrap" }}
      >
        {busy ? "Syncing…" : "Re-sync GitHub"}
      </button>
    </div>
  );
}

export function ActivityStreamHint({ projectId }: { projectId: string }) {
  const [last, setLast] = useState<{ id: string | null; kind?: string; subject_type?: string }>({ id: null });
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const es = new EventSource(`/api/projects/${projectId}/activities/stream`);
    esRef.current = es;
    es.onmessage = (ev) => {
      try {
        const j = JSON.parse(ev.data) as { latest_activity_id?: string | null; kind?: string; subject_type?: string };
        setLast({ id: j.latest_activity_id ?? null, kind: j.kind, subject_type: j.subject_type });
      } catch {
        /* ignore */
      }
    };
    es.onerror = () => {
      es.close();
    };
    return () => {
      es.close();
    };
  }, [projectId]);

  return (
    <p className="muted text-sm">
      Live stream (SSE): latest activity id{" "}
      <code>{last.id ?? "—"}</code>
      {last.kind ? <span> · kind <code>{last.kind}</code></span> : null}
      {" "}— refresh the page to load new posts when it changes.
    </p>
  );
}

function buildThreaded(items: ActivityRow[]): ActivityRow[] {
  return items.filter((a) => !a.parent_activity_id);
}

function getReplies(parentId: string, items: ActivityRow[]): ActivityRow[] {
  return items
    .filter((a) => a.parent_activity_id === parentId)
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
}

export function ActivityFeed({
  initial,
  projectId,
  canPost,
}: {
  initial: ActivityRow[];
  projectId?: string;
  canPost?: boolean;
}) {
  const router = useRouter();
  const { pending: replyPending, addFiles: addReplyFiles, remove: removeReplyFile, clear: clearReplyPending } = usePendingImages();
  const [replyToId, setReplyToId] = useState<string | null>(null);
  const [replyBody, setReplyBody] = useState("");
  const [replyBusy, setReplyBusy] = useState(false);
  const [replyCommitPicker, setReplyCommitPicker] = useState<string | null>(null);
  const [replyCommitMeta, setReplyCommitMeta] = useState<{
    commit_id: string;
    sha: string;
    owner: string;
    repo: string;
    html_url: string;
  } | null>(null);
  const [previewSubject, setPreviewSubject] = useState<{ subjectType: string; subjectId: string } | null>(null);

  const topItems = buildThreaded(initial);

  async function submitReply(parentActivity: ActivityRow) {
    if (!projectId) return;
    const caption = replyBody.trim();
    if (!caption && replyPending.length === 0) return;
    setReplyBusy(true);
    try {
      const uploadedIds: string[] = [];
      for (const p of replyPending) {
        const fd = new FormData();
        fd.append("file", p.file);
        const ur = await fetch(`/api/projects/${projectId}/attachments`, {
          method: "POST",
          body: fd,
        });
        const ut = await ur.text();
        if (!ur.ok) {
          try { const j = JSON.parse(ut) as { detail?: string }; throw new Error(j.detail ?? ut); }
          catch (e) {
            if (e instanceof Error && e.message !== ut) throw e;
            throw new Error(ut || `Upload failed (${ur.status})`);
          }
        }
        const row = JSON.parse(ut) as { id: string };
        uploadedIds.push(row.id);
      }
      const reply_meta: Record<string, unknown> = {};
      if (uploadedIds.length) {
        reply_meta.attachment_ids = uploadedIds;
      }
      if (replyCommitMeta) {
        reply_meta.github_ref = replyCommitMeta;
      }
      const payload: Record<string, unknown> = {
        subject_type: parentActivity.subject_type,
        subject_id: parentActivity.subject_id || projectId,
        kind: "comment",
        body: caption || (uploadedIds.length ? "(image)" : ""),
        parent_activity_id: parentActivity.id,
      };
      if (Object.keys(reply_meta).length) {
        payload.meta_json = reply_meta;
      }
      const r = await fetch(`/api/projects/${projectId}/activities`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const text = await r.text();
      if (!r.ok) {
        try {
          const j = JSON.parse(text) as { detail?: string };
          toast(j.detail ?? text, "error");
        } catch {
          toast(text || `Error ${r.status}`, "error");
        }
        setReplyBusy(false);
        return;
      }
      setReplyBody("");
      setReplyToId(null);
      setReplyCommitMeta(null);
      clearReplyPending();
      toast("Reply posted");
      router.refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Upload failed", "error");
    }
    setReplyBusy(false);
  }

  return (
    <div className="stack" style={{ gap: "0.75rem" }}>
      <ul className="stack" style={{ listStyle: "none", padding: 0, gap: "0.75rem" }}>
        {initial.length === 0 ? (
          <li className="muted">No activity yet.</li>
        ) : (
          topItems.map((a) => {
            const internal = a.is_internal === true;
            const childReplies = getReplies(a.id, initial);
            return (
              <li key={a.id}>
                <div
                  className="card"
                  style={{
                    padding: "0.75rem 1rem",
                    background: internal ? "var(--surface-warn, #fff8e1)" : undefined,
                    borderColor: internal ? "var(--border-warn, #f0c36d)" : undefined,
                  }}
                >
                  <div className="text-sm muted" style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center" }}>
                    <span>{a.actor_email ?? "user"}</span>
                    {a.kind === "github_commit" ? (
                      <span className="pill" style={{ fontSize: "0.65rem", background: "var(--accent, #0366d6)", color: "var(--on-accent, #fff)" }}>commit</span>
                    ) : (
                      <span className="pill" style={{ fontSize: "0.65rem" }}>{a.kind}</span>
                    )}
                    {a.subject_type === "task" && a.subject_id ? (
                      <span>{a.subject_ref ?? "task"}</span>
                    ) : a.subject_type === "ticket" && a.subject_id ? (
                      <span>{a.subject_ref ?? "ticket"}</span>
                    ) : (
                      <span>{a.subject_type}</span>
                    )}
                    {a.subject_title && a.subject_id ? (
                      <button
                        type="button"
                        style={{ background: "none", border: "none", cursor: "pointer", fontSize: "0.85rem", padding: 0, fontFamily: "inherit", color: "var(--text)", textAlign: "left" }}
                        onClick={() => setPreviewSubject({ subjectType: a.subject_type, subjectId: a.subject_id! })}
                        title={a.subject_title ?? undefined}
                      >
                        {a.subject_title.length > 80 ? a.subject_title.slice(0, 80) + "…" : a.subject_title}
                      </button>
                    ) : null}
                    <span>·</span>
                    <span suppressHydrationWarning>{new Date(a.created_at).toLocaleString()}</span>
                    {internal ? (
                      <span
                        className="pill"
                        title="Internal note — not customer-visible"
                        style={{ background: "var(--accent-warn, #c98300)", color: "var(--on-accent, #fff)", fontSize: "0.65rem" }}
                      >
                        Internal
                      </span>
                    ) : null}
                  </div>
                  {a.kind === "github_commit" ? (
                    <CommitCard meta={extractCommitMeta(a.meta_json)!} projectId={projectId} />
                  ) : (
                    <p style={{ margin: "0.35rem 0 0", whiteSpace: "pre-wrap" }}>{a.body}</p>
                  )}
                  {canPost && projectId ? (
                    <button
                      type="button"
                      className="btn btn-ghost text-sm"
                      style={{ marginTop: "0.35rem", padding: "0.15rem 0.5rem" }}
                      onClick={() => {
                        setReplyToId(replyToId === a.id ? null : a.id);
                        setReplyBody("");
                      }}
                    >
                      {replyToId === a.id ? "Cancel reply" : "Reply"}
                    </button>
                  ) : null}
                </div>
                {replyToId === a.id && projectId ? (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      submitReply(a);
                    }}
                    className="stack"
                    style={{
                      margin: "0.5rem 0 0 1.5rem",
                      padding: "0.65rem 0.85rem",
                      borderLeft: "2px solid var(--border)",
                      paddingLeft: "0.75rem",
                      gap: "0.5rem",
                    }}
                  >
                    <MarkdownEditor
                      value={replyBody}
                      onChange={setReplyBody}
                      rows={3}
                      placeholder="Write a reply…"
                      onPasteFiles={(files) => addReplyFiles(files)}
                      onDropFiles={(files) => addReplyFiles(files)}
                      mentionSuggestions={_searchUsers}
                      refSuggestions={_searchRefs}
                    />
                    <div className="stack" style={{ gap: "0.35rem" }}>
                      <label className="btn btn-ghost text-sm" style={{ cursor: "pointer", display: "inline-flex", alignItems: "center", gap: "0.35rem" }}>
                        <input
                          type="file"
                          accept="image/png,image/jpeg,image/gif,image/webp,application/pdf,text/plain,text/csv,.csv,.xls,.xlsx,.ppt,.pptx,.doc,.docx,.odt,.ods,.odp"
                          multiple
                          style={{ display: "none" }}
                          onChange={(e) => {
                            const list = e.target.files;
                            if (list?.length) addReplyFiles(Array.from(list));
                            e.target.value = "";
                          }}
                        />
                        Browse files…
                      </label>
                      {replyPending.length > 0 ? (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "flex-start" }}>
                          {replyPending.map((p) => (
                            <div key={p.key} style={{ position: "relative" }}>
                              {p.url ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img src={p.url} alt="" style={{ width: 72, height: 72, objectFit: "cover", borderRadius: 6, border: "1px solid var(--border)" }} />
                              ) : (
                                <div className="text-sm muted" style={{ width: 120, minHeight: 72, padding: "0.35rem", borderRadius: 6, border: "1px solid var(--border)", wordBreak: "break-all" }} title={p.file.name}>
                                  {p.file.name}
                                </div>
                              )}
                              <button type="button" className="btn btn-ghost text-sm" style={{ position: "absolute", top: -6, right: -6, padding: "0 0.35rem", minHeight: 0 }} onClick={() => removeReplyFile(p.key)} aria-label="Remove attachment">×</button>
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                      <button type="submit" className="btn btn-primary text-sm" disabled={replyBusy || (!replyBody.trim() && replyPending.length === 0)}>
                        {replyBusy ? "Posting…" : "Reply"}
                      </button>
                      <button
                        type="button"
                        className="btn btn-ghost text-sm"
                        onClick={() =>
                          setReplyCommitPicker(replyCommitPicker === a.id ? null : a.id)
                        }
                      >
                        Cite commit
                      </button>
                    </div>
                    {replyCommitPicker === a.id && projectId ? (
                      <CommitPicker
                        projectId={projectId}
                        onSelect={(md, meta) => {
                          setReplyBody((prev) => (prev ? prev + "\n" + md : md));
                          setReplyCommitMeta(meta);
                          setReplyCommitPicker(null);
                        }}
                        onClose={() => setReplyCommitPicker(null)}
                      />
                    ) : null}
                  </form>
                ) : null}
                {childReplies.length > 0 ? (
                  <ul
                    className="stack"
                    style={{
                      listStyle: "none",
                      padding: 0,
                      margin: "0.5rem 0 0 1.5rem",
                      gap: "0.5rem",
                      borderLeft: "2px solid var(--border)",
                      paddingLeft: "0.75rem",
                    }}
                  >
                    {childReplies.map((cr) => {
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
                            <div className="text-sm muted" style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", marginBottom: "0.25rem" }}>
                              <span>{cr.actor_email ?? "user"}</span>
                              <span className="pill" style={{ fontSize: "0.6rem" }}>{cr.kind}</span>
                              <span suppressHydrationWarning>· {new Date(cr.created_at).toLocaleString()}</span>
                              {cinternal ? (
                                <span className="pill" style={{ fontSize: "0.6rem", background: "var(--accent-warn, #c98300)", color: "#fff" }}>
                                  Internal
                                </span>
                              ) : null}
                            </div>
                            <p style={{ margin: 0, whiteSpace: "pre-wrap" }}>{cr.body}</p>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                ) : null}
              </li>
            );
          })
        )}
      </ul>
      {previewSubject ? (
        <SubjectPreview
          projectId={projectId!}
          subjectType={previewSubject.subjectType}
          subjectId={previewSubject.subjectId}
          onClose={() => setPreviewSubject(null)}
        />
      ) : null}
    </div>
  );
}
