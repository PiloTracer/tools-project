"use client";

export function SkipLink() {
  return (
    <a
      href="#main-content"
      style={{
        position: "absolute",
        left: "-9999px",
        zIndex: 9999,
        background: "var(--surface-overlay)",
        color: "var(--text)",
        padding: "0.5rem 1rem",
        borderRadius: "var(--radius-sm)",
        textDecoration: "none",
        fontWeight: 600,
      }}
      onFocus={(e) => (e.currentTarget.style.left = "0.5rem")}
      onBlur={(e) => (e.currentTarget.style.left = "-9999px")}
    >
      Skip to content
    </a>
  );
}
