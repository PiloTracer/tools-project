import Link from "next/link";

export function ProjectSubNav({
  projectId,
  current,
}: {
  projectId: string;
  current:
    | "overview"
    | "members"
    | "components"
    | "tasks"
    | "activity"
    | "tickets"
    | "github"
    | "settings";
}) {
  const base = `/projects/${projectId}`;
  const cls = (key: typeof current) =>
    current === key ? "pill" : "muted text-sm";
  return (
    <nav
      className="sub-nav"
      aria-label="Project sections"
      style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}
    >
      <Link href={base} className={cls("overview")}>
        Overview
      </Link>
      <Link href={`${base}/members`} className={cls("members")}>
        Members
      </Link>
      <Link href={`${base}/components`} className={cls("components")}>
        Components
      </Link>
      <Link href={`${base}/tasks`} className={cls("tasks")}>
        Tasks
      </Link>
      <Link href={`${base}/activity`} className={cls("activity")}>
        Activity
      </Link>
      <Link href={`${base}/tickets`} className={cls("tickets")}>
        Tickets
      </Link>
      <Link href={`${base}/github`} className={cls("github")}>
        GitHub
      </Link>
      <Link href={`${base}/settings`} className={cls("settings")}>
        Settings
      </Link>
    </nav>
  );
}
