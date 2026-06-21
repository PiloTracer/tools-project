import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { InviteMemberForm } from "./InviteMemberForm";
import { MemberList } from "./MemberList";
import { ProjectSubNav } from "../ProjectSubNav";

type ProjectRow = {
  id: string;
  name: string;
  membership_role?: string | null;
};

export default async function ProjectMembersPage({
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
  const canManage = ["owner", "maintainer"].includes(role) || me.is_superuser;

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Projects
        </Link>
        <p className="muted text-sm" style={{ margin: "0.15rem 0" }}>
          Project: <strong>{project.name}</strong>
        </p>
        <h1 style={{ marginTop: "0.25rem" }}>Members</h1>
        <ProjectSubNav projectId={id} current="members" />
      </div>

      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Invite</h2>
        <InviteMemberForm projectId={id} canInvite={canManage} />
      </div>

      <MemberList projectId={id} canManage={canManage} />
    </div>
  );
}
