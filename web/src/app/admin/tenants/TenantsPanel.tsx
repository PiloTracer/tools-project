"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { TenantRow } from "./page";

export function TenantsPanel({
  tenants,
  token,
  base,
}: {
  tenants: TenantRow[];
  token: string;
  base: string;
}) {
  const router = useRouter();
  const [items, setItems] = useState(tenants);
  const [showCreate, setShowCreate] = useState(false);
  const [slug, setSlug] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editActive, setEditActive] = useState(true);

  async function createTenant(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      const r = await fetch(`${base}/v1/admin/tenants`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ slug: slug.trim().toLowerCase(), name: name.trim() }),
      });
      if (!r.ok) {
        const j = (await r.json().catch(() => ({}))) as { detail?: string };
        setError(j.detail || `Failed (${r.status})`);
        return;
      }
      const created = (await r.json()) as TenantRow;
      setItems([...items, created]);
      setSlug("");
      setName("");
      setShowCreate(false);
      router.refresh();
    } catch {
      setError("Network error");
    } finally {
      setPending(false);
    }
  }

  async function updateTenant(id: string) {
    setError(null);
    setPending(true);
    try {
      const r = await fetch(`${base}/v1/admin/tenants/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name: editName.trim(), is_active: editActive }),
      });
      if (!r.ok) {
        const j = (await r.json().catch(() => ({}))) as { detail?: string };
        setError(j.detail || `Failed (${r.status})`);
        return;
      }
      const updated = (await r.json()) as TenantRow;
      setItems(items.map((t) => (t.id === id ? updated : t)));
      setEditingId(null);
      router.refresh();
    } catch {
      setError("Network error");
    } finally {
      setPending(false);
    }
  }

  function startEdit(t: TenantRow) {
    setEditingId(t.id);
    setEditName(t.name);
    setEditActive(t.is_active);
  }

  return (
    <div className="stack" style={{ gap: "1.5rem" }}>
      {error ? (
        <p role="alert" style={{ color: "var(--danger, #dc2626)" }}>
          {error}
        </p>
      ) : null}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <p className="muted">{items.length} tenant{items.length !== 1 ? "s" : ""}</p>
        {!showCreate && (
          <button className="btn btn-primary btn-sm" onClick={() => setShowCreate(true)}>
            + New Tenant
          </button>
        )}
      </div>

      {showCreate && (
        <form onSubmit={createTenant} className="stack card" style={{ gap: "0.75rem", padding: "1rem" }}>
          <h3 style={{ margin: 0 }}>Create Tenant</h3>
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span className="muted text-sm">Slug (URL-friendly, lowercase)</span>
            <input
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              required
              pattern="[a-z0-9-]+"
              placeholder="acme-corp"
              style={{ padding: "0.4rem 0.6rem", borderRadius: 6, border: "1px solid #cbd5e1" }}
            />
          </label>
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span className="muted text-sm">Display Name</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="Acme Corporation"
              style={{ padding: "0.4rem 0.6rem", borderRadius: 6, border: "1px solid #cbd5e1" }}
            />
          </label>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button className="btn btn-primary btn-sm" type="submit" disabled={pending}>
              {pending ? "Creating…" : "Create"}
            </button>
            <button
              className="btn btn-ghost btn-sm"
              type="button"
              onClick={() => { setShowCreate(false); setError(null); }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {items.length === 0 ? (
        <p className="muted">No tenants yet. The &quot;default&quot; tenant is created on first startup.</p>
      ) : (
        <div className="stack" style={{ gap: "0.5rem" }}>
          {items.map((t) => (
            <div
              key={t.id}
              className="card"
              style={{
                padding: "0.75rem 1rem",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              {editingId === t.id ? (
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flex: 1 }}>
                  <input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    style={{ padding: "0.3rem 0.5rem", borderRadius: 4, border: "1px solid #cbd5e1", flex: 1 }}
                  />
                  <label style={{ display: "flex", alignItems: "center", gap: "0.25rem", fontSize: "0.85rem" }}>
                    <input type="checkbox" checked={editActive} onChange={(e) => setEditActive(e.target.checked)} />
                    Active
                  </label>
                  <button className="btn btn-primary btn-sm" disabled={pending} onClick={() => updateTenant(t.id)}>
                    Save
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={() => setEditingId(null)}>
                    Cancel
                  </button>
                </div>
              ) : (
                <>
                  <div>
                    <strong>{t.name}</strong>
                    <span className="muted text-sm" style={{ marginLeft: "0.5rem", fontFamily: "monospace" }}>
                      {t.slug}
                    </span>
                    {!t.is_active && (
                      <span
                        style={{
                          marginLeft: "0.5rem",
                          fontSize: "0.75rem",
                          background: "var(--danger, #dc2626)",
                          color: "#fff",
                          padding: "0.1rem 0.4rem",
                          borderRadius: 4,
                        }}
                      >
                        Inactive
                      </span>
                    )}
                  </div>
                  <button className="btn btn-ghost btn-sm" onClick={() => startEdit(t)}>
                    Edit
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
