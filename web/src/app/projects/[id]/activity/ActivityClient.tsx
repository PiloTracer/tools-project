"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

type ActivityRow = {
  id: string;
  actor_email: string | null;
  kind: string;
  body: string;
  subject_type: string;
  created_at: string;
  is_internal?: boolean;
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
  const [body, setBody] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  if (!canPost) {
    return <p className="muted text-sm">Viewers cannot post activity.</p>;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    let subject_id = projectId;
    if (subjectType !== "project") {
      const entered = window.prompt("Paste task or ticket UUID")?.trim();
      if (!entered) {
        setMsg("subject_id required");
        return;
      }
      subject_id = entered;
    }
    const r = await fetch(`/api/projects/${projectId}/activities`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        subject_type: subjectType,
        subject_id: subject_id,
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
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="stack" style={{ gap: "0.65rem", maxWidth: "40rem" }}>
      <label className="stack" style={{ gap: "0.25rem" }}>
        <span className="text-sm muted">Subject</span>
        <select
          className="input"
          value={subjectType}
          onChange={(e) => setSubjectType(e.target.value)}
        >
          <option value="project">This project</option>
          <option value="task">Task (paste UUID)</option>
          <option value="ticket">Ticket (paste UUID)</option>
        </select>
      </label>
      <label className="stack" style={{ gap: "0.25rem" }}>
        <span className="text-sm muted">Message (use @you@example.com to mention)</span>
        <textarea
          className="input"
          rows={4}
          required
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
      </label>
      <button type="submit" className="btn btn-primary">
        Post
      </button>
      {msg ? <p className="err text-sm">{msg}</p> : null}
    </form>
  );
}

export function ActivityStreamHint({ projectId }: { projectId: string }) {
  const [last, setLast] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const es = new EventSource(`/api/projects/${projectId}/activities/stream`);
    esRef.current = es;
    es.onmessage = (ev) => {
      try {
        const j = JSON.parse(ev.data) as { latest_activity_id?: string | null };
        setLast(j.latest_activity_id ?? null);
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
      <code>{last ?? "—"}</code> — refresh the page to load new posts when it changes.
    </p>
  );
}

export function ActivityFeed({ initial }: { initial: ActivityRow[] }) {
  return (
    <ul className="stack" style={{ listStyle: "none", padding: 0, gap: "0.75rem" }}>
      {initial.length === 0 ? (
        <li className="muted">No activity yet.</li>
      ) : (
        initial.map((a) => {
          const internal = a.is_internal === true;
          return (
            <li
              key={a.id}
              className="card"
              style={{
                padding: "0.75rem 1rem",
                background: internal ? "var(--surface-warn, #fff8e1)" : undefined,
                borderColor: internal ? "var(--border-warn, #f0c36d)" : undefined,
              }}
            >
              <div className="text-sm muted" style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center" }}>
                <span>{a.actor_email ?? "user"}</span>
                <span className="pill" style={{ fontSize: "0.65rem" }}>{a.kind}</span>
                <span>· {a.subject_type} ·</span>
                <span>{new Date(a.created_at).toLocaleString()}</span>
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
              <p style={{ margin: "0.35rem 0 0", whiteSpace: "pre-wrap" }}>{a.body}</p>
            </li>
          );
        })
      )}
    </ul>
  );
}
