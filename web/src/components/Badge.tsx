import type { ReactNode } from "react";

const variants = {
  neutral: { bg: "rgb(148 163 184 / 12%)", color: "var(--muted)", border: "rgb(148 163 184 / 28%)" },
  accent: { bg: "rgb(56 189 248 / 15%)", color: "var(--accent)", border: "rgb(56 189 248 / 35%)" },
  success: { bg: "rgb(74 222 128 / 12%)", color: "var(--success)", border: "rgb(74 222 128 / 35%)" },
  danger: { bg: "rgb(251 113 133 / 12%)", color: "var(--danger)", border: "rgb(251 113 133 / 35%)" },
  warning: { bg: "rgb(251 191 36 / 12%)", color: "var(--warning)", border: "rgb(251 191 36 / 35%)" },
} as const;

type BadgeVariant = keyof typeof variants;

export function Badge({
  children,
  variant = "neutral",
  className = "",
  style,
}: {
  children: ReactNode;
  variant?: BadgeVariant;
  className?: string;
  style?: React.CSSProperties;
}) {
  const v = variants[variant];
  return (
    <span
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        fontSize: "0.72rem",
        fontWeight: 600,
        textTransform: "uppercase",
        letterSpacing: "0.06em",
        padding: "0.2rem 0.45rem",
        borderRadius: "var(--radius-sm)",
        background: v.bg,
        color: v.color,
        border: `1px solid ${v.border}`,
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {children}
    </span>
  );
}

export const stageBadgeVariant = (stage: string): BadgeVariant => {
  switch (stage) {
    case "won":
      return "success";
    case "lost":
      return "danger";
    case "negotiating":
    case "proposal_sent":
      return "warning";
    case "target":
    case "connected":
      return "accent";
    default:
      return "neutral";
  }
};
