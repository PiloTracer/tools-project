import Link from "next/link";
import { redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

type ProjectRow = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
  status?: string;
};

function statusPillClass(status: string | undefined): string {
  if (!status) return "pill";
  const s = status.toLowerCase();
  if (s === "active") return "pill pill-ok";
  if (s === "archived") return "pill pill-muted";
  return "pill";
}

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
    <div className="page-inner">
      <header className="page-header">
        <div className="page-header__text">
          <span className="pill">Your workspace</span>
          <h1>Projects</h1>
          <p className="muted page-header__lead">
            Create a project for each initiative or product line.
          </p>
        </div>
        <div className="page-header__actions">
          <Link className="btn btn-primary" href="/projects/new">
            New project
          </Link>
        </div>
      </header>

      <section className="page-body" aria-label="Project list">
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
                  <div className="project-row__titleline">
                    <h3>{p.name}</h3>
                    {p.status ? (
                      <span className={statusPillClass(p.status)}>{p.status}</span>
                    ) : null}
                  </div>
                  <span className="slug">{p.slug}</span>
                  {p.description ? (
                    <p className="muted text-sm project-row__desc">
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
      </section>
    </div>
  );
}
