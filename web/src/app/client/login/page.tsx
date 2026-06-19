"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export default function ClientLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const r = await fetch("/api/auth/local/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        setError(d.detail || "Login failed");
        return;
      }
      router.push("/client/dashboard");
    } catch {
      setError("Network error");
    }
  }

  return (
    <div className="page-inner">
      <main className="card stack" style={{ maxWidth: "24rem", margin: "4rem auto" }}>
        <h1>Client Portal</h1>
        <p className="muted text-sm">Sign in to access your projects.</p>
        {error ? <p role="alert" className="err">{error}</p> : null}
        <form onSubmit={handleSubmit} className="stack">
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          <button type="submit" className="btn btn-primary">Sign in</button>
        </form>
      </main>
    </div>
  );
}
