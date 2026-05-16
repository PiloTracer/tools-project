import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { ProjectSubNav } from "../ProjectSubNav";
import { NewComponentForm } from "./NewComponentForm";

type ComponentRow = {
  id: string;
  name: string;
  description: string | null;
};

type ProjectRow = {
  id: string;
  name: string;
  membership_role?: string | null;
};

export default async function ProjectComponentsPage({
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
  const cr = await apiServerFetch(`/v1/projects/${id}/components`);
  const items = cr.ok ? ((await cr.json()) as { items: ComponentRow[] }).items : [];

  const role = project.membership_role ?? "";
  const canEdit = ["owner", "maintainer", "contributor"].includes(role) || me.is_superuser;

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Projects
        </Link>
        <p className="muted text-sm" style={{ margin: "0.15rem 0" }}>
          Project: <strong>{project.name}</strong>
        </p>
        <h1 style={{ marginTop: "0.25rem" }}>Components</h1>
        <ProjectSubNav projectId={id} current="components" />
      </div>

      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>New component</h2>
        <NewComponentForm projectId={id} canEdit={canEdit} />
      </div>

      <ul className="project-list">
        {items.length === 0 ? (
          <li className="muted">No components yet.</li>
        ) : (
          items.map((c) => (
            <li key={c.id}>
              <div className="project-row">
                <h3>{c.name}</h3>
                {c.description ? (
                  <p className="muted text-sm" style={{ margin: "0.35rem 0 0" }}>
                    {c.description}
                  </p>
                ) : null}
              </div>
            </li>
          ))
        )}
      </ul>
    </div>
  );
}
