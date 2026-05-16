import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { ProjectSubNav } from "../../ProjectSubNav";

type ProjectRow = {
  id: string;
  name: string;
  membership_role?: string | null;
};

type TaskOut = {
  id: string;
  project_id: string;
  component_id: string | null;
  ref: string | null;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  assignee_id: string | null;
  reporter_id: string;
  due_at: string | null;
  parent_task_id: string | null;
  is_todo: boolean;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
};

type ActivityItem = {
  id: string;
  actor_email: string | null;
  body: string;
  created_at: string;
  parent_activity_id: string | null;
  kind: string;
  meta_json?: Record<string, unknown> | null;
};

export default async function TaskDetailPage({
  params,
}: {
  params: Promise<{ id: string; taskId: string }>;
}) {
  const me = await fetchMe();
  if (!me) {
    redirect("/login");
  }
  const { id: projectId, taskId } = await params;

  const [pr, tr] = await Promise.all([
    apiServerFetch(`/v1/projects/${projectId}`),
    apiServerFetch(`/v1/tasks/${taskId}`),
  ]);
  if (pr.status === 404) notFound();
  if (!pr.ok) {
    return (
      <div className="page-inner">
        <p className="err">Could not load project.</p>
      </div>
    );
  }
  if (tr.status === 404) notFound();
  if (!tr.ok) {
    return (
      <div className="page-inner">
        <p className="err">Could not load task.</p>
      </div>
    );
  }

  const project = (await pr.json()) as ProjectRow;
  const task = (await tr.json()) as TaskOut;
  if (task.project_id !== projectId) notFound();

  const ar = await apiServerFetch(
    `/v1/projects/${projectId}/activities?subject_type=task&subject_id=${taskId}&limit=50`,
  );
  const activityItems: ActivityItem[] = ar.ok
    ? ((await ar.json()) as { items: ActivityItem[] }).items
    : [];
  activityItems.sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  );

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href={`/projects/${projectId}/tasks`} className="muted text-sm">
          ← Tasks
        </Link>
        <p className="muted text-sm" style={{ margin: "0.15rem 0" }}>
          Project: <strong>{project.name}</strong>
        </p>
        <h1 style={{ marginTop: "0.25rem", marginBottom: "0.15rem" }}>
          {task.ref ? (
            <span className="muted text-sm" style={{ fontFamily: "var(--font-mono, monospace)" }}>
              {task.ref} ·{" "}
            </span>
          ) : null}
          {task.title}
        </h1>
        <ProjectSubNav projectId={projectId} current="tasks" />
      </div>

      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Details</h2>
        <dl
          className="stack text-sm"
          style={{
            margin: 0,
            display: "grid",
            gridTemplateColumns: "auto 1fr",
            gap: "0.35rem 1rem",
            alignItems: "baseline",
          }}
        >
          <dt className="muted">Status</dt>
          <dd style={{ margin: 0 }}>
            <span className="pill">{task.status}</span>
          </dd>
          <dt className="muted">Priority</dt>
          <dd style={{ margin: 0 }}>{task.priority}</dd>
          {task.due_at ? (
            <>
              <dt className="muted">Due</dt>
              <dd style={{ margin: 0 }}>{new Date(task.due_at).toLocaleString()}</dd>
            </>
          ) : null}
          <dt className="muted">Created</dt>
          <dd style={{ margin: 0 }}>{new Date(task.created_at).toLocaleString()}</dd>
          {task.updated_at ? (
            <>
              <dt className="muted">Updated</dt>
              <dd style={{ margin: 0 }}>{new Date(task.updated_at).toLocaleString()}</dd>
            </>
          ) : null}
        </dl>
        <div>
          <h3 className="text-sm muted" style={{ margin: "0.75rem 0 0.35rem" }}>
            Description
          </h3>
          {task.description ? (
            <p style={{ whiteSpace: "pre-wrap", margin: 0 }}>{task.description}</p>
          ) : (
            <p className="muted text-sm">No description.</p>
          )}
        </div>
      </div>

      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Activity</h2>
        {activityItems.length === 0 ? (
          <p className="muted text-sm">No activity yet.</p>
        ) : (
          <ul className="stack" style={{ listStyle: "none", margin: 0, padding: 0, gap: "0.75rem" }}>
            {activityItems.map((a) => (
              <li key={a.id} className="card" style={{ padding: "0.65rem 0.85rem" }}>
                <div className="muted text-sm" style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", marginBottom: "0.3rem" }}>
                  <span>{a.actor_email ?? "user"}</span>
                  <span className="pill" style={{ fontSize: "0.65rem" }}>{a.kind}</span>
                  <span>· {new Date(a.created_at).toLocaleString()}</span>
                </div>
                <div style={{ whiteSpace: "pre-wrap" }}>{a.body}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
