import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { ProjectSettingsForm } from "./ProjectSettingsForm";
import { ProjectSubNav } from "./ProjectSubNav";

type ProjectRow = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  owner_id: string;
  status: string;
  project_key: string | null;
  membership_role?: string | null;
  created_at: string;
  updated_at: string;
};

export default async function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const me = await fetchMe();
  if (!me) {
    redirect("/login");
  }
  const { id } = await params;
  const r = await apiServerFetch(`/v1/projects/${id}`);
  if (r.status === 404) {
    notFound();
  }
  if (!r.ok) {
    return (
      <div className="page-inner">
        <p className="err">Could not load project.</p>
        <Link href="/projects">← Projects</Link>
      </div>
    );
  }
  const p = (await r.json()) as ProjectRow;
  const role = p.membership_role ?? "";
  const canEditSettings =
    ["owner", "maintainer"].includes(role) || me.is_superuser;

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Projects
        </Link>
        <p className="muted text-sm" style={{ margin: "0.15rem 0" }}>
          Project: <strong>{p.name}</strong>
        </p>
        <h1 style={{ marginTop: "0.25rem" }}>Overview</h1>
        <p className="slug" style={{ margin: "0.25rem 0" }}>
          slug: <code>{p.slug}</code>
          {p.project_key ? (
            <span className="muted" style={{ marginLeft: "0.75rem" }}>
              key <code>{p.project_key}</code>
            </span>
          ) : null}
        </p>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
          <span className="pill">{p.status}</span>
          {p.membership_role ? (
            <span className="muted text-sm">Your role: {p.membership_role}</span>
          ) : null}
        </div>
        {p.description ? <p style={{ maxWidth: "40rem", marginTop: "0.5rem" }}>{p.description}</p> : null}
        <div style={{ marginTop: "1rem" }}>
          <ProjectSubNav projectId={id} current="overview" />
        </div>
      </div>
      <div className="card wide stack">
        <ProjectSettingsForm
          projectId={id}
          initialName={p.name}
          initialDescription={p.description ?? ""}
          initialStatus={p.status || "active"}
          initialProjectKey={p.project_key ?? ""}
          canEdit={canEditSettings}
        />
      </div>
      <div className="card wide stack">
        <span className="pill">Project hub</span>
        <p className="muted text-sm" style={{ marginTop: "0.75rem" }}>
          Use <strong>Members</strong> to invite collaborators, <strong>Components</strong> to group work,
          and <strong>Tasks</strong> for the MVP backlog. Access is enforced by membership roles on the API.
        </p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.5rem" }}>
          <Link className="btn btn-primary" href={`/projects/${id}/tasks`}>
            Open tasks
          </Link>
          <Link className="btn btn-ghost" href={`/projects/${id}/members`}>
            Members
          </Link>
          <Link className="btn btn-ghost" href={`/projects/${id}/components`}>
            Components
          </Link>
          <Link className="btn btn-ghost" href={`/projects/${id}/activity`}>
            Activity
          </Link>
          <Link className="btn btn-ghost" href={`/projects/${id}/tickets`}>
            Tickets
          </Link>
        </div>
      </div>
    </div>
  );
}
