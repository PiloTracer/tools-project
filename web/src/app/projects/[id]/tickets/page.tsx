import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { ProjectSubNav } from "../ProjectSubNav";
import { NewTicketForm, TicketsView, type TicketQueueRow } from "./TicketsClient";

type ProjectRow = {
  id: string;
  name: string;
  membership_role?: string | null;
};

export default async function ProjectTicketsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const me = await fetchMe();
  if (!me) {
    redirect("/login");
  }
  const { id } = await params;
  const pr = await apiServerFetch(`/v1/projects/${id}`);
  if (pr.status === 404) {
    notFound();
  }
  if (!pr.ok) {
    return (
      <div className="page-inner">
        <p className="err">Could not load project.</p>
      </div>
    );
  }
  const project = (await pr.json()) as ProjectRow;
  const tr = await apiServerFetch(`/v1/projects/${id}/tickets`);
  const items = tr.ok ? ((await tr.json()) as { items: TicketQueueRow[] }).items : [];
  const role = project.membership_role ?? "";
  const canEdit = ["owner", "maintainer", "contributor"].includes(role) || me.is_superuser;
  const canDelete = ["owner", "maintainer"].includes(role) || me.is_superuser;

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Projects
        </Link>
        <p className="muted text-sm" style={{ margin: "0.15rem 0" }}>
          Project: <strong>{project.name}</strong>
        </p>
        <h1 style={{ marginTop: "0.25rem" }}>Support ticket queue</h1>
        <p className="muted text-sm" style={{ margin: "0.35rem 0 0" }}>
          Open cases first, oldest first (triage). Open a row for the full case: description and threaded-style comments via
          activity.
        </p>
        <p className="muted text-sm" style={{ margin: "0.25rem 0 0" }}>
          Age signal: <span style={{ color: "var(--accent-warn, #c98300)" }}>○ &gt; 7 d</span>{" "}
          ·{" "}
          <span style={{ color: "var(--accent-bad, #c0392b)", fontWeight: 600 }}>● &gt; 14 d</span>{" "}
          (terminal tickets are not flagged).
        </p>
        <ProjectSubNav projectId={id} current="tickets" />
      </div>
      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>New ticket</h2>
        <NewTicketForm projectId={id} canEdit={canEdit} />
      </div>
      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Queue</h2>
        {items.length === 0 ? (
          <p className="muted">No tickets.</p>
        ) : (
          <TicketsView projectId={id} tickets={items} canEdit={canEdit} canDelete={canDelete} />
        )}
      </div>
    </div>
  );
}
