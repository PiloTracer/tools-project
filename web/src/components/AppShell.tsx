import Link from "next/link";
import type { ReactNode } from "react";

import { ClientRedirect } from "@/components/ClientRedirect";
import { CmdkPalette } from "@/components/CmdkPalette";
import { ToastContainer } from "@/components/Toast";
import { SignOutButton } from "@/components/SignOutButton";
import { SkipLink } from "@/components/SkipLink";
import { fetchMe } from "@/shared/server/session";

export async function AppShell({ children }: { children: ReactNode }) {
  const me = await fetchMe();
  const isClientOnly = !!(me && me.client_contact_id && !me.is_superuser);

  return (
    <div className="app-frame">
      <ClientRedirect me={me} />
      <SkipLink />
      <header className="app-header">
        <div className="app-header-inner">
          <Link href={isClientOnly ? "/client/dashboard" : "/"} className="brand">
            <span className="brand-mark" aria-hidden />
            <span className="brand-text">tools-project</span>
          </Link>
          <nav className="nav-links" aria-label="Primary">
            {!me ? (
              <>
                <Link href="/">Home</Link>
                <Link href="/client/login">Client Portal</Link>
                <Link href="/login" className="nav-cta">Sign in</Link>
              </>
            ) : isClientOnly ? (
              <>
                <Link href="/client/dashboard">Client Portal</Link>
              </>
            ) : (
              <>
                <Link href="/">Home</Link>
                <Link href="/today">Today</Link>
                <Link href="/projects">Projects</Link>
                <Link href="/inbox">Inbox</Link>
                <Link href="/prospects">Prospects</Link>
                <Link href="/clients">Clients</Link>
                {me.client_contact_id ? (
                  <Link href="/client/dashboard">Client Portal</Link>
                ) : null}
                <Link href="/reports">Reports</Link>
                <Link href="/settings/api-keys">API Keys</Link>
                <Link href="/about">About</Link>
                {me.is_superuser ? (
                  <Link href="/admin/users">Admin</Link>
                ) : null}
                <span
                  className="muted text-sm"
                  style={{
                    fontFamily: "var(--font-mono, monospace)",
                    padding: "0.15rem 0.5rem",
                    background: "var(--bg-elevated)",
                    borderRadius: 4,
                    cursor: "default",
                  }}
                  title="Press ⌘K or Ctrl+K to open command palette"
                >
                  ⌘K
                </span>
              </>
            )}
          </nav>
          {me ? (
            <div className="user-chip" title={me.email}>
              <span className="user-avatar" aria-hidden>
                {(me.display_name || me.email).slice(0, 1).toUpperCase()}
              </span>
              <div className="user-meta">
                <span className="user-name">
                  {me.display_name || me.email.split("@")[0]}
                </span>
                <span className="user-sub">
                  {me.auth === "oauth" ? "SSO" : "Local"} · {me.email}
                </span>
              </div>
              <SignOutButton />
            </div>
          ) : (
            <span className="muted text-sm">Not signed in</span>
          )}
        </div>
      </header>
      <div id="main-content" className="app-body">{children}</div>
      <CmdkPalette />
      <ToastContainer />
    </div>
  );
}
