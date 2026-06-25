"use client";

import { useState } from "react";

export function CopyRefButton({ ref: refCode }: { ref: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(refCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard not available
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      title={copied ? "Copied!" : `Copy ${refCode}`}
      aria-label={`Copy reference ${refCode}`}
      style={{
        background: "none",
        border: "none",
        cursor: "pointer",
        padding: "0.15rem 0.3rem",
        marginLeft: "0.3rem",
        fontSize: "0.75rem",
        color: "var(--muted)",
        borderRadius: "0.25rem",
        display: "inline-flex",
        alignItems: "center",
        verticalAlign: "middle",
        transition: "color 0.15s",
      }}
      onMouseEnter={(e) => { (e.target as HTMLElement).style.color = "var(--text)"; }}
      onMouseLeave={(e) => { (e.target as HTMLElement).style.color = "var(--muted)"; }}
    >
      {copied ? "✓" : "⧉"}
    </button>
  );
}
