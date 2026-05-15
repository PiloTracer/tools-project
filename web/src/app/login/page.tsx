import Link from "next/link";

import { LocalLoginForm } from "@/components/LocalLoginForm";

async function authConfigFromApi(): Promise<{
  local_enabled: boolean;
  oauth_enabled: boolean;
}> {
  const base =
    process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300";
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

const HINTS: Record<string, string> = {
  no_state:
    "The IdP did not return `state`. Start again from **Continue with SSO**.",
  oauth_state_invalid:
    "PKCE state was missing or expired. Try signing in once more from the home page.",
  no_code: "Authorization code missing — try **Continue with SSO** again.",
  oauth_config:
    "Server OAuth configuration error — check `OAUTH_CLIENT_SECRET` and related env vars.",
  token_exchange:
    "Token exchange failed — verify client id/secret and redirect URI in tools-dashboard.",
  userinfo: "Could not load your user profile from the IdP after login.",
  oauth_disabled:
    "tools-dashboard OAuth is turned off for this deployment (`AUTH_OAUTH_ENABLED`). Use email/password or enable OAuth in `.env`.",
  admin_auth: "Sign in with a local superuser to access admin.",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const err = typeof sp.error === "string" ? sp.error : undefined;
  const oauthErr = typeof sp.oauth_error === "string" ? sp.oauth_error : undefined;
  const hint = err ? HINTS[err] : undefined;
  const cfg = await authConfigFromApi();

  return (
    <div className="page-inner">
    <main className="card stack">
      <h1>Sign in</h1>
      {err ? (
        <p role="alert">
          <strong>{err}</strong>
          {hint ? ` — ${hint}` : null}
        </p>
      ) : null}
      {oauthErr ? (
        <p className="muted">
          Provider error: <code>{oauthErr}</code>
        </p>
      ) : null}

      {cfg.oauth_enabled ? (
        <p>
          <Link className="btn btn-primary" href="/sign-in">
            Continue with SSO (tools-dashboard)
          </Link>
        </p>
      ) : (
        <p className="muted">SSO is disabled for this deployment.</p>
      )}

      {cfg.local_enabled ? (
        <>
          <p className="muted">Or sign in with a local account:</p>
          <LocalLoginForm />
        </>
      ) : (
        <p className="muted">Local accounts are disabled for this deployment.</p>
      )}

      <p className="muted">
        <Link href="/">← Back to home</Link>
      </p>
    </main>
    </div>
  );
}
