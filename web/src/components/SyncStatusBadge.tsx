export function SyncStatusBadge({
  status,
  error,
  errorCount,
}: {
  status: string;
  error?: string | null;
  errorCount?: number;
}) {
  const s = (status || "idle").toLowerCase();

  if (s === "error") {
    return (
      <span
        title={error ? `${error}${errorCount ? ` (${errorCount} consecutive)` : ""}` : "Sync error"}
        style={{
          display: "inline-flex", alignItems: "center", gap: "0.3rem",
          fontSize: "0.72rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em",
          padding: "0.15rem 0.4rem", borderRadius: "var(--radius-sm)",
          background: "rgb(251 113 133 / 12%)", color: "var(--danger)",
          border: "1px solid rgb(251 113 133 / 30%)", cursor: "default",
        }}
      >
        <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--danger)", display: "inline-block" }} />
        error
        {errorCount ? ` (${errorCount})` : ""}
      </span>
    );
  }

  if (s === "syncing") {
    return (
      <span
        style={{
          display: "inline-flex", alignItems: "center", gap: "0.3rem",
          fontSize: "0.72rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em",
          padding: "0.15rem 0.4rem", borderRadius: "var(--radius-sm)",
          background: "rgb(251 191 36 / 12%)", color: "var(--warning)",
          border: "1px solid rgb(251 191 36 / 30%)",
        }}
      >
        <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--warning)", display: "inline-block" }} />
        syncing
      </span>
    );
  }

  return (
    <span
      style={{
        display: "inline-flex", alignItems: "center", gap: "0.3rem",
        fontSize: "0.72rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em",
        padding: "0.15rem 0.4rem", borderRadius: "var(--radius-sm)",
        background: "rgb(74 222 128 / 12%)", color: "var(--success)",
        border: "1px solid rgb(74 222 128 / 30%)",
      }}
    >
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--success)", display: "inline-block" }} />
      {s === "idle" ? "idle" : "ok"}
    </span>
  );
}
