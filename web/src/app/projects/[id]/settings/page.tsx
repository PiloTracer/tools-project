import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { ProjectSettingsForm } from "../ProjectSettingsForm";
import { ProjectSubNav } from "../ProjectSubNav";
import { GitHubSettingsForm } from "./GitHubSettingsForm";

type ProjectRow = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  owner_id: string;
  status: string;
  project_key: string | null;
  membership_role?: string | null;
};

type GithubLinkRow = {
  id: string;
  owner: string;
  repo: string;
  last_synced_at: string | null;
};

export default async function ProjectSettingsPage({
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
        <Link href="/projects">← Projects</Link>
      </div>
    );
  }
  const project = (await pr.json()) as ProjectRow;

  const role = project.membership_role ?? "";
  const canEditSettings =
    ["owner", "maintainer"].includes(role) || me.is_superuser;

  const linksRes = await apiServerFetch(`/v1/projects/${id}/github/links`);
  const links: GithubLinkRow[] = linksRes.ok ? await linksRes.json() : [];

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Projects
        </Link>
        <p className="muted text-sm" style={{ margin: "0.15rem 0" }}>
          Project: <strong>{project.name}</strong>
        </p>
        <h1 style={{ marginTop: "0.25rem" }}>Settings</h1>
        <ProjectSubNav projectId={id} current="settings" />
      </div>

      <div className="card wide stack">
        <ProjectSettingsForm
          projectId={id}
          initialName={project.name}
          initialDescription={project.description ?? ""}
          initialStatus={project.status || "active"}
          initialProjectKey={project.project_key ?? ""}
          canEdit={canEditSettings}
        />
      </div>

      <div className="card wide stack">
        <GitHubSettingsForm
          projectId={id}
          links={links}
          canEdit={canEditSettings}
        />
      </div>
    </div>
  );
}
