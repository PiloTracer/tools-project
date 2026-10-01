// TODO M3-T7: Client-side project detail view (filtered tasks/activities for client
// participants) is deferred — needs the dual auth system working first.

import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { ProgressBar } from "@/components/PlanTaskBody";
import { ProjectSettingsForm } from "./ProjectSettingsForm";
import type { MilestoneRow } from "./tasks/MilestoneGroups";
import { ProjectSubNav } from "./ProjectSubNav";
import { ProjectDashboard } from "./ProjectDashboard";

type ProjectRow = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  owner_id: string;
  status: string;
  project_key: string | null;
  github_task_registry_enabled: boolean;
  auto_prefix_enabled: boolean;
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
  const mlr = await apiServerFetch(`/v1/projects/${id}/milestones`);
  const milestones: MilestoneRow[] = mlr.ok
    ? ((await mlr.json()) as { items: MilestoneRow[] }).items
    : [];
  const orderedMilestones = [...milestones].sort((a, b) => a.sort_order - b.sort_order);
  const activeMilestone = orderedMilestones.find((m) => m.status === "active") ?? null;
  const planTaskTotal = orderedMilestones.reduce((sum, m) => sum + m.task_total, 0);
  const planTaskDone = orderedMilestones.reduce((sum, m) => sum + m.task_done, 0);
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
          initialRegistryEnabled={p.github_task_registry_enabled ?? false}
          initialAutoPrefix={p.auto_prefix_enabled ?? false}
          canEdit={canEditSettings}
        />
      </div>
      {orderedMilestones.length > 0 ? (
        <div className="card wide stack">
          <div style={{ display: "flex", alignItems: "baseline", gap: "0.6rem", flexWrap: "wrap" }}>
            <h2 style={{ margin: 0 }}>Milestones</h2>
            <span className="muted text-sm">
              {orderedMilestones.length} planned
              {planTaskTotal > 0 ? ` · ${planTaskDone}/${planTaskTotal} tasks done` : ""}
            </span>
            {activeMilestone ? (
              <span className="pill pill-ok" style={{ fontSize: "0.65rem" }}>
                current: {activeMilestone.key ?? activeMilestone.name}
              </span>
            ) : null}
            <Link className="btn btn-ghost text-sm" href={`/projects/${id}/tasks`} style={{ marginLeft: "auto" }}>
              Open tasks by milestone
            </Link>
          </div>
          <ul className="stack" style={{ listStyle: "none", paddingLeft: 0, gap: "0.5rem", marginTop: "0.25rem" }}>
            {orderedMilestones.map((m) => {
              const pct = m.task_total > 0 ? Math.round((m.task_done / m.task_total) * 100) : 0;
              return (
                <li key={m.id} className="stack" style={{ gap: "0.25rem" }}>
                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                    {m.key ? (
                      <span
                        className="pill"
                        style={{ fontSize: "0.7rem", fontFamily: "var(--font-mono, monospace)" }}
                      >
                        {m.key}
                      </span>
                    ) : null}
                    <Link href={`/projects/${id}/tasks?milestone=${m.id}`} style={{ fontWeight: 600 }}>
                      {m.name}
                    </Link>
                    <span className="pill" style={{ fontSize: "0.65rem" }}>
                      {m.status}
                    </span>
                    {m.plan_state === "obsolete" ? (
                      <span className="pill pill-muted" style={{ fontSize: "0.65rem" }}>
                        obsolete
                      </span>
                    ) : null}
                    <span className="muted text-sm" style={{ marginLeft: "auto" }}>
                      {m.task_done}/{m.task_total}
                    </span>
                  </div>
                  <div style={{ maxWidth: "26rem" }}>
                    <ProgressBar percent={pct} />
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
      <ProjectDashboard projectId={id} projectSlug={p.slug} />
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
