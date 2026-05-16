import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { InviteMemberForm } from "./InviteMemberForm";
import { ProjectSubNav } from "../ProjectSubNav";

type MemberRow = {
  user_id: string;
  email: string;
  display_name: string | null;
  role: string;
  created_at: string;
};

type ProjectRow = {
  id: string;
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
  const mr = await apiServerFetch(`/v1/projects/${id}/members`);
  const members = mr.ok ? ((await mr.json()) as { items: MemberRow[] }).items : [];

  const role = project.membership_role ?? "";
  const canInvite = ["owner", "maintainer"].includes(role) || me.is_superuser;

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Projects
        </Link>
        <h1 style={{ marginTop: "0.5rem" }}>Members</h1>
        <ProjectSubNav projectId={id} current="members" />
      </div>

      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Invite</h2>
        <InviteMemberForm projectId={id} canInvite={canInvite} />
      </div>

      <div className="card wide">
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
              <th style={{ padding: "0.5rem 0" }}>Email</th>
              <th>Name</th>
              <th>Role</th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.user_id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: "0.35rem 0" }}>{m.email}</td>
                <td>{m.display_name ?? "—"}</td>
                <td>
                  <span className="pill">{m.role}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
