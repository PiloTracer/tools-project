import Link from "next/link";
import { apiServerFetch, fetchMe } from "@/shared/server/session";
import { redirect } from "next/navigation";

type ProjectRow = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  status: string;
  membership_role?: string | null;
};

export default async function ClientDashboardPage() {
  const me = await fetchMe();
  if (!me) {
    redirect("/client/login");
  }

  const res = await apiServerFetch("/v1/me/client/projects");
  const projects: ProjectRow[] = res.ok ? (await res.json()).items : [];

  return (
    <div className="page-inner">
      <main className="card stack" style={{ maxWidth: "48rem", margin: "2rem auto" }}>
        <h1>Client Dashboard</h1>
        <p className="muted text-sm">
          Welcome, <strong>{me.display_name || me.email}</strong>. Here are the projects you have access to.
        </p>

        {projects.length === 0 ? (
          <p className="muted">You do not have access to any projects yet.</p>
        ) : (
          <ul className="stack-sm" style={{ listStyle: "none", padding: 0 }}>
            {projects.map((project) => (
              <li key={project.id} className="card">
                <Link href={`/client/projects/${project.id}`} className="block">
                  <strong>{project.name}</strong>
                  {project.description ? (
                    <p className="muted text-sm">{project.description}</p>
                  ) : null}
                  <p className="muted text-sm">Role: {project.membership_role || "view"}</p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}
