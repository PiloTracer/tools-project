import Link from "next/link";
import { redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

type TodayItem = {
  task: {
    id: string;
    title: string;
    status: string;
    due_at: string | null;
    project_id: string;
  };
  project_name: string;
};

type MentionItem = {
  id: string;
  project_id: string;
  project_name: string;
  excerpt: string;
  created_at: string;
};

export default async function TodayPage() {
  const me = await fetchMe();
  if (!me) {
    redirect("/login");
  }

  const [tr, mr] = await Promise.all([
    apiServerFetch("/v1/me/today"),
    apiServerFetch("/v1/me/mentions"),
  ]);
  const today = tr.ok ? ((await tr.json()) as { items: TodayItem[] }).items : [];
  const mentions = mr.ok ? ((await mr.json()) as { items: MentionItem[] }).items : [];

  return (
    <div className="page-inner">
      <header className="page-header">
        <div className="page-header__text">
          <span className="pill">My focus</span>
          <h1>Today</h1>
          <p className="muted text-sm page-header__lead">
            Assigned tasks with due dates in the next week (UTC), plus @mentions from activity.
          </p>
        </div>
      </header>

      <div className="page-body stack-lg">
        <section className="card wide stack">
          <h2 style={{ marginTop: 0 }}>Upcoming assigned tasks</h2>
          {today.length === 0 ? (
            <p className="muted">Nothing due in the window, or no assignee+due set.</p>
          ) : (
            <ul className="stack" style={{ listStyle: "none", padding: 0, gap: "0.5rem" }}>
              {today.map((row) => (
                <li key={row.task.id}>
                  <Link href={`/projects/${row.task.project_id}/tasks`} className="project-row">
                    <strong>{row.task.title}</strong>
                    <span className="muted text-sm" style={{ marginLeft: "0.5rem" }}>
                      {row.project_name} · {row.task.status}
                      {row.task.due_at
                        ? ` · due ${new Date(row.task.due_at).toLocaleDateString()}`
                        : ""}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Mentions</h2>
        {mentions.length === 0 ? (
          <p className="muted">
            No @mentions yet. Post activity with <code>@email@example.com</code> on a project you belong
            to.
          </p>
        ) : (
          <ul className="stack" style={{ listStyle: "none", padding: 0, gap: "0.75rem" }}>
            {mentions.map((m) => (
              <li key={m.id} className="card" style={{ padding: "0.65rem 1rem" }}>
                <div className="text-sm muted">
                  {m.project_name} · {new Date(m.created_at).toLocaleString()}
                </div>
                <p style={{ margin: "0.35rem 0 0" }}>{m.excerpt}</p>
                <Link className="text-sm" href={`/projects/${m.project_id}/activity`}>
                  Open activity →
                </Link>
              </li>
            ))}
          </ul>
        )}
        </section>

        <p>
          <Link href="/projects">← Projects</Link>
        </p>
      </div>
    </div>
  );
}
