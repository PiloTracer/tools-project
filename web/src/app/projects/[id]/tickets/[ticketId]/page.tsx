import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { ProjectSubNav } from "../../ProjectSubNav";
import { TicketDiscussion, type ActivityItem } from "./TicketDiscussion";

type ProjectRow = {
  id: string;
  name: string;
  membership_role?: string | null;
};

type TicketOut = {
  id: string;
  project_id: string;
  ref: string | null;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  queue_slug: string;
  requester_email: string | null;
  reporter_id: string;
  assignee_id: string | null;
  first_response_at: string | null;
  resolved_at: string | null;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
};

const IMG_LINE = /^!\[([^\]]*)\]\((\/api\/attachments\/[0-9a-fA-F-]+)\)\s*$/;

function TicketDescriptionBody({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <div className="stack" style={{ gap: "0.65rem" }}>
      {lines.map((line, i) => {
        const m = line.match(IMG_LINE);
        if (m) {
          return (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              key={i}
              src={m[2]}
              alt={m[1] || "image"}
              style={{ maxWidth: "min(100%, 720px)", height: "auto", borderRadius: 8 }}
            />
          );
        }
        if (line.trim() === "") {
          return <div key={i} style={{ minHeight: "0.35rem" }} />;
        }
        return (
          <span key={i} style={{ whiteSpace: "pre-wrap", display: "block" }}>
            {line}
          </span>
        );
      })}
    </div>
  );
}

export default async function TicketDetailPage({
  params,
}: {
  params: Promise<{ id: string; ticketId: string }>;
}) {
  const me = await fetchMe();
  if (!me) {
    redirect("/login");
  }
  const { id: projectId, ticketId } = await params;

  const [pr, tr] = await Promise.all([
    apiServerFetch(`/v1/projects/${projectId}`),
    apiServerFetch(`/v1/tickets/${ticketId}`),
  ]);
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
  if (tr.status === 404) {
    notFound();
  }
  if (!tr.ok) {
    return (
      <div className="page-inner">
        <p className="err">Could not load ticket.</p>
      </div>
    );
  }

  const project = (await pr.json()) as ProjectRow;
  const ticket = (await tr.json()) as TicketOut;
  if (ticket.project_id !== projectId) {
    notFound();
  }

  const ar = await apiServerFetch(
    `/v1/projects/${projectId}/activities?subject_type=ticket&subject_id=${ticketId}&limit=50`,
  );
  const activityItemsRaw: ActivityItem[] = ar.ok
    ? ((await ar.json()) as { items: ActivityItem[] }).items
    : [];
  const activityItems = [...activityItemsRaw].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  );

  const role = project.membership_role ?? "";
  const canEdit = ["owner", "maintainer", "contributor"].includes(role) || me.is_superuser;

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href={`/projects/${projectId}/tickets`} className="muted text-sm">
          ← Ticket queue
        </Link>
        <p className="muted text-sm" style={{ margin: "0.15rem 0" }}>
          Project: <strong>{project.name}</strong>
        </p>
        <h1 style={{ marginTop: "0.25rem", marginBottom: "0.15rem" }}>
          {ticket.ref ? <span className="muted text-sm" style={{ fontFamily: "var(--font-mono, monospace)" }}>{ticket.ref} · </span> : null}
          {ticket.title}
        </h1>
        <ProjectSubNav projectId={projectId} current="tickets" />
      </div>

      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Case</h2>
        <dl
          className="stack text-sm"
          style={{ margin: 0, display: "grid", gridTemplateColumns: "auto 1fr", gap: "0.35rem 1rem", alignItems: "baseline" }}
        >
          <dt className="muted">Status</dt>
          <dd style={{ margin: 0 }}>
            <span className="pill">{ticket.status}</span>
          </dd>
          <dt className="muted">Priority</dt>
          <dd style={{ margin: 0 }}>{ticket.priority}</dd>
          <dt className="muted">Queue</dt>
          <dd style={{ margin: 0 }}>
            <span className="pill">{ticket.queue_slug}</span>
          </dd>
          {ticket.requester_email ? (
            <>
              <dt className="muted">Requester</dt>
              <dd style={{ margin: 0 }}>{ticket.requester_email}</dd>
            </>
          ) : null}
          <dt className="muted">Opened</dt>
          <dd style={{ margin: 0 }}>{new Date(ticket.created_at).toLocaleString()}</dd>
          {ticket.first_response_at ? (
            <>
              <dt className="muted">First response</dt>
              <dd style={{ margin: 0 }}>{new Date(ticket.first_response_at).toLocaleString()}</dd>
            </>
          ) : null}
          {ticket.resolved_at ? (
            <>
              <dt className="muted">Resolved</dt>
              <dd style={{ margin: 0 }}>{new Date(ticket.resolved_at).toLocaleString()}</dd>
            </>
          ) : null}
        </dl>
        <div>
          <h3 className="text-sm muted" style={{ margin: "0.75rem 0 0.35rem" }}>
            Description
          </h3>
          {ticket.description ? (
            <TicketDescriptionBody text={ticket.description} />
          ) : (
            <p className="muted text-sm">No description.</p>
          )}
        </div>
      </div>

      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Discussion</h2>
        <TicketDiscussion
          projectId={projectId}
          ticketId={ticketId}
          initialItems={activityItems}
          canEdit={canEdit}
        />
      </div>
    </div>
  );
}
