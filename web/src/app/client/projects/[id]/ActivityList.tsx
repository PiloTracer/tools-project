"use client";

import { AttachmentImages, attachmentIds } from "@/components/AttachmentImages";
import { CommitCard, extractCommitMeta } from "@/components/CommitCard";
import { MarkdownBody } from "@/components/MarkdownBody";

type ActivityRow = {
  id: string;
  kind: string;
  body: string;
  is_internal: boolean;
  created_at: string;
  actor_email: string | null;
  meta_json: Record<string, unknown> | null;
};

export function ActivityList({ activities, projectId }: { activities: ActivityRow[]; projectId: string }) {
  return (
    <ul className="stack-sm" style={{ listStyle: "none", padding: 0 }}>
      {activities.map((activity) => (
        <li key={activity.id} className="card">
          <p className="muted text-sm" suppressHydrationWarning>
            {activity.kind === "github_commit" ? (
              <span className="pill" style={{ fontSize: "0.65rem", background: "var(--accent, #0366d6)", color: "var(--on-accent, #fff)" }}>commit</span>
            ) : (
              <span>{activity.kind}</span>
            )}
            <span suppressHydrationWarning> · {new Date(activity.created_at).toLocaleString()}</span>
            {activity.actor_email ? <span> · {activity.actor_email}</span> : null}
          </p>
          {activity.kind === "github_commit" ? (
            <CommitCard meta={extractCommitMeta(activity.meta_json)!} projectId={projectId} readonly />
          ) : (
            <>
              {activity.body !== "(image)" ? (
                <div style={{ margin: "0.35rem 0 0" }}>
                  <MarkdownBody text={activity.body} />
                </div>
              ) : null}
              {attachmentIds(activity.meta_json).length > 0 ? (
                <div style={{ marginTop: "0.35rem" }}>
                  <AttachmentImages ids={attachmentIds(activity.meta_json)} />
                </div>
              ) : null}
            </>
          )}
        </li>
      ))}
    </ul>
  );
}