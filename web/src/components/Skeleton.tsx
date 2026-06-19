export function Skeleton({ width, height = "1rem", style }: { width?: string; height?: string; style?: React.CSSProperties }) {
  return (
    <div
      aria-hidden
      style={{
        width: width ?? "100%",
        height,
        borderRadius: "var(--radius-sm)",
        background: "linear-gradient(90deg, var(--surface) 25%, var(--surface-elevated) 50%, var(--surface) 75%)",
        backgroundSize: "200% 100%",
        animation: "skeleton-pulse 1.4s ease infinite",
        ...style,
      }}
    />
  );
}
