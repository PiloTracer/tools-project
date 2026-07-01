"use client";

import { useCallback, useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { Dialog } from "@/components/Dialog";
import { toast } from "@/components/Toast";
import { apiRequest } from "@/shared/client/api";

type MemberRow = {
  user_id: string;
  email: string;
  display_name: string | null;
  role: string;
};

export function MemberList(props: { projectId: string; canManage: boolean }) {
  return (
    <Suspense fallback={<div className="card wide"><p className="muted">Loading members…</p></div>}>
      <MemberListInner {...props} />
    </Suspense>
  );
}

function MemberListInner({
  projectId,
  canManage,
}: {
  projectId: string;
  canManage: boolean;
}) {
  const searchParams = useSearchParams();
  const refreshKey = searchParams.get("r") ?? "";
  const [members, setMembers] = useState<MemberRow[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [removeTarget, setRemoveTarget] = useState<MemberRow | null>(null);

  const load = useCallback(async () => {
    const r = await apiRequest<{ items: MemberRow[] }>(`/api/projects/${projectId}/members`);
    if (r.ok) setMembers(r.data.items);
  }, [projectId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load, refreshKey]);

  async function remove(userId: string) {
    setBusy(userId);
    const r = await apiRequest(`/api/projects/${projectId}/members/${userId}`, {
      method: "DELETE",
    });
    setBusy(null);
    if (!r.ok) { toast(r.error, "error"); return; }
    setMembers((prev) => prev.filter((m) => m.user_id !== userId));
    setRemoveTarget(null);
    toast("Member removed");
  }

  if (members.length === 0) {
    return (
      <div className="card wide">
        <p className="muted">No members yet.</p>
      </div>
    );
  }

  return (
    <div className="card wide">
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
            <th style={{ padding: "0.5rem 0" }}>Email</th>
            <th>Name</th>
            <th>Role</th>
            {canManage && <th style={{ width: 0 }} />}
          </tr>
        </thead>
        <tbody>
          {members.map((m) => (
            <tr key={m.user_id} style={{ borderBottom: "1px solid var(--border)" }}>
              <td style={{ padding: "0.35rem 0" }}>{m.email}</td>
              <td>{m.display_name ?? "—"}</td>
              <td>
                <span className="pill">{m.role}</span>
              </td>
              {canManage && (
                <td style={{ paddingLeft: "0.75rem" }}>
                  <button
                    type="button"
                    className="btn btn-ghost text-sm"
                    disabled={busy === m.user_id}
                    onClick={() => setRemoveTarget(m)}
                    style={{ color: "var(--err)" }}
                  >
                    {busy === m.user_id ? "…" : "Remove"}
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      <Dialog
        open={removeTarget !== null}
        onClose={() => setRemoveTarget(null)}
        title="Remove member"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setRemoveTarget(null)}>Cancel</button>
            <button
              type="button"
              className="btn btn-primary"
              style={{ background: "var(--danger)", color: "var(--text)", boxShadow: "none" }}
              onClick={() => removeTarget && remove(removeTarget.user_id)}
            >
              Remove
            </button>
          </>
        }
      >
        <p className="text-sm">
          Remove <strong>{removeTarget?.email}</strong> from the project? This action cannot be undone.
        </p>
      </Dialog>
    </div>
  );
}
