"use client";

import Link from "next/link";
import { useEffect } from "react";

/**
 * Route-level error boundary.
 *
 * Without this, an uncaught render error unmounts the React tree and the page
 * dies with the browser's generic "This page couldn't load" — no message, no
 * way back. This renders a readable failure with a retry instead, and logs the
 * error so the failing render stays diagnosable.
 */
export default function RouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Page render failed:", error);
  }, [error]);

  return (
    <div className="page-inner">
      <main className="stack" style={{ maxWidth: "40rem", margin: "3rem auto" }}>
        <h1>This page failed to render</h1>
        <p className="muted text-sm">
          Your last action did not complete. Try again — if it keeps failing, report the
          reference below.
        </p>
        {error.digest ? (
          <p className="muted text-sm">
            Reference: <code>{error.digest}</code>
          </p>
        ) : null}
        <div className="row" style={{ gap: "0.5rem", display: "flex" }}>
          <button type="button" className="btn btn-primary" onClick={() => reset()}>
            Try again
          </button>
          <Link className="btn btn-ghost" href="/">
            ← Home
          </Link>
        </div>
      </main>
    </div>
  );
}
