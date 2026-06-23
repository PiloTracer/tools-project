import Link from "next/link";
import { apiServerFetch, fetchMe } from "@/shared/server/session";
import { redirect, notFound } from "next/navigation";

import { ClientTaskCreateForm } from "./ClientTaskCreateForm";

type ProjectRow = {
  id: string;
  name: string;
  description: string | null;
  status: string;
  membership_role?: string | null;
};

type ActivityRow = {
  id: string;
  kind: string;
  body: string;
  is_internal: boolean;
  created_at: string;
  actor_email: string | null;
  meta_json: Record<string, unknown> | null;
};

type TaskRow = {
  id: string;
  ref: string;
  title: string;
  status: string;
  priority: string;
  due_at: string | null;
};

type TicketRow = {
  id: string;
  ref: string;
  title: string;
  status: string;
  priority: string;
};

export default async function ClientProjectPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const me = await fetchMe();
  if (!me) {
    redirect("/client/login");
  }

  const { id } = await params;

  const [projectRes, activitiesRes, tasksRes, ticketsRes] = await Promise.all([
    apiServerFetch(`/v1/me/client/projects/${id}`),
    apiServerFetch(`/v1/me/client/projects/${id}/activities?limit=20`),
    apiServerFetch(`/v1/me/client/projects/${id}/tasks`),
    apiServerFetch(`/v1/me/client/projects/${id}/tickets`),
  ]);

  if (projectRes.status === 404) {
    notFound();
  }
  if (!projectRes.ok) {
    return (
      <div className="page-inner">
        <p className="err">Could not load project.</p>
        <Link href="/client/dashboard">← Dashboard</Link>
      </div>
    );
  }

  const project = (await projectRes.json()) as ProjectRow;
  const activities: ActivityRow[] = activitiesRes.ok
    ? (await activitiesRes.json()).items
    : [];
  const tasks: TaskRow[] = tasksRes.ok ? (await tasksRes.json()).items : [];
  const tickets: TicketRow[] = ticketsRes.ok ? (await ticketsRes.json()).items : [];

  const role = project.membership_role ?? "view";
  const canContribute = role === "contribute" || role === "decision_maker";

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/client/dashboard" className="muted text-sm">← Dashboard</Link>
        <h1 style={{ marginTop: "0.25rem" }}>{project.name}</h1>
        {project.description ? (
          <p className="muted">{project.description}</p>
        ) : null}
        <p className="muted text-sm">Role: {role}</p>
      </div>

      {canContribute && (
        <ClientTaskCreateForm projectId={id} />
      )}

      <section className="card stack">
        <h2>Your tasks</h2>
        {tasks.length === 0 ? (
          <p className="muted">No tasks assigned to you.</p>
        ) : (
          <ul className="stack-sm" style={{ listStyle: "none", padding: 0 }}>
            {tasks.map((task) => (
              <li key={task.id} className="card">
                <strong>
                  {task.ref}: {task.title}
                </strong>
                <p className="muted text-sm">
                  {task.status} · {task.priority}
                  {task.due_at ? ` · due ${new Date(task.due_at).toLocaleDateString()}` : ""}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

      {canContribute && tickets.length > 0 && (
        <section className="card stack">
          <h2>Tickets</h2>
          <ul className="stack-sm" style={{ listStyle: "none", padding: 0 }}>
            {tickets.map((ticket) => (
              <li key={ticket.id} className="card">
                <strong>
                  {ticket.ref}: {ticket.title}
                </strong>
                <p className="muted text-sm">
                  {ticket.status} · {ticket.priority}
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="card stack">
        <h2>Activity</h2>
        {activities.length === 0 ? (
          <p className="muted">No public activity yet.</p>
        ) : (
          <ul className="stack-sm" style={{ listStyle: "none", padding: 0 }}>
            {activities.map((activity) => (
              <li key={activity.id} className="card">
                <p className="muted text-sm" suppressHydrationWarning>
                  {activity.kind === "github_commit" ? (
                    <span className="pill" style={{ fontSize: "0.65rem", background: "var(--accent, #0366d6)", color: "var(--on-accent, #fff)" }}>commit</span>
                  ) : (
                    <span>{activity.kind}</span>
                  )}
                  <span> · {new Date(activity.created_at).toLocaleString()}</span>
                  {activity.actor_email ? <span> · {activity.actor_email}</span> : null}
                </p>
                {activity.kind === "github_commit" && activity.meta_json ? (
                  <div>
                    <a
                      href={activity.meta_json.html_url as string}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}
                    >
                      <code style={{ fontSize: "0.85rem" }}>{(activity.meta_json.sha as string)?.slice(0, 7)}</code>
                    </a>
                    <span className="muted" style={{ fontSize: "0.8rem", marginLeft: "0.5rem" }}>
                      {activity.meta_json.owner as string}/{activity.meta_json.repo as string}
                    </span>
                    <p style={{ margin: "0.2rem 0 0", whiteSpace: "pre-wrap", fontSize: "0.9rem" }}>
                      {activity.meta_json.message_preview as string}
                    </p>
                  </div>
                ) : (
                  <p style={{ margin: "0.35rem 0 0", whiteSpace: "pre-wrap" }}>{activity.body}</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
