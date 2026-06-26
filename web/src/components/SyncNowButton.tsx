"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "@/components/Toast";

export function SyncNowButton({
  projectId,
  linkId,
}: {
  projectId: string;
  linkId: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function handleSync() {
    setBusy(true);
    try {
      const r = await fetch(
        `/api/projects/${projectId}/github/links/${linkId}/sync`,
        { method: "POST" },
      );
      const text = await r.text();
      if (!r.ok) {
        try {
          const j = JSON.parse(text) as { detail?: string };
          toast(j.detail ?? text, "error");
        } catch {
          toast(text || `Error ${r.status}`, "error");
        }
        return;
      }
      toast("Sync complete");
      router.refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Sync failed", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <button type="button" className="btn btn-sm btn-secondary" onClick={handleSync} disabled={busy} style={{ fontSize: "0.72rem" }}>
      {busy ? "Syncing…" : "Sync now"}
    </button>
  );
}
