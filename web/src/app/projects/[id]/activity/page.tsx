import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { ActivityComposer, ActivityFeed, ActivityStreamHint } from "./ActivityClient";
import { ProjectSubNav } from "../ProjectSubNav";

type ActivityRow = {
  id: string;
  actor_email: string | null;
  kind: string;
  body: string;
  subject_type: string;
  created_at: string;
};

type ProjectRow = { membership_role?: string | null };

export default async function ProjectActivityPage({
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
  const ar = await apiServerFetch(`/v1/projects/${id}/activities`);
  const items = ar.ok ? ((await ar.json()) as { items: ActivityRow[] }).items : [];
  const role = project.membership_role ?? "";
  const canPost = ["owner", "maintainer", "contributor"].includes(role) || me.is_superuser;

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Projects
        </Link>
        <h1 style={{ marginTop: "0.5rem" }}>Activity</h1>
        <ProjectSubNav projectId={id} current="activity" />
      </div>
      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>New post</h2>
        <ActivityComposer projectId={id} canPost={canPost} />
      </div>
      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Feed</h2>
        <ActivityStreamHint projectId={id} />
        <ActivityFeed initial={items} />
      </div>
    </div>
  );
}
