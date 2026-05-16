"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function InviteMemberForm({
  projectId,
  canInvite,
}: {
  projectId: string;
  canInvite: boolean;
}) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("contributor");
  const [msg, setMsg] = useState<string | null>(null);

  if (!canInvite) {
    return (
      <p className="muted text-sm">
        Only owners and maintainers can invite members.
      </p>
    );
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    const r = await fetch(`/api/projects/${projectId}/members`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim(), role }),
    });
    const text = await r.text();
    if (!r.ok) {
      try {
        const j = JSON.parse(text) as { detail?: string };
        setMsg(j.detail ?? text);
      } catch {
        setMsg(text || `Error ${r.status}`);
      }
      return;
    }
    setEmail("");
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="stack" style={{ gap: "0.5rem", maxWidth: "28rem" }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "flex-end" }}>
        <label className="stack" style={{ flex: "1 1 160px", gap: "0.25rem" }}>
          <span className="text-sm muted">Email</span>
          <input
            className="input"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="colleague@example.com"
          />
        </label>
        <label className="stack" style={{ gap: "0.25rem" }}>
          <span className="text-sm muted">Role</span>
          <select className="input" value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="viewer">viewer</option>
            <option value="contributor">contributor</option>
            <option value="maintainer">maintainer</option>
            <option value="owner">owner</option>
          </select>
        </label>
        <button type="submit" className="btn btn-primary">
          Add member
        </button>
      </div>
      {msg ? <p className="err text-sm">{msg}</p> : null}
    </form>
  );
}
