"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function LocalLoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      const r = await fetch("/api/auth/local/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!r.ok) {
        const j = (await r.json().catch(() => ({}))) as { error?: string };
        setError(j.error || `Sign-in failed (${r.status})`);
        setPending(false);
        return;
      }
      router.replace("/");
      router.refresh();
    } catch {
      setError("Network error");
      setPending(false);
    }
  }

  return (
    <form className="stack" onSubmit={onSubmit}>
      {error ? (
        <p role="alert">
          <strong>{error}</strong>
        </p>
      ) : null}
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
    </form>
  );
}
