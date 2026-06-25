import Link from "next/link";
import { redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";
import { CopyRefButton } from "@/components/CopyRefButton";
import { WatchButtons } from "./WatchButtons";

type TodayItem = {
  task: {
    id: string;
    title: string;
    status: string;
    due_at: string | null;
    project_id: string;
    ref: string | null;
  };
  project_name: string;
};

type WatchedTicketRow = {
  ticket: {
    id: string;
    title: string;
    status: string;
    project_id: string;
    ref: string | null;
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

type MyStats = {
  open_tasks: number;
  overdue_tasks: number;
  done_this_week: number;
  inbox_count: number;
  mention_count: number;
  open_tickets: number;
};

export default async function TodayPage() {
  const me = await fetchMe();
  if (!me) {
    redirect("/login");
  }

  const [tr, mr, sr] = await Promise.all([
    apiServerFetch("/v1/me/today"),
    apiServerFetch("/v1/me/mentions"),
    apiServerFetch("/v1/stats/me"),
  ]);
  const todayJson = tr.ok ? ((await tr.json()) as { items: TodayItem[]; watched_tickets?: WatchedTicketRow[] }) : { items: [], watched_tickets: [] };
  const today = todayJson.items ?? [];
  const watchedTickets = todayJson.watched_tickets ?? [];
  const mentions = mr.ok ? ((await mr.json()) as { items: MentionItem[] }).items : [];
  const stats: MyStats | null = sr.ok ? (await sr.json()) as MyStats : null;

  return (
    <div className="page-inner">
      <header className="page-header">
        <div className="page-header__text">
          <span className="pill">My focus</span>
          <h1>Today</h1>
          <p className="muted text-sm page-header__lead">
            Assigned tasks with due dates in the next week, watched items, and @mentions.
          </p>
        </div>
        <div className="page-header__actions">
          <Link className="btn btn-primary" href="/inbox">
            Inbox
          </Link>
        </div>
      </header>

      {stats ? (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
            gap: "0.75rem",
            marginBottom: "1.5rem",
          }}
        >
          <StatCard label="Open tasks" value={stats.open_tasks} secondary={stats.overdue_tasks > 0 ? `${stats.overdue_tasks} overdue` : undefined} />
          <StatCard label="Done this week" value={stats.done_this_week} />
          <StatCard label="Open tickets" value={stats.open_tickets} />
          <StatCard label="Inbox" value={stats.inbox_count} secondary={stats.mention_count > 0 ? `${stats.mention_count} recent mentions` : undefined} />
        </div>
      ) : null}

      <div className="page-body stack-lg">
        <section className="card wide stack">
          <h2 style={{ marginTop: 0 }}>Upcoming assigned tasks</h2>
          {today.length === 0 ? (
            <p className="muted">Nothing due in the window, or no assignee+due set.</p>
          ) : (
            <ul className="stack" style={{ listStyle: "none", padding: 0, gap: "0.5rem" }}>
              {today.map((row) => (
                <li key={row.task.id}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <Link href={`/projects/${row.task.project_id}/tasks`} className="project-row" style={{ flex: 1 }}>
                      <strong>
                        {row.task.ref ? (
                          <span className="muted" style={{ fontFamily: "var(--font-mono, monospace)", fontSize: "0.75rem", marginRight: "0.35rem" }}>
                            {row.task.ref}
                            <CopyRefButton code={row.task.ref} />
                          </span>
                        ) : null}
                        {row.task.title}
                      </strong>
                      <span className="muted text-sm" style={{ marginLeft: "0.5rem" }}>
                        {row.project_name} · {row.task.status}
                        {row.task.due_at
                          ? ` · due ${new Date(row.task.due_at).toLocaleDateString()}`
                          : ""}
                      </span>
                    </Link>
                    <WatchButtons subjectType="task" subjectId={row.task.id} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        {watchedTickets.length > 0 ? (
          <section className="card wide stack">
            <h2 style={{ marginTop: 0 }}>Watched tickets</h2>
            <ul className="stack" style={{ listStyle: "none", padding: 0, gap: "0.5rem" }}>
              {watchedTickets.map((row) => (
                <li key={row.ticket.id}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <Link
                      href={`/projects/${row.ticket.project_id}/tickets/${row.ticket.id}`}
                      className="project-row"
                      style={{ flex: 1 }}
                    >
                      <strong>
                        {row.ticket.ref ? (
                          <span
                            className="muted"
                            style={{ fontFamily: "var(--font-mono, monospace)", fontSize: "0.75rem", marginRight: "0.35rem" }}
                          >
                            {row.ticket.ref}
                            <CopyRefButton code={row.ticket.ref} />
                          </span>
                        ) : null}
                        {row.ticket.title}
                      </strong>
                      <span className="muted text-sm" style={{ marginLeft: "0.5rem" }}>
                        {row.project_name} · {row.ticket.status}
                      </span>
                    </Link>
                    <WatchButtons subjectType="ticket" subjectId={row.ticket.id} />
                  </div>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

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
                <div className="text-sm muted" suppressHydrationWarning>
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

function StatCard({ label, value, secondary }: { label: string; value: number; secondary?: string }) {
  return (
    <div
      style={{
        background: "var(--surface-elevated)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding: "1.25rem 1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.15rem",
      }}
    >
      <span className="text-sm muted">{label}</span>
      <span style={{ fontSize: "1.75rem", fontWeight: 700, lineHeight: 1.2 }}>
        {value}
      </span>
      {secondary ? <span className="text-xs muted">{secondary}</span> : null}
    </div>
  );
}
