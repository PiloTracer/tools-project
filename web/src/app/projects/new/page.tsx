import Link from "next/link";
import { redirect } from "next/navigation";

import { NewProjectForm } from "@/components/NewProjectForm";
import { fetchMe } from "@/shared/server/session";

export default async function NewProjectPage() {
  const me = await fetchMe();
  if (!me) {
    redirect("/login");
  }

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Projects
        </Link>
        <h1 style={{ marginTop: "0.5rem" }}>New project</h1>
        <p className="muted">Name is required. Slug is optional (lowercase, hyphens).</p>
      </div>
      <div className="card wide" style={{ maxWidth: "36rem" }}>
        <NewProjectForm />
      </div>
    </div>
  );
}
