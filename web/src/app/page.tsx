import Link from "next/link";

function apiBaseUrl(): string {
  const internal = process.env.API_INTERNAL_URL?.replace(/\/+$/, "");
  if (internal) return internal;
  const pub = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "");
  if (pub) return pub;
  return "http://api:8300";
}

async function apiStatus(): Promise<string> {
  const base = apiBaseUrl();
  try {
    const r = await fetch(`${base}/healthz`, { cache: "no-store" });
    if (!r.ok) return `API unhealthy (HTTP ${r.status})`;
    const j = (await r.json()) as { status?: string };
    return j.status === "ok" ? "API reachable" : "API unexpected response";
  } catch {
    return "API unreachable (is the stack up?)";
  }
}

async function authConfigFromApi(): Promise<{
  local_enabled: boolean;
  oauth_enabled: boolean;
}> {
  const base = apiBaseUrl();
  try {
    const r = await fetch(`${base}/v1/auth/config`, { cache: "no-store" });
    if (!r.ok) return { local_enabled: true, oauth_enabled: true };
    return (await r.json()) as {
      local_enabled: boolean;
      oauth_enabled: boolean;
    };
  } catch {
    return { local_enabled: true, oauth_enabled: true };
  }
}

export default async function HomePage() {
  const [backend, cfg] = await Promise.all([apiStatus(), authConfigFromApi()]);
  return (
    <main className="card stack">
      <h1>tools-project</h1>
      <p className="muted">Project hub — projects, tasks, tickets, GitHub context.</p>
      <p className="muted">{backend}</p>
      <p className="muted">
        Auth:{" "}
        {cfg.oauth_enabled ? "tools-dashboard OAuth supported. " : "OAuth off. "}
        {cfg.local_enabled ? "Local accounts supported." : "Local accounts off."}
      </p>
      <p className="stack" style={{ marginTop: "1rem" }}>
        <Link className="btn btn-primary" href="/login">
          Sign in
        </Link>
      </p>
      {cfg.local_enabled ? (
        <p>
          <Link href="/admin/users">Local user admin</Link>
          <span className="muted"> — list users (superuser only).</span>
        </p>
      ) : null}
      <p className="muted">
        Configure <code>AUTH_*</code>, <code>JWT_SECRET</code>, and optional{" "}
        <code>BOOTSTRAP_ADMIN_*</code> in <code>.env</code>.
      </p>
    </main>
  );
}
