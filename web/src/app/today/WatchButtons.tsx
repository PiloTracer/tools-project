"use client";

import { useRouter } from "next/navigation";

export function WatchButtons({
  subjectType,
  subjectId,
}: {
  subjectType: "task" | "ticket" | "project";
  subjectId: string;
}) {
  const router = useRouter();

  async function watch() {
    const r = await fetch("/api/me/watch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subject_type: subjectType, subject_id: subjectId }),
    });
    if (r.ok) router.refresh();
  }

  async function unwatch() {
    const r = await fetch("/api/me/watch", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subject_type: subjectType, subject_id: subjectId }),
    });
    if (r.ok) router.refresh();
  }

  return (
    <span style={{ display: "flex", gap: "0.25rem", flexShrink: 0 }}>
      <button
        type="button"
        className="btn btn-ghost text-sm"
        style={{ padding: "0.1rem 0.35rem", fontSize: "0.7rem" }}
        onClick={watch}
        title="Watch"
      >
        👁
      </button>
      <button
        type="button"
        className="btn btn-ghost text-sm"
        style={{ padding: "0.1rem 0.35rem", fontSize: "0.7rem" }}
        onClick={unwatch}
        title="Unwatch"
      >
        ✕
      </button>
    </span>
  );
}
