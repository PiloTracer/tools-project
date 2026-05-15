import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

type ProjectRow = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  owner_id: string;
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

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Projects
        </Link>
        <h1 style={{ marginTop: "0.5rem" }}>{p.name}</h1>
        <p className="slug" style={{ margin: "0.25rem 0" }}>
          {p.slug}
        </p>
        {p.description ? <p style={{ maxWidth: "40rem" }}>{p.description}</p> : null}
      </div>
      <div className="card wide">
        <span className="pill">Preview</span>
        <p className="muted text-sm" style={{ marginTop: "0.75rem" }}>
          Tasks, tickets, and activity for this project will show up here next. You can already
          use this page as an anchor in the UI while we grow the domain.
        </p>
      </div>
    </div>
  );
}
