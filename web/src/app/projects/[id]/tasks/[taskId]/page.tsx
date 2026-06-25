import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { CopyRefButton } from "@/components/CopyRefButton";
import { TaskDetailEditor } from "@/components/TaskDetailEditor";
import { TaskDiscussion } from "@/components/TaskDiscussion";
import { ProjectSubNav } from "../../ProjectSubNav";

type ProjectRow = {
  id: string;
  name: string;
  membership_role?: string | null;
};

type TaskOut = {
  id: string;
  project_id: string;
  component_id: string | null;
  ref: string | null;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  assignee_id: string | null;
  reporter_id: string;
  due_at: string | null;
  parent_task_id: string | null;
  is_todo: boolean;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
};

type ActivityItem = {
  id: string;
  actor_email: string | null;
  body: string;
  created_at: string;
  parent_activity_id: string | null;
  kind: string;
  meta_json?: Record<string, unknown> | null;
};

export default async function TaskDetailPage({
  params,
}: {
  params: Promise<{ id: string; taskId: string }>;
}) {
  const me = await fetchMe();
  if (!me) {
    redirect("/login");
  }
  const { id: projectId, taskId } = await params;

  const [pr, tr, mr] = await Promise.all([
    apiServerFetch(`/v1/projects/${projectId}`),
    apiServerFetch(`/v1/tasks/${taskId}`),
    apiServerFetch(`/v1/projects/${projectId}/members`),
  ]);
  const members: { user_id: string; email: string; role: string }[] = mr.ok
    ? ((await mr.json()) as { items: { user_id: string; email: string; role: string }[] }).items
    : [];
  if (pr.status === 404) notFound();
  if (!pr.ok) {
    return (
      <div className="page-inner">
        <p className="err">Could not load project.</p>
      </div>
    );
  }
  if (tr.status === 404) notFound();
  if (!tr.ok) {
    return (
      <div className="page-inner">
        <p className="err">Could not load task.</p>
      </div>
    );
  }

  const project = (await pr.json()) as ProjectRow;
  const task = (await tr.json()) as TaskOut;
  if (task.project_id !== projectId) notFound();

  const ar = await apiServerFetch(
    `/v1/projects/${projectId}/activities?subject_type=task&subject_id=${taskId}&limit=50`,
  );
  const activityItems: ActivityItem[] = ar.ok
    ? ((await ar.json()) as { items: ActivityItem[] }).items
    : [];
  activityItems.sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  );

  const role = project.membership_role ?? "";
  const canEdit = ["owner", "maintainer", "contributor"].includes(role) || me.is_superuser;

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href={`/projects/${projectId}/tasks`} className="muted text-sm">
          ← Tasks
        </Link>
        <p className="muted text-sm" style={{ margin: "0.15rem 0" }}>
          Project: <strong>{project.name}</strong>
        </p>
        <h1 style={{ marginTop: "0.25rem", marginBottom: "0.15rem" }}>
          {task.ref ? (
            <span className="muted text-sm" style={{ fontFamily: "var(--font-mono, monospace)" }}>
              {task.ref}
              <CopyRefButton code={task.ref} /> ·{" "}
            </span>
          ) : null}
          {task.title}
        </h1>
        <ProjectSubNav projectId={projectId} current="tasks" />
      </div>

      <TaskDetailEditor task={task} canEdit={canEdit} members={members} />

      <TaskDiscussion projectId={projectId} taskId={taskId} initialItems={activityItems} canEdit={canEdit} />
    </div>
  );
}
