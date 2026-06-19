"use client";

import { useState, type ReactNode } from "react";

export type Column<T> = {
  key: string;
  label: string;
  sortable?: boolean;
  render: (row: T) => ReactNode;
  style?: React.CSSProperties;
};

export function DataTable<T extends { id: string }>({
  columns,
  rows,
  onRowClick,
  sortKey: externalSortKey,
  onSortChange,
  emptyMessage = "No data",
  loading,
}: {
  columns: Column<T>[];
  rows: T[];
  onRowClick?: (row: T) => void;
  sortKey?: string;
  onSortChange?: (key: string) => void;
  emptyMessage?: string;
  loading?: boolean;
}) {
  const [internalSort, setInternalSort] = useState<{ key: string; dir: "asc" | "desc" } | null>(null);
  const sortKey = externalSortKey ?? internalSort?.key ?? "";
  const sortDir = internalSort?.dir ?? "asc";

  const handleSort = (key: string) => {
    if (onSortChange) {
      onSortChange(key);
      return;
    }
    setInternalSort((prev) => {
      if (prev?.key === key) {
        return { key, dir: prev.dir === "asc" ? "desc" : "asc" };
      }
      return { key, dir: "asc" };
    });
  };

  const sorted = [...rows].sort((a, b) => {
    if (!sortKey) return 0;
    const col = columns.find((c) => c.key === sortKey);
    if (!col) return 0;
    const va = String(col.render(a) ?? "");
    const vb = String(col.render(b) ?? "");
    const cmp = va.localeCompare(vb);
    return sortDir === "asc" ? cmp : -cmp;
  });

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            aria-hidden
            style={{
              height: "2.5rem",
              borderRadius: "var(--radius-sm)",
              background: "linear-gradient(90deg, var(--surface) 25%, var(--surface-elevated) 50%, var(--surface) 75%)",
              backgroundSize: "200% 100%",
              animation: "skeleton-pulse 1.4s ease infinite",
            }}
          />
        ))}
      </div>
    );
  }

  if (sorted.length === 0) {
    return (
      <div
        style={{
          padding: "2rem",
          textAlign: "center",
          color: "var(--muted)",
          border: "1px dashed var(--border)",
          borderRadius: "var(--radius)",
        }}
      >
        {emptyMessage}
      </div>
    );
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: "0.9rem",
        }}
      >
        <thead>
          <tr style={{ borderBottom: "1px solid var(--border)" }}>
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                style={{
                  textAlign: "left",
                  padding: "0.65rem 0.5rem",
                  fontWeight: 600,
                  fontSize: "0.82rem",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  color: "var(--muted)",
                  cursor: col.sortable ? "pointer" : "default",
                  userSelect: "none",
                  whiteSpace: "nowrap",
                  ...col.style,
                }}
                onClick={() => {
                  if (col.sortable) handleSort(col.key);
                }}
                aria-sort={
                  sortKey === col.key ? (sortDir === "asc" ? "ascending" : "descending") : undefined
                }
              >
                {col.sortable ? (
                  <span>
                    {col.label}{" "}
                    <span style={{ opacity: sortKey === col.key ? 1 : 0.3 }}>
                      {sortKey === col.key ? (sortDir === "asc" ? "▲" : "▼") : "▲"}
                    </span>
                  </span>
                ) : (
                  col.label
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr
              key={row.id}
              onClick={() => onRowClick?.(row)}
              style={{
                borderBottom: "1px solid var(--border)",
                cursor: onRowClick ? "pointer" : "default",
                transition: "background 0.1s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "var(--surface)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "none";
              }}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  style={{
                    padding: "0.65rem 0.5rem",
                    verticalAlign: "middle",
                    ...col.style,
                  }}
                >
                  {col.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
