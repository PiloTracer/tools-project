import Link from "next/link";
import { redirect } from "next/navigation";

import { apiServerFetch, fetchMe } from "@/shared/server/session";

import { TemplatesClient } from "./TemplatesClient";

type TemplateCard = {
  id: string;
  key: string;
  name: string;
  team: string | null;
  description: string | null;
  columns: { label: string }[];
};

export default async function TemplatesPage() {
  const me = await fetchMe();
  if (!me) {
    redirect("/login");
  }
  const response = await apiServerFetch("/v1/project-templates");
  const templates = response.ok
    ? ((await response.json()) as { items: TemplateCard[] }).items
    : [];

  return (
    <div className="page-inner stack-lg">
      <div>
        <Link href="/projects" className="muted text-sm">
          ← Projects
        </Link>
        <h1 style={{ marginTop: "0.5rem" }}>Templates</h1>
        <p className="muted">
          Choose a way of working for a new project. Projects you already have keep their board.
        </p>
      </div>
      <TemplatesClient templates={templates} canAdd={me.is_superuser} />
    </div>
  );
}
