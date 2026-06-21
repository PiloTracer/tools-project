"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect, useRef } from "react";

import { toast } from "@/components/Toast";

type UserHit = {
  id: string;
  email: string;
  display_name: string | null;
};

export function InviteMemberForm({
  projectId,
  canInvite,
}: {
  projectId: string;
  canInvite: boolean;
}) {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<UserHit[]>([]);
  const [searchPending, setSearchPending] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserHit | null>(null);
  const [role, setRole] = useState("contributor");
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    if (!searchQuery.trim() || selectedUser) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSearchResults([]);
      return;
    }
    searchTimer.current = setTimeout(async () => {
      setSearchPending(true);
      try {
        const r = await fetch(
          `/api/projects/${projectId}/members/search-users?q=${encodeURIComponent(searchQuery)}`,
        );
        if (r.ok) setSearchResults((await r.json()) ?? []);
        else setSearchResults([]);
      } catch {
        setSearchResults([]);
      } finally {
        setSearchPending(false);
      }
    }, 200);
    return () => {
      if (searchTimer.current) clearTimeout(searchTimer.current);
    };
  }, [searchQuery, projectId, selectedUser]);

  if (!canInvite) {
    return (
      <p className="muted text-sm">
        Only owners and maintainers can invite members.
      </p>
    );
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedUser) return;
    const r = await fetch(`/api/projects/${projectId}/members`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: selectedUser.email, role }),
    });
    const text = await r.text();
    if (!r.ok) {
      try {
        const j = JSON.parse(text) as Record<string, unknown>;
        const d = j.detail;
        toast(Array.isArray(d) ? d.map((e: Record<string, unknown>) => e.msg ?? e.type).join("; ") : (typeof d === "string" ? d : text), "error");
      } catch {
        toast(text || `Error ${r.status}`, "error");
      }
      return;
    }
    toast("Member added");
    setSelectedUser(null);
    setSearchQuery("");
    router.replace(`/projects/${projectId}/members?r=${Date.now()}`, { scroll: false });
  }

  return (
    <form onSubmit={onSubmit} className="stack" style={{ gap: "0.5rem", maxWidth: "32rem" }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "flex-end" }}>
        <label className="stack" style={{ flex: "1 1 200px", gap: "0.25rem", position: "relative" }}>
          <span className="text-sm muted">Search by email or name</span>
          <input
            className="input"
            value={selectedUser ? `${selectedUser.email}${selectedUser.display_name ? ` (${selectedUser.display_name})` : ""}` : searchQuery}
            onChange={(e) => {
              setSelectedUser(null);
              setSearchQuery(e.target.value);
            }}
            placeholder="Type to search…"
            autoComplete="off"
          />

          {selectedUser ? (
            <div style={{ padding: "0.3rem 0", color: "var(--muted)", fontSize: "0.82rem" }}>
              Selected: <strong>{selectedUser.email}</strong>
              {selectedUser.display_name ? ` (${selectedUser.display_name})` : ""}
            </div>
          ) : searchPending ? (
            <div style={{ padding: "0.3rem 0", color: "var(--muted)", fontSize: "0.82rem" }}>Searching…</div>
          ) : searchQuery && searchResults.length === 0 ? (
            <div style={{ padding: "0.3rem 0", color: "var(--muted)", fontSize: "0.82rem" }}>No matching users.</div>
          ) : searchResults.length > 0 ? (
            <div
              style={{
                position: "absolute",
                top: "100%",
                left: 0,
                right: 0,
                zIndex: 50,
                maxHeight: "14rem",
                overflowY: "auto",
                border: "1px solid var(--border)",
                borderRadius: 6,
                background: "var(--bg-elevated)",
                marginTop: "0.25rem",
              }}
            >
              {searchResults.map((u) => (
                <button
                  key={u.id}
                  type="button"
                  className="btn-ghost"
                  style={{
                    display: "block",
                    width: "100%",
                    textAlign: "left",
                    padding: "0.5rem",
                    borderRadius: 0,
                    border: "none",
                    borderBottom: "1px solid var(--border)",
                    cursor: "pointer",
                    background: "transparent",
                    fontFamily: "inherit",
                    fontSize: "0.9rem",
                    color: "var(--text)",
                  }}
                  onClick={() => {
                    setSelectedUser(u);
                    setSearchResults([]);
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{u.email}</div>
                  {u.display_name ? (
                    <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>{u.display_name}</div>
                  ) : null}
                </button>
              ))}
            </div>
          ) : null}
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

        <button type="submit" className="btn btn-primary" disabled={!selectedUser}>
          Add member
        </button>
      </div>
    </form>
  );
}
