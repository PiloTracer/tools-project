import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { ProjectSubNav } from "../ProjectSubNav";
import { NewTaskForm, TaskTable, type TaskRow } from "./TasksClient";

type ProjectRow = {
  id: string;
  name: string;
  membership_role?: string | null;
};

export default async function ProjectTasksPage({
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

  const [tr, cr] = await Promise.all([
    apiServerFetch(`/v1/projects/${id}/tasks`),
    apiServerFetch(`/v1/projects/${id}/components`),
  ]);
  const tasks = tr.ok ? ((await tr.json()) as { items: TaskRow[] }).items : [];
  const components = cr.ok
    ? ((await cr.json()) as { items: { id: string; name: string }[] }).items
    : [];

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
        <h1 style={{ marginTop: "0.25rem" }}>Tasks</h1>
        <ProjectSubNav projectId={id} current="tasks" />
      </div>

      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>New task</h2>
        <NewTaskForm projectId={id} canEdit={canEdit} components={components} />
      </div>

      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>All tasks</h2>
        {tasks.length === 0 ? (
          <p className="muted">No tasks yet.</p>
        ) : (
          <TaskTable tasks={tasks} canEdit={canEdit} />
        )}
      </div>
    </div>
  );
}
