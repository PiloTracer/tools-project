export function StatCard({
  label,
  value,
  secondary,
}: {
  label: string;
  value: string | number;
  secondary?: string;
}) {
  return (
    <div
      style={{
        background: "var(--surface-elevated)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding: "1.25rem 1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.15rem",
      }}
    >
      <span className="text-sm muted">{label}</span>
      <span style={{ fontSize: "1.75rem", fontWeight: 700, lineHeight: 1.2 }}>
        {value}
      </span>
      {secondary ? <span className="text-xs muted">{secondary}</span> : null}
    </div>
  );
}
