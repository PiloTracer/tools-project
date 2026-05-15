import Link from "next/link";
import { redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

type ProjectRow = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
};

export default async function ProjectsPage() {
  const me = await fetchMe();
  if (!me) {
    redirect("/login");
  }

  const r = await apiServerFetch("/v1/projects");
  if (!r.ok) {
    return (
      <div className="page-inner">
        <p className="err">Could not load projects ({r.status}).</p>
        <Link href="/">← Home</Link>
      </div>
    );
  }
  const data = (await r.json()) as { items: ProjectRow[] };
  const items = data.items ?? [];

  return (
    <div className="page-inner stack-lg">
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-end", gap: "1rem" }}>
        <div style={{ flex: "1 1 200px" }}>
          <span className="pill">Your workspace</span>
          <h1 style={{ marginTop: "0.65rem" }}>Projects</h1>
          <p className="muted">Create a project for each initiative or product line.</p>
        </div>
        <Link className="btn btn-primary" href="/projects/new">
          New project
        </Link>
      </div>

      {items.length === 0 ? (
        <div className="card wide">
          <p className="muted">No projects yet.</p>
          <Link className="btn btn-primary" href="/projects/new">
            Create your first project
          </Link>
        </div>
      ) : (
        <ul className="project-list">
          {items.map((p) => (
            <li key={p.id}>
              <Link href={`/projects/${p.id}`} className="project-row">
                <h3>{p.name}</h3>
                <span className="slug">{p.slug}</span>
                {p.description ? (
                  <p className="muted text-sm" style={{ margin: "0.35rem 0 0" }}>
                    {p.description.length > 160
                      ? `${p.description.slice(0, 160)}…`
                      : p.description}
                  </p>
                ) : null}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
