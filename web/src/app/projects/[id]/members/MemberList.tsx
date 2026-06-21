"use client";

import { useCallback, useEffect, useState } from "react";

import { toast } from "@/components/Toast";

type MemberRow = {
  user_id: string;
  email: string;
  display_name: string | null;
  role: string;
};

export function MemberList({
  projectId,
  canManage,
}: {
  projectId: string;
  canManage: boolean;
}) {
  const [members, setMembers] = useState<MemberRow[]>([]);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    const r = await fetch(`/api/projects/${projectId}/members`);
    if (r.ok) {
      const data = (await r.json()) as { items: MemberRow[] };
      setMembers(data.items);
    }
  }, [projectId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  async function remove(userId: string) {
    if (!confirm("Remove this member from the project?")) return;
    setBusy(userId);
    const r = await fetch(`/api/projects/${projectId}/members/${userId}`, {
      method: "DELETE",
    });
    setBusy(null);
    if (r.ok) {
      setMembers((prev) => prev.filter((m) => m.user_id !== userId));
      toast("Member removed");
    } else {
      const text = await r.text();
      try {
        const j = JSON.parse(text) as Record<string, unknown>;
        const d = j.detail;
        toast(Array.isArray(d) ? d.map((e: Record<string, unknown>) => e.msg ?? e.type).join("; ") : (typeof d === "string" ? d : text), "error");
      } catch {
        toast(text || `Error ${r.status}`, "error");
      }
    }
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
                    onClick={() => remove(m.user_id)}
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
    </div>
  );
}
