import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { ProjectSubNav } from "../ProjectSubNav";
import { NewTicketForm, TicketTable } from "./TicketsClient";

type TicketRow = {
  id: string;
  ref: string | null;
  title: string;
  status: string;
  priority: string;
  queue_slug: string;
};

type ProjectRow = { membership_role?: string | null };

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
  const items = tr.ok ? ((await tr.json()) as { items: TicketRow[] }).items : [];
  const role = project.membership_role ?? "";
  const canEdit = ["owner", "maintainer", "contributor"].includes(role) || me.is_superuser;
  const canDelete = ["owner", "maintainer"].includes(role) || me.is_superuser;

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Projects
        </Link>
        <h1 style={{ marginTop: "0.5rem" }}>Support tickets</h1>
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
          <TicketTable tickets={items} canEdit={canEdit} canDelete={canDelete} />
        )}
      </div>
    </div>
  );
}
