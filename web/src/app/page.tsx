import Link from "next/link";

import { DashboardSystem } from "@/app/_components/DashboardSystem";
import { DashboardWorkspace } from "@/app/_components/DashboardWorkspace";
import { apiServerFetch, fetchMe } from "@/shared/server/session";

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

type ProjectRow = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
};

export default async function HomePage() {
  const [backend, cfg, me] = await Promise.all([
    apiStatus(),
    authConfigFromApi(),
    fetchMe(),
  ]);

  let projects: ProjectRow[] = [];
  if (me) {
    const pr = await apiServerFetch("/v1/projects");
    if (pr.ok) {
      const data = (await pr.json()) as { items?: ProjectRow[] };
      projects = data.items ?? [];
    }
  }

  const apiOk = backend.includes("reachable");
  const authParts: string[] = [];
  if (cfg.oauth_enabled) authParts.push("OAuth");
  if (cfg.local_enabled) authParts.push("Local accounts");
  const authLabel = authParts.join(" · ") || "—";

  const displayName = me?.display_name || me?.email.split("@")[0] || "";

  return (
    <div className="page-inner stack-lg">
      <header className="home-hero">
        <span className="pill">Project hub</span>
        <h1 style={{ marginTop: "0.65rem" }}>
          Welcome{me ? `, ${me.display_name || me.email.split("@")[0]}` : ""}
        </h1>
        <p className="muted home-hero-lead">
          Plan work by project, capture tasks and support tickets, and wire GitHub context — all
          behind your org auth.
        </p>
      </header>

      <div className="grid-dashboard">
        {me ? (
          <DashboardWorkspace projects={projects} displayName={displayName} />
        ) : (
          <div className="dashboard-tile dashboard-tile--workspace">
            <h2>Workspace</h2>
            <p className="muted text-sm">
              Sign in to create projects, see what you’re working on, and jump back in with one
              click.
            </p>
            <div className="dashboard-actions">
              <Link className="btn btn-primary" href="/login">
                Sign in
              </Link>
            </div>
          </div>
        )}

        <DashboardSystem
          apiOk={apiOk}
          authLabel={authLabel}
          showUserAdmin={cfg.local_enabled && !!me?.is_superuser}
        />
      </div>

      {!me ? (
        <p className="muted text-sm">
          Configure <code>AUTH_*</code>, <code>JWT_SECRET</code>, and optional{" "}
          <code>BOOTSTRAP_ADMIN_*</code> in <code>.env</code>.
        </p>
      ) : null}
    </div>
  );
}
