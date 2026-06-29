"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiRequest } from "@/shared/client/api";
import { toast } from "@/components/Toast";

type ReadinessCheck = {
  id: string;
  label: string;
  met: boolean;
  action: string;
  api: string | null;
};

type ReadinessResponse = {
  ready: boolean;
  score: string;
  checks: ReadinessCheck[];
};

export function CommitReadinessCard({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [data, setData] = useState<ReadinessResponse | null>(null);
  const [testingId, setTestingId] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/projects/${projectId}/github/readiness`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setData(d as ReadinessResponse))
      .catch(() => {});
  }, [projectId]);

  async function handleFix(check: ReadinessCheck) {
    if (check.id === "github_link") {
      router.refresh();
      return;
    }
    if (check.id === "project_key" || check.id === "registry_enabled" || check.id === "auto_prefix") {
      toast("Update the settings above and save.", "success");
      return;
    }
    if (check.id === "commits_synced" && check.api) {
      setTestingId("commits_synced");
      const r = await apiRequest(check.api, { method: "POST" });
      setTestingId(null);
      if (r.ok) {
        toast("Sync triggered! Refresh to see updated status.", "success");
        const fresh = await fetch(`/api/projects/${projectId}/github/readiness`);
        if (fresh.ok) setData(await fresh.json() as ReadinessResponse);
      } else {
        toast(r.error, "error");
      }
    }
  }

  if (!data) {
    return (
      <div className="card wide stack">
        <h2 style={{ marginTop: 0 }}>Commit Association Readiness</h2>
        <p className="muted text-sm">Checking readiness…</p>
      </div>
    );
  }

  return (
    <div className="card wide stack">
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <h2 style={{ margin: 0 }}>Commit Association Readiness</h2>
        <span
          className="text-sm"
          style={{
            padding: "0.15rem 0.5rem",
            borderRadius: "1rem",
            background: data.ready ? "var(--success, #282)" : "var(--warning, #b90)",
            color: "#fff",
            fontWeight: 600,
          }}
        >
          {data.score}
        </span>
      </div>
      <p className="text-sm muted" style={{ margin: 0 }}>
        {data.ready
          ? "All checks pass — commits will be auto-linked to tasks and tickets."
          : "Complete the steps below to enable commit-to-task/ticket association."}
      </p>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {data.checks.map((c) => (
          <li
            key={c.id}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "0.5rem",
              padding: "0.5rem 0",
              borderBottom: "1px solid var(--border)",
            }}
          >
            <span
              style={{
                fontSize: "1.1rem",
                lineHeight: 1.4,
                color: c.met ? "var(--success, #282)" : "var(--danger, #c33)",
              }}
            >
              {c.met ? "✓" : "✗"}
            </span>
            <div style={{ flex: 1 }}>
              <strong className="text-sm">{c.label}</strong>
              {!c.met && (
                <>
                  <p className="text-sm muted" style={{ margin: "0.15rem 0" }}>
                    {c.action}
                  </p>
                  <button
                    className="btn btn-ghost text-sm"
                    style={{ marginTop: "0.25rem" }}
                    onClick={() => handleFix(c)}
                    disabled={testingId === c.id}
                  >
                    {testingId === c.id ? "Working…" : "Fix"}
                  </button>
                </>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
