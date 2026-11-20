import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { ProjectSubNav } from "../ProjectSubNav";
import { NewWorkTypeForm, WorkTypeList, type WorkTypeRow } from "./NewWorkTypeForm";

type ProjectRow = {
  id: string;
  name: string;
  membership_role?: string | null;
};

export default async function ProjectWorkTypesPage({
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
  const wr = await apiServerFetch(`/v1/projects/${id}/work-types`);
  const items = wr.ok ? ((await wr.json()) as { items: WorkTypeRow[] }).items : [];
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
        <h1 style={{ marginTop: "0.25rem" }}>Work types</h1>
        <p className="muted text-sm" style={{ margin: "0.35rem 0 0" }}>
          The kind of effort on a task or ticket. A component still names the product area.
          Existing items stay on Programming until someone changes them.
        </p>
        <ProjectSubNav projectId={id} current="work-types" />
      </div>
      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>New work type</h2>
        <NewWorkTypeForm projectId={id} canEdit={canEdit} />
      </div>
      <WorkTypeList items={items} canDelete={canDelete} />
    </div>
  );
}
