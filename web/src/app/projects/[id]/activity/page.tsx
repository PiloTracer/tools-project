import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { ActivityComposer, ActivityFeed, ActivityStreamHint, GithubBackfillSync } from "./ActivityClient";
import { ProjectSubNav } from "../ProjectSubNav";

type ActivityRow = {
  id: string;
  actor_email: string | null;
  kind: string;
  body: string;
  subject_type: string;
  subject_id?: string;
  created_at: string;
  parent_activity_id?: string | null;
  is_internal?: boolean;
  meta_json?: Record<string, unknown> | null;
  subject_ref?: string | null;
  subject_title?: string | null;
};

type ProjectRow = {
  id: string;
  name: string;
  membership_role?: string | null;
};

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
  let items: ActivityRow[] = [];
  let activityHasMore = false;
  let activityTotal: number | null = null;
  let activityError: string | null = null;
  if (ar.ok) {
    const data = (await ar.json()) as {
      items?: ActivityRow[];
      total?: number;
      has_more?: boolean;
    };
    items = data.items ?? [];
    activityHasMore = Boolean(data.has_more);
    activityTotal = data.total ?? null;
  } else {
    activityError = `Could not load activity (HTTP ${ar.status}).`;
  }
  const role = project.membership_role ?? "";
  const canPost = ["owner", "maintainer", "contributor"].includes(role) || me.is_superuser;
  // GitHub backfill is owner/maintainer-only in the API; do not show the
  // control to contributors who would only get a 403.
  const canSyncGithub = ["owner", "maintainer"].includes(role) || me.is_superuser;

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Projects
        </Link>
        <p className="muted text-sm" style={{ margin: "0.15rem 0" }}>
          Project: <strong>{project.name}</strong>
        </p>
        <h1 style={{ marginTop: "0.25rem" }}>Activity</h1>
        <ProjectSubNav projectId={id} current="activity" />
      </div>
      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>New post</h2>
        <ActivityComposer projectId={id} canPost={canPost} />
      </div>
      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Feed</h2>
        {canSyncGithub ? <GithubBackfillSync projectId={id} /> : null}
        <ActivityStreamHint projectId={id} initialLatestId={items[0]?.id ?? null} />
        <ActivityFeed
          initial={items}
          projectId={id}
          canPost={canPost}
          initialHasMore={activityHasMore}
          initialTotal={activityTotal}
          initialError={activityError}
        />
      </div>
    </div>
  );
}
