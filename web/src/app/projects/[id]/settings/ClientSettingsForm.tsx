"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

import { Badge } from "@/components/Badge";
import { Dialog } from "@/components/Dialog";

type LinkedClientRow = {
  id: string;
  client_id: string;
  client_name: string;
  client_slug: string;
  created_at: string;
};

type AccessRow = {
  id: string;
  client_contact_id: string;
  contact_name: string | null;
  contact_email: string | null;
  client_name: string | null;
  role: string;
  can_view_tasks: boolean;
  can_view_tickets: boolean;
  can_create_tasks: boolean;
};

export function ClientSettingsForm({
  projectId,
  canEdit,
}: {
  projectId: string;
  canEdit: boolean;
}) {
  const router = useRouter();
  const [linkedClients, setLinkedClients] = useState<LinkedClientRow[]>([]);
  const [accessGrants, setAccessGrants] = useState<AccessRow[]>([]);
  const [showLinkClient, setShowLinkClient] = useState(false);
  const [clientId, setClientId] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  const fetchData = async () => {
    const [lc, ag] = await Promise.all([
      fetch(`/api/projects/${projectId}/clients`),
      fetch(`/api/projects/${projectId}/client-access`),
    ]);
    if (lc.ok) setLinkedClients((await lc.json()).items ?? []);
    if (ag.ok) setAccessGrants((await ag.json()).items ?? []);
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  if (!canEdit) {
    return (
      <div>
        <h2 style={{ marginTop: 0 }}>Clients</h2>
        <p className="muted text-sm">Only owners and maintainers can manage client links.</p>
        {linkedClients.length > 0 && (
          <ul style={{ marginTop: "0.5rem" }}>
            {linkedClients.map((c) => <li key={c.id}>{c.client_name}</li>)}
          </ul>
        )}
      </div>
    );
  }

  const handleLinkClient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clientId.trim()) return;
    setMsg(null);
    const r = await fetch(`/api/projects/${projectId}/clients`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: clientId.trim() }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Failed to link" }));
      setMsg(err.detail);
      return;
    }
    setClientId("");
    setShowLinkClient(false);
    fetchData();
    router.refresh();
  };

  const handleUnlink = async (clientId: string) => {
    await fetch(`/api/projects/${projectId}/clients?client_id=${clientId}`, { method: "DELETE" });
    fetchData();
    router.refresh();
  };

  const handleRevokeAccess = async (accessId: string) => {
    await fetch(`/api/projects/${projectId}/client-access/${accessId}`, { method: "DELETE" });
    fetchData();
  };

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Clients</h2>

      {linkedClients.length > 0 ? (
        <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "1rem" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
              <th style={{ padding: "0.5rem 0" }}>Client</th>
              <th>Slug</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {linkedClients.map((c) => (
              <tr key={c.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: "0.35rem 0", fontWeight: 600 }}>{c.client_name}</td>
                <td style={{ fontFamily: "ui-monospace, monospace", fontSize: "0.82rem", color: "var(--muted)" }}>
                  {c.client_slug}
                </td>
                <td style={{ textAlign: "right" }}>
                  <button className="btn btn-sm btn-ghost" style={{ color: "var(--danger)" }} onClick={() => handleUnlink(c.client_id)}>
                    Unlink
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="muted text-sm">No clients linked to this project yet.</p>
      )}

      <button className="btn btn-sm btn-secondary" onClick={() => { setClientId(""); setMsg(null); setShowLinkClient(true); }}>
        Link client
      </button>

      <Dialog
        open={showLinkClient}
        onClose={() => setShowLinkClient(false)}
        title="Link client to project"
        actions={
          <>
            <button type="button" className="btn btn-ghost" onClick={() => setShowLinkClient(false)}>Cancel</button>
            <button type="submit" form="link-client-form" className="btn btn-primary">Link</button>
          </>
        }
      >
        <form id="link-client-form" onSubmit={handleLinkClient} className="stack" style={{ gap: "0.65rem" }}>
          <label className="field">
            <span className="label">Client ID (UUID)</span>
            <input className="input" value={clientId} onChange={(e) => setClientId(e.target.value)} required placeholder="Enter client UUID" />
          </label>
          {msg ? <p className="err text-sm">{msg}</p> : null}
        </form>
      </Dialog>

      <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "1.25rem 0" }} />

      <h2 style={{ marginTop: 0 }}>Client Access</h2>

      {accessGrants.length > 0 ? (
        <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "1rem" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
              <th style={{ padding: "0.5rem 0" }}>Contact</th>
              <th>Client</th>
              <th>Role</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {accessGrants.map((a) => (
              <tr key={a.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: "0.35rem 0" }}>
                  <div style={{ fontWeight: 600 }}>{a.contact_name ?? "—"}</div>
                  <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>{a.contact_email}</div>
                </td>
                <td style={{ color: "var(--muted)", fontSize: "0.88rem" }}>{a.client_name ?? "—"}</td>
                <td><Badge variant="neutral">{a.role}</Badge></td>
                <td style={{ textAlign: "right" }}>
                  <button className="btn btn-sm btn-ghost" style={{ color: "var(--danger)" }} onClick={() => handleRevokeAccess(a.id)}>
                    Revoke
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="muted text-sm">No client access grants yet.</p>
      )}
    </div>
  );
}
