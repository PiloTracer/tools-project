import Link from "next/link";
import { redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { InboxClient } from "./InboxClient";

type InboxItem = {
  id: string;
  body_md: string;
  triaged_to_type: string | null;
  triaged_to_id: string | null;
  created_at: string;
};

type ProjectItem = {
  id: string;
  name: string;
  status: string;
};

export default async function InboxPage() {
  const me = await fetchMe();
  if (!me) redirect("/login");

  let items: InboxItem[] = [];
  let projects: ProjectItem[] = [];

  const [ir, pr] = await Promise.all([
    apiServerFetch("/v1/inbox"),
    apiServerFetch("/v1/projects"),
  ]);
  if (ir.ok) {
    items = ((await ir.json()) as { items: InboxItem[] }).items;
  }
  if (pr.ok) {
    projects = ((await pr.json()) as { items: ProjectItem[] }).items.filter(
      (p) => p.status !== "archived",
    );
  }

  return (
    <div className="page-inner">
      <header className="page-header">
        <div className="page-header__text">
          <span className="pill">Quick capture</span>
          <h1>Inbox</h1>
          <p className="muted text-sm page-header__lead">
            Capture thoughts, then triage into projects as tasks or tickets.
          </p>
        </div>
      </header>

      <div className="page-body stack-lg">
        <InboxClient initialItems={items} projects={projects} />
        <p>
          <Link href="/">← Home</Link>
        </p>
      </div>
    </div>
  );
}
