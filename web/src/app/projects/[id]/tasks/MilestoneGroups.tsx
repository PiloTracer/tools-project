"use client";

import Link from "next/link";

import { CopyRefButton } from "@/components/CopyRefButton";
import { ProgressBar } from "@/components/PlanTaskBody";
import { taskLabel } from "@/shared/plan-text";

export type MilestoneRow = {
  id: string;
  key: string | null;
  name: string;
  summary: string | null;
  status: string;
  plan_state: string;
  sort_order: number;
  plan_ref: string | null;
  task_total: number;
  task_done: number;
};

type TaskLike = {
  id: string;
  ref: string | null;
  title: string;
  status: string;
  priority: string;
  milestone_id?: string | null;
  plan_ref?: string | null;
  plan_state?: string;
};

function statusPill(status: string): string {
  if (status === "done" || status === "active") return "pill pill-ok";
  if (status === "blocked") return "pill pill-err";
  if (status === "cancelled") return "pill pill-muted";
  return "pill";
}

/**
 * Tasks grouped by milestone — the "12 milestones, 158 tasks" view.
 * The active milestone is expanded by default; the rest are one click away.
 */
export function MilestoneGroups({
  projectId,
  milestones,
  tasks,
  onSetMilestoneFilter,
}: {
  projectId: string;
  milestones: MilestoneRow[];
  tasks: TaskLike[];
  onSetMilestoneFilter?: (milestoneId: string) => void;
}) {
  const byMilestone = new Map<string, TaskLike[]>();
  const unassigned: TaskLike[] = [];
  for (const t of tasks) {
    const key = t.milestone_id ?? "";
    if (!key) {
      unassigned.push(t);
      continue;
    }
    const list = byMilestone.get(key);
    if (list) list.push(t);
    else byMilestone.set(key, [t]);
  }

  const ordered = [...milestones].sort((a, b) => a.sort_order - b.sort_order);
  const activeId = ordered.find((m) => m.status === "active")?.id ?? ordered[0]?.id ?? "";

  return (
    <div className="stack" style={{ gap: "0.6rem" }}>
      {ordered.map((m) => {
        const rows = byMilestone.get(m.id) ?? [];
        const pct = m.task_total > 0 ? Math.round((m.task_done / m.task_total) * 100) : 0;
        const isActive = m.status === "active";
        return (
          <details
            key={m.id}
            open={m.id === activeId}
            className="card"
            style={{ padding: "0.6rem 0.75rem" }}
          >
            <summary style={{ cursor: "pointer", listStyle: "none" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                {m.key ? (
                  <span
                    className="pill"
                    style={{ fontSize: "0.7rem", fontFamily: "var(--font-mono, monospace)" }}
                  >
                    {m.key}
                  </span>
                ) : null}
                <strong>{m.name}</strong>
                <span className={statusPill(m.status)} style={{ fontSize: "0.65rem" }}>
                  {m.status}
                </span>
                {isActive ? (
                  <span className="pill pill-ok" style={{ fontSize: "0.65rem" }}>
                    current
                  </span>
                ) : null}
                {m.plan_state === "obsolete" ? (
                  <span className="pill pill-muted" style={{ fontSize: "0.65rem" }}>
                    obsolete
                  </span>
                ) : null}
                <span className="text-sm muted" style={{ marginLeft: "auto" }}>
                  {m.task_done}/{m.task_total} done · {rows.length} shown
                </span>
                {onSetMilestoneFilter ? (
                  <button
                    type="button"
                    className="btn btn-ghost text-sm"
                    onClick={(e) => {
                      e.preventDefault();
                      onSetMilestoneFilter(m.id);
                    }}
                  >
                    Focus
                  </button>
                ) : (
                  <Link
                    className="btn btn-ghost text-sm"
                    href={`/projects/${projectId}/tasks?milestone=${m.id}`}
                  >
                    Open
                  </Link>
                )}
              </div>
              <div style={{ marginTop: "0.4rem", maxWidth: "22rem" }}>
                <ProgressBar percent={pct} />
              </div>
              {m.summary ? (
                <p className="muted text-sm" style={{ margin: "0.35rem 0 0" }}>
                  {m.summary}
                </p>
              ) : null}
            </summary>
            <ul
              className="stack"
              style={{ listStyle: "none", paddingLeft: 0, gap: "0.3rem", marginTop: "0.6rem" }}
            >
              {rows.length === 0 ? (
                <li className="muted text-sm">No tasks shown for this milestone (check the filters).</li>
              ) : (
                rows.map((t) => (
                  <li
                    key={t.id}
                    style={{ display: "flex", gap: "0.45rem", alignItems: "baseline", flexWrap: "wrap" }}
                  >
                    {t.ref ? (
                      <span
                        className="muted text-sm"
                        style={{ fontFamily: "var(--font-mono, monospace)" }}
                      >
                        {t.ref}
                      </span>
                    ) : null}
                    <Link
                      href={`/projects/${projectId}/tasks/${t.id}`}
                      style={{ flex: 1, minWidth: "12rem" }}
                      title={t.title}
                    >
                      {taskLabel(t.title)}
                    </Link>
                    <span className={statusPill(t.status)} style={{ fontSize: "0.6rem" }}>
                      {t.status}
                    </span>
                    {t.plan_state === "obsolete" ? (
                      <span className="pill pill-muted" style={{ fontSize: "0.6rem" }}>
                        obsolete
                      </span>
                    ) : null}
                  </li>
                ))
              )}
            </ul>
          </details>
        );
      })}

      {unassigned.length > 0 ? (
        <details className="card" style={{ padding: "0.6rem 0.75rem" }}>
          <summary style={{ cursor: "pointer" }}>
            <strong>No milestone</strong>{" "}
            <span className="text-sm muted">· {unassigned.length} task(s)</span>
          </summary>
          <ul
            className="stack"
            style={{ listStyle: "none", paddingLeft: 0, gap: "0.3rem", marginTop: "0.6rem" }}
          >
            {unassigned.map((t) => (
              <li
                key={t.id}
                style={{ display: "flex", gap: "0.45rem", alignItems: "baseline", flexWrap: "wrap" }}
              >
                {t.ref ? (
                  <span
                    className="muted text-sm"
                    style={{ fontFamily: "var(--font-mono, monospace)" }}
                  >
                    {t.ref}
                    <CopyRefButton code={t.ref} />
                  </span>
                ) : null}
                <Link
                  href={`/projects/${projectId}/tasks/${t.id}`}
                  style={{ flex: 1, minWidth: "12rem" }}
                  title={t.title}
                >
                  {taskLabel(t.title)}
                </Link>
                <span className={statusPill(t.status)} style={{ fontSize: "0.6rem" }}>
                  {t.status}
                </span>
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </div>
  );
}
