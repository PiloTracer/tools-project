import type { ReactNode } from "react";

export function Chip({
  children,
  onRemove,
  variant = "default",
  style,
}: {
  children: ReactNode;
  onRemove?: () => void;
  variant?: "default" | "accent";
  style?: React.CSSProperties;
}) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.35rem",
        padding: "0.2rem 0.5rem",
        fontSize: "0.8rem",
        fontWeight: 500,
        borderRadius: "var(--radius-sm)",
        background: variant === "accent" ? "rgb(56 189 248 / 12%)" : "var(--surface)",
        border: `1px solid ${variant === "accent" ? "rgb(56 189 248 / 35%)" : "var(--border)"}`,
        color: variant === "accent" ? "var(--accent)" : "var(--text)",
        ...style,
      }}
    >
      {children}
      {onRemove ? (
        <button
          type="button"
          onClick={onRemove}
          aria-label="Remove"
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "inherit",
            padding: 0,
            fontSize: "0.85rem",
            lineHeight: 1,
            opacity: 0.7,
          }}
        >
          ×
        </button>
      ) : null}
    </span>
  );
}
