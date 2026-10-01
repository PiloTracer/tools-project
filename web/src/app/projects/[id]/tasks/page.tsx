import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { ProjectSubNav } from "../ProjectSubNav";
import { NewTaskForm, TasksView, type TaskRow } from "./TasksClient";
import type { MilestoneRow } from "./MilestoneGroups";

type ProjectRow = {
  id: string;
  name: string;
  membership_role?: string | null;
};

export default async function ProjectTasksPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
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

  const [tr, cr, mr, mlr] = await Promise.all([
    apiServerFetch(`/v1/projects/${id}/tasks?limit=500`),
    apiServerFetch(`/v1/projects/${id}/components`),
    apiServerFetch(`/v1/projects/${id}/members`),
    apiServerFetch(`/v1/projects/${id}/milestones`),
  ]);
  const tasks = tr.ok ? ((await tr.json()) as { items: TaskRow[] }).items : [];
  const components = cr.ok
    ? ((await cr.json()) as { items: { id: string; name: string }[] }).items
    : [];
  const members: { user_id: string; email: string; role: string }[] = mr.ok
    ? ((await mr.json()) as { items: { user_id: string; email: string; role: string }[] }).items
    : [];
  const milestones: MilestoneRow[] = mlr.ok
    ? ((await mlr.json()) as { items: MilestoneRow[] }).items
    : [];

  const sp = (await searchParams) ?? {};
  const initialMilestone = typeof sp.milestone === "string" ? sp.milestone : "";
  const initialPlanState =
    typeof sp.plan_state === "string" && ["active", "obsolete", "all"].includes(sp.plan_state)
      ? sp.plan_state
      : "active";

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
          <>
            <p className="muted text-sm" style={{ marginTop: 0 }}>
              {tasks.length} task(s)
              {milestones.length > 0 ? ` · ${milestones.length} milestone(s)` : ""} — group by
              milestone, or switch to the board/table view.
            </p>
            <TasksView
              projectId={id}
              tasks={tasks}
              canEdit={canEdit}
              members={members}
              milestones={milestones}
              initialMilestone={initialMilestone}
              initialPlanState={initialPlanState}
            />
          </>
        )}
      </div>
    </div>
  );
}
