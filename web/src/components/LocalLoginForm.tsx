"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

interface TenantChoice {
  tenant_slug: string;
  tenant_name: string;
}

export function LocalLoginForm({ tenantSlug }: { tenantSlug?: string | null }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [choices, setChoices] = useState<TenantChoice[] | null>(null);
  const [selectedTenant, setSelectedTenant] = useState<string>(tenantSlug || "");

  async function doLogin(ts?: string) {
    setError(null);
    setPending(true);
    try {
      const r = await fetch("/api/auth/local/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, tenant_slug: ts || selectedTenant || undefined }),
      });
      if (r.status === 300) {
        const j = (await r.json()) as { choices?: TenantChoice[] };
        if (j.choices && j.choices.length > 0) {
          setChoices(j.choices);
          setPending(false);
          return;
        }
      }
      if (!r.ok) {
        const j = (await r.json().catch(() => ({}))) as { error?: string };
        setError(j.error || `Sign-in failed (${r.status})`);
        setPending(false);
        return;
      }
      router.replace("/projects");
      router.refresh();
    } catch {
      setError("Network error");
      setPending(false);
    }
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    doLogin();
  }

  return (
    <form className="stack" onSubmit={onSubmit}>
      {error ? (
        <p role="alert">
          <strong>{error}</strong>
        </p>
      ) : null}
      {choices ? (
        <div className="stack" style={{ gap: "0.5rem" }}>
          <p className="muted">Select your organization:</p>
          {choices.map((c) => (
            <button
              key={c.tenant_slug}
              type="button"
              className="button"
              onClick={() => { setSelectedTenant(c.tenant_slug); setChoices(null); doLogin(c.tenant_slug); }}
            >
              {c.tenant_name}
            </button>
          ))}
        </div>
      ) : (
        <>
          <label className="stack" style={{ display: "block" }}>
        <span className="muted">Email</span>
        <input
          name="email"
          type="email"
          autoComplete="username"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ width: "100%", padding: "0.5rem", borderRadius: 6, border: "1px solid #cbd5e1" }}
        />
      </label>
      <label className="stack" style={{ display: "block" }}>
        <span className="muted">Password</span>
        <input
          name="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ width: "100%", padding: "0.5rem", borderRadius: 6, border: "1px solid #cbd5e1" }}
        />
      </label>
      <button className="btn btn-primary" type="submit" disabled={pending}>
        {pending ? "Signing in…" : "Sign in with email"}
      </button>
        </>
      )}
    </form>
  );
}
