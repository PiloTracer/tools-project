import Link from "next/link";
import type { ReactNode } from "react";

import { CmdkPalette } from "@/components/CmdkPalette";
import { SignOutButton } from "@/components/SignOutButton";
import { fetchMe } from "@/shared/server/session";

export async function AppShell({ children }: { children: ReactNode }) {
  const me = await fetchMe();

  return (
    <div className="app-frame">
      <header className="app-header">
        <div className="app-header-inner">
          <Link href="/" className="brand">
            <span className="brand-mark" aria-hidden />
            <span className="brand-text">tools-project</span>
          </Link>
          <nav className="nav-links" aria-label="Primary">
            <Link href="/">Home</Link>
            {me ? (
              <>
                <Link href="/today">Today</Link>
                <Link href="/projects">Projects</Link>
                <Link href="/inbox">Inbox</Link>
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
            ) : (
              <Link href="/login" className="nav-cta">
                Sign in
              </Link>
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
      <div className="app-body">{children}</div>
      <CmdkPalette />
    </div>
  );
}
