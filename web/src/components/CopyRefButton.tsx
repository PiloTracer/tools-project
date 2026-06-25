"use client";

import { useState } from "react";

export function CopyRefButton({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard not available
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      title={copied ? "Copied!" : `Copy ${code}`}
      aria-label={`Copy reference ${code}`}
      style={{
        background: "none",
        border: "1px solid var(--border)",
        cursor: "pointer",
        padding: "0.1rem 0.4rem",
        marginLeft: "0.35rem",
        fontSize: "0.7rem",
        color: "var(--accent)",
        borderRadius: "0.25rem",
        display: "inline-flex",
        alignItems: "center",
        gap: "0.2rem",
        verticalAlign: "middle",
        fontFamily: "inherit",
        lineHeight: 1.4,
      }}
    >
      {copied ? "✓" : "📋"} Copy
    </button>
  );
}
