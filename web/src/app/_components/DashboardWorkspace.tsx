import Link from "next/link";

type ProjectRow = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
};

export function DashboardWorkspace({
  projects,
  displayName,
}: {
  projects: ProjectRow[];
  displayName: string;
}) {
  const preview = projects.slice(0, 4);
  const more = projects.length - preview.length;

  return (
    <div className="dashboard-tile dashboard-tile--workspace">
      <div className="dashboard-tile-head">
        <div>
          <h2>Workspace</h2>
          <p className="muted text-sm dashboard-tile-tagline">
            Pick up where you left off, {displayName.split(" ")[0] || displayName}.
          </p>
        </div>
        <span className="pill pill-ok dashboard-count" aria-live="polite">
          {projects.length} project{projects.length === 1 ? "" : "s"}
        </span>
      </div>

      <div className="dashboard-actions">
        <Link className="btn btn-primary" href="/projects">
          Open projects
        </Link>
        <Link className="btn btn-secondary" href="/projects/new">
          New project
        </Link>
      </div>

      {projects.length === 0 ? (
        <div className="dashboard-empty">
          <p className="dashboard-empty-title">No projects yet</p>
          <p className="muted text-sm">
            Create a project to group tasks, tickets, and GitHub links. You can add more later.
          </p>
          <Link className="btn btn-primary" href="/projects/new" style={{ marginTop: "0.75rem" }}>
            Create your first project
          </Link>
        </div>
      ) : (
        <>
          <p className="dashboard-section-label">Recent</p>
          <ul className="dash-project-list">
            {preview.map((p) => (
              <li key={p.id}>
                <Link href={`/projects/${p.id}`} className="dash-project-mini">
                  <span className="dash-project-mini-icon" aria-hidden />
                  <span className="dash-project-mini-body">
                    <span className="dash-project-mini-name">{p.name}</span>
                    <span className="dash-project-mini-slug">{p.slug}</span>
                  </span>
                  <span className="dash-project-mini-chevron" aria-hidden>
                    →
                  </span>
                </Link>
              </li>
            ))}
          </ul>
          {more > 0 ? (
            <p className="muted text-sm" style={{ margin: "0.35rem 0 0" }}>
              +{more} more —{" "}
              <Link href="/projects" className="dash-inline-link">
                see all
              </Link>
            </p>
          ) : null}
        </>
      )}
    </div>
  );
}
