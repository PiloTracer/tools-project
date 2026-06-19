"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { CommitPicker } from "@/components/CommitPicker";
import { MarkdownEditor } from "@/components/MarkdownEditor";
import { SubjectPicker } from "@/components/SubjectPicker";
import { SubjectPreview } from "@/components/SubjectPreview";

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
  const [subjectType, setSubjectType] = useState("project");
  const [subjectId, setSubjectId] = useState<string | null>(null);
  const [subjectLabel, setSubjectLabel] = useState<string | null>(null);
  const [body, setBody] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [showCommitPicker, setShowCommitPicker] = useState(false);
  const [showSubjectPicker, setShowSubjectPicker] = useState(false);

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

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    let resolvedSubjectId = projectId;
    let resolvedSubjectType = "project";
    if (subjectType !== "project") {
      if (!subjectId) {
        setMsg("Select a task or ticket to link this post to.");
        return;
      }
      resolvedSubjectId = subjectId;
      resolvedSubjectType = subjectType;
    }
    const r = await fetch(`/api/projects/${projectId}/activities`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        subject_type: resolvedSubjectType,
        subject_id: resolvedSubjectId,
        body: body.trim(),
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
    setBody("");
    setSubjectType("project");
    setSubjectId(null);
    setSubjectLabel(null);
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="stack" style={{ gap: "0.65rem", maxWidth: "40rem" }}>
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
          mentionSuggestions={_searchUsers}
          refSuggestions={_searchRefs}
        />
      </label>
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
        <button type="submit" className="btn btn-primary">
          Post
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
          onSelect={(md) => {
            setBody((prev) => (prev ? prev + "\n" + md : md));
            setShowCommitPicker(false);
          }}
          onClose={() => setShowCommitPicker(false)}
        />
      ) : null}
      {msg ? <p className="err text-sm">{msg}</p> : null}
    </form>
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
  const [replyToId, setReplyToId] = useState<string | null>(null);
  const [replyBody, setReplyBody] = useState("");
  const [replyBusy, setReplyBusy] = useState(false);
  const [replyMsg, setReplyMsg] = useState<string | null>(null);
  const [replyCommitPicker, setReplyCommitPicker] = useState<string | null>(null);
  const [previewSubject, setPreviewSubject] = useState<{ subjectType: string; subjectId: string } | null>(null);

  const topItems = buildThreaded(initial);

  async function submitReply(parentActivity: ActivityRow) {
    if (!projectId) return;
    const rim = replyBody.trim();
    if (!rim) return;
    setReplyBusy(true);
    setReplyMsg(null);
    const r = await fetch(`/api/projects/${projectId}/activities`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        subject_type: parentActivity.subject_type,
        subject_id: parentActivity.subject_id || projectId,
        kind: "comment",
        body: rim,
        parent_activity_id: parentActivity.id,
      }),
    });
    const text = await r.text();
    if (!r.ok) {
      try {
        const j = JSON.parse(text) as { detail?: string };
        setReplyMsg(j.detail ?? text);
      } catch {
        setReplyMsg(text || `Error ${r.status}`);
      }
      setReplyBusy(false);
      return;
    }
    setReplyBody("");
    setReplyToId(null);
    setReplyBusy(false);
    router.refresh();
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
                      <button
                        type="button"
                        className="muted"
                        style={{ background: "none", border: "none", cursor: "pointer", fontSize: "inherit", padding: 0, fontFamily: "inherit", textDecoration: "underline", textUnderlineOffset: "2px" }}
                        onClick={() => setPreviewSubject({ subjectType: "task", subjectId: a.subject_id! })}
                        title={a.subject_title ?? undefined}
                      >
                        {a.subject_ref ?? "task"}
                      </button>
                    ) : a.subject_type === "ticket" && a.subject_id ? (
                      <button
                        type="button"
                        className="muted"
                        style={{ background: "none", border: "none", cursor: "pointer", fontSize: "inherit", padding: 0, fontFamily: "inherit", textDecoration: "underline", textUnderlineOffset: "2px" }}
                        onClick={() => setPreviewSubject({ subjectType: "ticket", subjectId: a.subject_id! })}
                        title={a.subject_title ?? undefined}
                      >
                        {a.subject_ref ?? "ticket"}
                      </button>
                    ) : (
                      <span>{a.subject_type}</span>
                    )}
                    {a.subject_title && a.subject_id ? (
                      <span className="text-sm" style={{ color: "var(--text)" }}>{a.subject_title.length > 60 ? a.subject_title.slice(0, 60) + "…" : a.subject_title}</span>
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
                  {a.kind === "github_commit" && a.meta_json ? (
                    <div style={{ margin: "0.35rem 0 0" }}>
                      <a
                        href={a.meta_json.html_url as string}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}
                      >
                        <code style={{ fontSize: "0.85rem" }}>{(a.meta_json.sha as string)?.slice(0, 7)}</code>
                      </a>
                      <span className="muted" style={{ fontSize: "0.8rem", marginLeft: "0.5rem" }}>
                        {a.meta_json.owner as string}/{a.meta_json.repo as string}
                      </span>
                      <p style={{ margin: "0.2rem 0 0", whiteSpace: "pre-wrap", fontSize: "0.9rem" }}>
                        {a.meta_json.message_preview as string}
                      </p>
                    </div>
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
                        setReplyMsg(null);
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
                      mentionSuggestions={_searchUsers}
                      refSuggestions={_searchRefs}
                    />
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                      <button type="submit" className="btn btn-primary text-sm" disabled={replyBusy || !replyBody.trim()}>
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
                        onSelect={(md) => {
                          setReplyBody((prev) => (prev ? prev + "\n" + md : md));
                          setReplyCommitPicker(null);
                        }}
                        onClose={() => setReplyCommitPicker(null)}
                      />
                    ) : null}
                    {replyMsg ? <p className="err text-sm">{replyMsg}</p> : null}
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
