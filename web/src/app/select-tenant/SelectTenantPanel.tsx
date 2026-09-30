"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { TenantOption } from "./page";

export function SelectTenantPanel({
  options,
  current,
  next,
}: {
  options: TenantOption[];
  current: string | null;
  next?: string;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<string | null>(null);

  async function choose(slug: string) {
    setError(null);
    setPending(slug);
    try {
      const r = await fetch("/api/auth/tenant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenant_slug: slug }),
      });
      if (!r.ok) {
        const j = (await r.json().catch(() => ({}))) as { error?: string };
        setError(j.error || `Could not select organization (${r.status})`);
        setPending(null);
        return;
      }
      router.replace(next ?? "/projects");
      router.refresh();
    } catch {
      setError("Network error");
      setPending(null);
    }
  }

  return (
    <div className="stack" style={{ gap: "0.75rem" }}>
      {error ? (
        <p role="alert" className="err">
          <strong>{error}</strong>
        </p>
      ) : null}
      <ul className="stack" style={{ listStyle: "none", padding: 0, gap: "0.5rem" }}>
        {options.map((t) => (
          <li key={t.slug}>
            <button
              type="button"
              className={t.slug === current ? "btn btn-primary" : "btn"}
              disabled={pending !== null}
              onClick={() => choose(t.slug)}
            >
              {t.name}
              <span className="muted text-sm"> · {t.slug}</span>
              {t.slug === current ? " · current" : ""}
              {pending === t.slug ? " · selecting…" : ""}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
